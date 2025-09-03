import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from selenium_.page.tgdd import TGDD
from selenium_.model.phone_configuration import PhoneConfiguration
from selenium_.model.filter_list import FilterList
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome, ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Phone Scraper API")
templates = Jinja2Templates(directory="templates")

# ==== Models ====
class PhoneConfigInput(BaseModel):
    brand: Optional[List[str]] = None
    price_range: Optional[str] = None
    ram: Optional[List[str]] = None
    storage: Optional[List[str]] = None
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
    brands = filter_list.get_brands()
    price_ranges = filter_list.get_price_ranges()
    ram_options = filter_list.get_ram_options()
    storage_options = filter_list.get_storage_options()
    resolution_options = filter_list.get_resolution_options()
    refresh_rate_options = filter_list.get_refresh_rate_options()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "brands": brands,
            "price_ranges": price_ranges,
            "ram_options": ram_options,
            "storage_options": storage_options,
            "resolution_options": resolution_options,
            "refresh_rate_options": refresh_rate_options
        }
    )

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_phones(config: PhoneConfigInput):
    logger.info(f"Received scrape request with config: {config}")
    driver = None
    try:
        options = ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)

        phone_config = PhoneConfiguration(
            brand=config.brand,
            price_range=config.price_range,
            ram=config.ram,
            storage=config.storage,
            resolutions=config.resolutions,
            refresh_rates=config.refresh_rates
        )
        tgdd = TGDD(driver)
        results = []
        error = tgdd.run(phone_config, results)

        if error:
            logger.error(f"Scraper error: {error}")
            raise HTTPException(status_code=500, detail=error)

        total_products = tgdd.total_product
        logger.info(f"Found {total_products} products")

        products_out: List[ProductOut] = []
        for r in tgdd.results:
            products_out.append(ProductOut(
                image_link=getattr(r, "image_link", "N/A"),
                name=getattr(r, "name", ""),
                price=getattr(r, "price", "Không có thông tin"),
                product_link=getattr(r, "product_link", "N/A"),
                details=getattr(r, "details", []) or []
            ))

        return ScrapeResponse(
            total_products=total_products,
            selected_brands=config.brand or [],
            selected_price_range=config.price_range,
            selected_ram=config.ram or [],
            selected_storage=config.storage or [],
            selected_resolutions=config.resolutions or [],
            selected_refresh_rates=config.refresh_rates or [],
            products=products_out
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        logger.info("Scrape completed, leaving WebDriver open for inspection")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)