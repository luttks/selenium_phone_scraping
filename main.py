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

# ==== NEW: Models ====
class PhoneConfigInput(BaseModel):
    brand: Optional[List[str]] = None

class ProductOut(BaseModel):
    image: str
    name: str
    price: str
    link: str
    details: List[str]

class ScrapeResponse(BaseModel):
    total_products: int
    selected_brands: List[str]
    products: List[ProductOut]  # NEW

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    logger.info("Rendering index page")
    filter_list = FilterList()
    brands = filter_list.get_brands()
    return templates.TemplateResponse("index.html", {"request": request, "brands": brands})

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_phones(config: PhoneConfigInput):
    logger.info(f"Received scrape request with brands: {config.brand}")
    driver = None
    try:
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)

        phone_config = PhoneConfiguration(brand=config.brand)
        tgdd = TGDD(driver)
        results = []
        error = tgdd.run(phone_config, results)

        if error:
            logger.error(f"Scraper error: {error}")
            raise HTTPException(status_code=500, detail=error)

        total_products = tgdd.total_product
        logger.info(f"Found {total_products} products")

        # Map tgdd.results -> ProductOut
        products_out: List[ProductOut] = []
        for r in tgdd.results:
            # Giả định model Result có thuộc tính: img, name, price, link, details
            products_out.append(ProductOut(
                image=getattr(r, "img", ""),
                name=getattr(r, "name", ""),
                price=getattr(r, "price", ""),
                link=getattr(r, "link", getattr(r, "product_link", "")),
                details=getattr(r, "details", []) or []
            ))

        return ScrapeResponse(
            total_products=total_products,
            selected_brands=config.brand or [],
            products=products_out
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
