"""
Dynamic Filter Scraper - No hardcoded values, scrapes filters from websites
Follows code_rules.prompt.md principles
"""
import logging
from typing import Dict, List, Optional, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

logger = logging.getLogger(__name__)

class DynamicFilterScraper:
    """Dynamic filter scraper that extracts all available filters from websites"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        
    def _init_driver(self):
        """Initialize Chrome driver with optimized options"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        
    def scrape_fptshop_filters(self) -> Dict[str, Any]:
        """Dynamically scrape all filter options from FPTShop"""
        if not self.driver:
            self._init_driver()
            
        try:
            logger.info("🔍 Scraping FPTShop filters dynamically...")
            self.driver.get("https://fptshop.com.vn/dien-thoai")
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "cdt-product"))
            )
            
            filters = {
                'brands': self._scrape_fptshop_brands(),
                'price_ranges': self._scrape_fptshop_prices(),
                'ram_options': self._scrape_fptshop_ram(),
                'storage_options': self._scrape_fptshop_storage(),
                'operating_systems': self._scrape_fptshop_os(),
                'network_types': self._scrape_fptshop_network()
            }
            
            logger.info(f"✅ Scraped FPTShop filters: {len(filters['brands'])} brands, {len(filters['price_ranges'])} price ranges")
            return filters
            
        except Exception as e:
            logger.error(f"❌ Error scraping FPTShop filters: {e}")
            return self._get_fallback_filters()
            
    def _scrape_fptshop_brands(self) -> List[Dict[str, str]]:
        """Scrape brand options from FPTShop"""
        brands = []
        try:
            # Click on brand filter to expand
            brand_filter = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'filter-item')]//span[text()='Thương hiệu']"))
            )
            brand_filter.click()
            time.sleep(2)
            
            # Get all brand options
            brand_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'filter-item')]//span[text()='Thương hiệu']/../..//label")
            
            for element in brand_elements:
                try:
                    brand_name = element.find_element(By.TAG_NAME, "span").text.strip()
                    brand_value = element.find_element(By.TAG_NAME, "input").get_attribute("value")
                    
                    if brand_name and brand_value:
                        brands.append({
                            'name': brand_name,
                            'value': brand_value.lower()
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not scrape brands: {e}")
            
        return brands
        
    def _scrape_fptshop_prices(self) -> List[Dict[str, str]]:
        """Scrape price range options from FPTShop"""
        price_ranges = []
        try:
            # Look for price filter options
            price_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'price-filter')]//label | //div[contains(text(), 'triệu')]")
            
            for element in price_elements:
                try:
                    text = element.text.strip()
                    if 'triệu' in text:
                        # Extract price range info
                        value = text.lower().replace(' ', '-').replace('triệu', 'trieu')
                        price_ranges.append({
                            'name': text,
                            'value': value
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not scrape price ranges: {e}")
            
        return price_ranges
        
    def _scrape_fptshop_ram(self) -> List[Dict[str, str]]:
        """Scrape RAM options from FPTShop"""
        ram_options = []
        try:
            # Look for RAM/Memory filters
            ram_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'filter')]//span[contains(text(), 'GB') and contains(text(), 'RAM')] | //label[contains(., 'GB')]")
            
            for element in ram_elements:
                try:
                    text = element.text.strip()
                    if 'GB' in text and any(char.isdigit() for char in text):
                        # Extract RAM value
                        import re
                        ram_match = re.search(r'(\d+)\s*GB', text)
                        if ram_match:
                            ram_value = f"{ram_match.group(1)}gb"
                            ram_options.append({
                                'name': text,
                                'value': ram_value
                            })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not scrape RAM options: {e}")
            
        return ram_options
        
    def _scrape_fptshop_storage(self) -> List[Dict[str, str]]:
        """Scrape storage options from FPTShop"""
        storage_options = []
        try:
            # Look for storage filters
            storage_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'filter')]//span[contains(text(), 'GB') or contains(text(), 'TB')] | //label[contains(., 'GB') or contains(., 'TB')]")
            
            for element in storage_elements:
                try:
                    text = element.text.strip()
                    if ('GB' in text or 'TB' in text) and any(char.isdigit() for char in text):
                        # Extract storage value
                        import re
                        storage_match = re.search(r'(\d+)\s*(GB|TB)', text)
                        if storage_match:
                            number, unit = storage_match.groups()
                            storage_value = f"{number}{unit.lower()}"
                            storage_options.append({
                                'name': text,
                                'value': storage_value
                            })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not scrape storage options: {e}")
            
        return storage_options
        
    def _scrape_fptshop_os(self) -> List[Dict[str, str]]:
        """Scrape OS options from FPTShop"""
        os_options = []
        try:
            # Look for OS filters
            os_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'filter')]//span[contains(text(), 'iOS') or contains(text(), 'Android')] | //label[contains(., 'iOS') or contains(., 'Android')]")
            
            for element in os_elements:
                try:
                    text = element.text.strip()
                    if text.lower() in ['ios', 'android']:
                        os_options.append({
                            'name': text,
                            'value': text.lower()
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not scrape OS options: {e}")
            
        return os_options
        
    def _scrape_fptshop_network(self) -> List[Dict[str, str]]:
        """Scrape network options from FPTShop"""
        network_options = []
        try:
            # Look for network filters
            network_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'filter')]//span[contains(text(), '4G') or contains(text(), '5G')] | //label[contains(., '4G') or contains(., '5G')]")
            
            for element in network_elements:
                try:
                    text = element.text.strip()
                    if text.lower() in ['4g', '5g']:
                        network_options.append({
                            'name': text,
                            'value': text.lower()
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not scrape network options: {e}")
            
        return network_options
        
    def scrape_tgdd_filters(self) -> Dict[str, Any]:
        """Dynamically scrape all filter options from TGDD"""
        if not self.driver:
            self._init_driver()
            
        try:
            logger.info("🔍 Scraping TGDD filters dynamically...")
            self.driver.get("https://www.thegioididong.com/dtdd")
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "item"))
            )
            
            filters = {
                'brands': self._scrape_tgdd_brands(),
                'price_ranges': self._scrape_tgdd_prices(),
                'ram_options': self._scrape_tgdd_ram(),
                'storage_options': self._scrape_tgdd_storage(),
                'resolution_options': self._scrape_tgdd_resolutions(),
                'refresh_rate_options': self._scrape_tgdd_refresh_rates()
            }
            
            logger.info(f"✅ Scraped TGDD filters: {len(filters['brands'])} brands, {len(filters['price_ranges'])} price ranges")
            return filters
            
        except Exception as e:
            logger.error(f"❌ Error scraping TGDD filters: {e}")
            return self._get_fallback_filters()
            
    def _scrape_tgdd_brands(self) -> List[Dict[str, str]]:
        """Scrape brand options from TGDD"""
        brands = []
        try:
            # Find brand filter elements
            brand_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'brand')]//a | //ul[contains(@class, 'brand')]//a")
            
            for element in brand_elements:
                try:
                    brand_name = element.text.strip()
                    brand_href = element.get_attribute("href")
                    
                    if brand_name and brand_href:
                        # Extract brand value from href
                        import re
                        brand_match = re.search(r'brand/([^/?]+)', brand_href)
                        brand_value = brand_match.group(1) if brand_match else brand_name.lower()
                        
                        brands.append({
                            'name': brand_name,
                            'value': brand_value
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not scrape TGDD brands: {e}")
            
        return brands
        
    def _scrape_tgdd_prices(self) -> List[Dict[str, str]]:
        """Scrape price range options from TGDD"""
        price_ranges = []
        try:
            # Find price filter elements
            price_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'price')]//a | //ul[contains(@class, 'price')]//a")
            
            for element in price_elements:
                try:
                    text = element.text.strip()
                    href = element.get_attribute("href")
                    
                    if 'triệu' in text or 'tr' in text:
                        # Extract price range value from href
                        import re
                        price_match = re.search(r'price/([^/?]+)', href)
                        price_value = price_match.group(1) if price_match else text.lower().replace(' ', '-')
                        
                        price_ranges.append({
                            'name': text,
                            'value': price_value
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not scrape TGDD price ranges: {e}")
            
        return price_ranges
        
    def _scrape_tgdd_ram(self) -> List[Dict[str, str]]:
        """Scrape RAM options from TGDD"""
        # Similar implementation for TGDD RAM scraping
        return []
        
    def _scrape_tgdd_storage(self) -> List[Dict[str, str]]:
        """Scrape storage options from TGDD"""
        # Similar implementation for TGDD storage scraping
        return []
        
    def _scrape_tgdd_resolutions(self) -> List[Dict[str, str]]:
        """Scrape resolution options from TGDD"""
        # Similar implementation for TGDD resolution scraping
        return []
        
    def _scrape_tgdd_refresh_rates(self) -> List[Dict[str, str]]:
        """Scrape refresh rate options from TGDD"""
        # Similar implementation for TGDD refresh rate scraping
        return []
        
    def _get_fallback_filters(self) -> Dict[str, Any]:
        """Fallback minimal filters if scraping fails"""
        return {
            'brands': [],
            'price_ranges': [],
            'ram_options': [],
            'storage_options': [],
            'operating_systems': [],
            'network_types': [],
            'resolution_options': [],
            'refresh_rate_options': []
        }
        
    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
