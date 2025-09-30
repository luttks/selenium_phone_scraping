import logging
import json
import uuid
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from selenium_.page.tgdd import TGDD
from selenium_.page.fpt import FPTShop   # <-- Đã được tạo riêng
from selenium_.model.phone_configuration import PhoneConfiguration
from selenium_.model.filter_list import FilterList
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome, ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import uvicorn
import redis
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Phone Scraper API")
templates = Jinja2Templates(directory="templates")

# Redis connection (auto-connect)
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        decode_responses=True
    )
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis connected successfully!")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}. Results will not be cached.")
    redis_client = None


# ==== Models ====
class PhoneConfigInput(BaseModel):
    brand: Optional[List[str]] = None
    price_range: Optional[str] = None
    ram: Optional[List[str]] = None  # [value, operator]
    storage: Optional[List[str]] = None  # [value, operator]
    resolutions: Optional[List[str]] = None
    refresh_rates: Optional[List[str]] = None


class ProductOut(BaseModel):
    image_link: str
    name: str
    price: str
    product_link: str
    details: List[str]


class ScrapeResponse(BaseModel):
    total_products: int
    selected_brands: List[str]
    selected_price_range: Optional[str]
    selected_ram: List[str]
    selected_storage: List[str]
    selected_resolutions: List[str]
    selected_refresh_rates: List[str]
    products: List[ProductOut]


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    logger.info("Rendering index page")
    filter_list = FilterList()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "brands": filter_list.get_brands(),
            "price_ranges": filter_list.get_price_ranges(),
            "ram_options": filter_list.get_ram_options(),
            "storage_options": filter_list.get_storage_options(),
            "resolution_options": filter_list.get_resolution_options(),
            "refresh_rate_options": filter_list.get_refresh_rate_options(),
        }
    )


def parse_ram_or_storage(value_list: Optional[List[str]]) -> Optional[tuple]:
    if not value_list or len(value_list) != 2:
        return None
    value, operator = value_list[0], value_list[1]
    if operator not in [">=", "<=", "="]:
        operator = "="
    return (value, operator)


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_phones(config: PhoneConfigInput):
    logger.info(f"Received scrape request with config: {config}")

    # Chuẩn hóa cấu hình
    phone_config = PhoneConfiguration(
        brand=config.brand or [],
        price_range=config.price_range,
        ram=parse_ram_or_storage(config.ram),
        storage=parse_ram_or_storage(config.storage),
        resolutions=config.resolutions or [],
        refresh_rates=config.refresh_rates or [],
    )

    driver_tgdd = None
    driver_fpt = None
    try:
        def build_options():
            opts = ChromeOptions()
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--start-maximized")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option('useAutomationExtension', False)
            # Block site permission prompts (notifications, geolocation, media) and run headless
            opts.add_argument("--disable-notifications")
            opts.add_argument("--no-first-run")
            opts.add_argument("--disable-popup-blocking")
            opts.add_argument("--use-fake-ui-for-media-stream")
            opts.add_argument("--window-size=1280,720")
            # Headless mode for both TGDD and FPT
            opts.add_argument("--headless=new")
            # Chrome content settings to block prompts
            opts.add_experimental_option(
                "prefs",
                {
                    "profile.default_content_setting_values.notifications": 2,
                    "profile.default_content_setting_values.geolocation": 2,
                    "profile.default_content_setting_values.media_stream_mic": 2,
                    "profile.default_content_setting_values.media_stream_camera": 2,
                },
            )
            return opts

        # Create two independent drivers for parallel scraping
        driver_tgdd = Chrome(service=Service(ChromeDriverManager().install()), options=build_options())
        driver_fpt = Chrome(service=Service(ChromeDriverManager().install()), options=build_options())

        all_results = []

        # Run TGDD and FPT in parallel
        logger.info("Scraping TGDD and FPT in parallel...")
        tgdd_error = None
        fpt_error = None

        def run_tgdd():
            nonlocal tgdd_error
            try:
                scraper = TGDD(driver_tgdd)
                tgdd_error = scraper.run(phone_config, all_results)
            except Exception as e:
                tgdd_error = str(e)

        def run_fpt():
            nonlocal fpt_error
            try:
                scraper = FPTShop(driver_fpt)
                fpt_error = scraper.run(phone_config, all_results)
            except Exception as e:
                fpt_error = str(e)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(run_tgdd), executor.submit(run_fpt)]
            for f in futures:
                f.result()

        if tgdd_error:
            logger.warning(f"TGDD scrape error (non-fatal): {tgdd_error}")
        if fpt_error:
            logger.warning(f"FPT scrape error (non-fatal): {fpt_error}")

        # === Loại bỏ trùng lặp ===
        seen = set()
        unique_results = []
        for r in all_results:
            key = (r.name.strip().lower(), r.price.strip())
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        # === Chuẩn bị response ===
        products_out = [
            ProductOut(
                image_link=r.image_link or "N/A",
                name=r.name or "",
                price=r.price or "Không có thông tin",
                product_link=r.product_link or "N/A",
                details=r.details or []
            )
            for r in unique_results
        ]

        # Create response
        response_data = ScrapeResponse(
            total_products=len(products_out),
            selected_brands=config.brand or [],
            selected_price_range=config.price_range,
            selected_ram=config.ram or [],
            selected_storage=config.storage or [],
            selected_resolutions=config.resolutions or [],
            selected_refresh_rates=config.refresh_rates or [],
            products=products_out
        )
        
        # Save to Redis with 1 minute expiration
        if redis_client:
            try:
                result_id = str(uuid.uuid4())
                redis_key = f"scrape_result:{result_id}"
                redis_client.setex(
                    redis_key, 
                    60,  # 1 minute expiration
                    json.dumps(response_data.dict())
                )
                logger.info(f"Result saved to Redis with ID: {result_id}")
                
                # Add result_id to response
                response_dict = response_data.dict()
                response_dict['result_id'] = result_id
                return response_dict
            except Exception as e:
                logger.warning(f"Failed to save to Redis: {e}")
        
        return response_data

    except Exception as e:
        logger.error(f"Unexpected error during scraping: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Ensure both drivers are closed
        for drv, name in ((driver_tgdd, "TGDD"), (driver_fpt, "FPT")):
            if drv:
                try:
                    drv.quit()
                    logger.info(f"{name} WebDriver closed successfully.")
                except Exception as e:
                    logger.warning(f"Error closing {name} WebDriver: {e}")


@app.get("/home/{result_id}", response_class=HTMLResponse)
async def get_result_page(request: Request, result_id: str):
    """Get scrape result by ID and display in HTML format"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    try:
        # Get data from Redis
        redis_key = f"scrape_result:{result_id}"
        cached_data = redis_client.get(redis_key)
        
        if not cached_data:
            raise HTTPException(status_code=404, detail="Result not found or expired")
        
        # Parse cached data
        result_data = json.loads(cached_data)
        
        # Separate products by source
        tgdd_products = [p for p in result_data['products'] 
                        if p.get('product_link') and 'thegioididong.com' in p['product_link']]
        fpt_products = [p for p in result_data['products'] 
                       if p.get('product_link') and 'fptshop.com' in p['product_link']]
        
        # Render template with data
        return templates.TemplateResponse(
            "result.html", 
            {
                "request": request,
                "total_products": result_data['total_products'],
                "tgdd_products": tgdd_products,
                "fpt_products": fpt_products,
                "all_products": result_data['products'],
                "result_id": result_id,
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid cached data format")
    except Exception as e:
        logger.error(f"Error retrieving result: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/{result_id}")
async def get_result_api(result_id: str):
    """Return cached scrape result by ID in JSON format"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service unavailable")

    try:
        redis_key = f"scrape_result:{result_id}"
        cached_data = redis_client.get(redis_key)

        if not cached_data:
            raise HTTPException(status_code=404, detail="Result not found or expired")

        result_data = json.loads(cached_data)
        return result_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid cached data format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving result JSON: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/{result_id}", response_class=HTMLResponse)
async def get_index_with_id(request: Request, result_id: str):
    """Serve the main index UI even when path contains a result_id."""
    logger.info("Rendering index page with result_id path")
    filter_list = FilterList()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "brands": filter_list.get_brands(),
            "price_ranges": filter_list.get_price_ranges(),
            "ram_options": filter_list.get_ram_options(),
            "storage_options": filter_list.get_storage_options(),
            "resolution_options": filter_list.get_resolution_options(),
            "refresh_rate_options": filter_list.get_refresh_rate_options(),
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)