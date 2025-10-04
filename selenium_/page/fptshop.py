"""
FPTShop phone scraper - Clean version
Fixed to target search results area instead of advertisement carousel
"""
import time
import re
import logging
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

from ..model.phone_configuration import PhoneConfiguration
from ..model.result import Phone

logger = logging.getLogger(__name__)
from ..model.result import Phone

logger = logging.getLogger(__name__)

class FPTShopScraper:
    """FPTShop scraper with URL-based filtering and proper pagination"""
    
    BASE_URL = "https://fptshop.com.vn/dien-thoai"
    
    def __init__(self):
        self.driver = None
        self.wait = None
    
    def setup_driver(self):
        """Setup Chrome driver"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def cleanup(self):
        """Clean up driver resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def scrape_phones(self, config: PhoneConfiguration) -> List[Phone]:
        """Main scraping method"""
        try:
            self.setup_driver()
            logger.info("Starting FPTShop phone scraping with URL-based filters")
            
            # Build filtered URL
            filtered_url = self._build_filtered_url(config)
            logger.info(f"Loading FPTShop with filters: {filtered_url}")
            
            self.driver.get(filtered_url)
            time.sleep(5)
            
            # Get page info
            logger.info(f"Current URL: {self.driver.current_url}")
            logger.info(f"Page title: {self.driver.title}")
            
            # Get target brands for filtering
            target_brands = []
            if config.brands and config.brands[0].strip().lower() != "all":
                target_brands = [brand.strip().lower() for brand in config.brands]
                logger.info(f"Target brands for filtering: {target_brands}")
            
            # Load all products with pagination
            logger.info("Loading all products with pagination...")
            self._load_all_products()
            
            # Extract phones from MAIN search results area, avoid carousel
            phones = self._extract_phones_from_search_area(target_brands)
            
            logger.info(f"Successfully scraped {len(phones)} phones from FPTShop")
            return phones
            
        except Exception as e:
            logger.error(f"Error scraping FPTShop phones: {e}")
            return []
        finally:
            self.cleanup()
    
    def get_available_brands(self) -> List[str]:
        """Scrape available brands from FPTShop dynamically"""
        try:
            self.setup_driver()
            logger.info("Scraping available brands from FPTShop")
            
            self.driver.get(self.BASE_URL)
            time.sleep(3)
            
            brands = []
            
            # Get the full brand list from the carousel area - most reliable method
            try:
                logger.info("Looking for brand carousel links...")
                # Target the main brand carousel
                brand_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/dien-thoai/') and not(contains(@href, '?')) and not(@href='/dien-thoai')]")
                logger.info(f"Found {len(brand_links)} brand carousel links")
                
                seen_brands = set()
                for link in brand_links:
                    try:
                        href = link.get_attribute('href')
                        if href and '/dien-thoai/' in href:
                            # Extract brand name from URL like /dien-thoai/samsung -> samsung
                            parts = href.split('/dien-thoai/')
                            if len(parts) > 1:
                                brand_part = parts[1].split('/')[0].split('?')[0]  # Remove any params
                                
                                # Filter out category pages and specific models
                                exclude_terms = {
                                    'dien-thoai-5g', 'ai', '5g', 'gap', 'gaming', 'pho-thong', 
                                    'dien-thoai-gap', 'dien-thoai-gaming', 'dien-thoai-ai'
                                }
                                
                                if brand_part and len(brand_part) > 2 and brand_part not in exclude_terms:
                                    # Handle special cases
                                    if brand_part == 'apple-iphone':
                                        if 'apple' not in seen_brands:
                                            brands.append('apple')
                                            seen_brands.add('apple')
                                    elif '-' not in brand_part or brand_part.startswith(('samsung-galaxy', 'iphone-')):
                                        # These are specific models, extract brand
                                        if brand_part.startswith('samsung-galaxy'):
                                            if 'samsung' not in seen_brands:
                                                brands.append('samsung')
                                                seen_brands.add('samsung')
                                        elif brand_part.startswith('iphone-'):
                                            if 'apple' not in seen_brands:
                                                brands.append('apple') 
                                                seen_brands.add('apple')
                                    else:
                                        # Regular brand name
                                        clean_brand = brand_part.lower()
                                        if clean_brand not in seen_brands and len(clean_brand) > 2:
                                            brands.append(clean_brand)
                                            seen_brands.add(clean_brand)
                                            
                    except Exception as e:
                        logger.debug(f"Error processing brand link: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error extracting brand carousel: {e}")
            
            # Remove duplicates and filter 
            brands = list(dict.fromkeys(brands))  # Preserve order while removing duplicates
            
            # Filter out invalid entries and specific models
            valid_brands = []
            processed_brands = set()
            
            for brand in brands:
                # Check if it's a valid brand name (not a model or category)
                if brand and len(brand) > 2:
                    # Extract base brand from complex names
                    base_brand = brand.lower()
                    
                    # Handle specific cases first
                    if any(term in base_brand for term in ['iphone-', 'apple-iphone']):
                        base_brand = 'apple'
                    elif any(term in base_brand for term in ['samsung-galaxy', 'galaxy-']):
                        base_brand = 'samsung'  
                    elif any(term in base_brand for term in ['xiaomi-redmi', 'xiaomi-poco', 'redmi-', 'poco-']):
                        base_brand = 'xiaomi'
                    elif any(term in base_brand for term in ['oppo-reno', 'oppo-a']):
                        base_brand = 'oppo'
                    elif any(term in base_brand for term in ['honor-magic', 'honor-x']):
                        base_brand = 'honor'
                    elif any(term in base_brand for term in ['tecno-spark', 'tecno-pova']):
                        base_brand = 'tecno'
                    elif any(term in base_brand for term in ['realme-', 'realme-c', 'realme-gt']):
                        base_brand = 'realme'
                    elif any(term in base_brand for term in ['vivo-', 'vivo-v', 'vivo-y']):
                        base_brand = 'vivo'
                    elif any(term in base_brand for term in ['redmagic-']):
                        base_brand = 'redmagic'
                    elif any(term in base_brand for term in ['nubia-']):
                        base_brand = 'nubia'
                    elif any(term in base_brand for term in ['tcl-']):
                        base_brand = 'tcl'
                    
                    # Skip specific model numbers and series names
                    skip_patterns = [
                        '-series', '-pro-', '-max', '-fold', '-flip', '-ultra',
                        'galaxy-s-series', 'galaxy-a-series', 'galaxy-z-series',
                        'iphone-14-series', 'iphone-15-series', 'iphone-16-series'
                    ]
                    
                    # Skip if it contains model-specific patterns but isn't a base brand
                    if any(pattern in base_brand for pattern in skip_patterns):
                        # Only keep if it's exactly these series names
                        if base_brand not in {'galaxy-s-series', 'galaxy-a-series', 'galaxy-z-series'}:
                            continue
                        else:
                            base_brand = 'samsung'  # Convert series to base brand
                    
                    # Skip if contains model numbers or specific product codes
                    if (any(char.isdigit() for char in base_brand) and 
                        not base_brand in {'redmagic', 'tecno', 'honor', 'vivo'} and
                        not any(base_brand.startswith(prefix) for prefix in ['tcl', 'honor', 'redmagic'])):
                        # Check if it's a model number pattern like "a5i-6gb", "14t-pro"
                        parts = base_brand.split('-')
                        if len(parts) > 1:
                            first_part = parts[0]
                            # If first part is a known brand, use that
                            known_brands = {'samsung', 'apple', 'xiaomi', 'oppo', 'honor', 'tecno', 'realme', 'vivo', 'nokia', 'zte', 'redmagic', 'nubia', 'tcl', 'itel', 'mobell', 'viettel', 'masstel', 'benco', 'inoi'}
                            if first_part in known_brands:
                                base_brand = first_part
                            else:
                                continue  # Skip model numbers
                        else:
                            continue  # Skip single-word model numbers
                    
                    # Only add if we haven't seen this brand yet
                    if base_brand not in processed_brands and base_brand and len(base_brand) > 1:
                        valid_brands.append(base_brand)
                        processed_brands.add(base_brand)
            
            brands = valid_brands
            
            logger.info(f"Found {len(brands)} available brands: {brands}")
            
            # Return only what we actually found from the website
            return brands
            
        except Exception as e:
            logger.error(f"Error getting available brands: {e}")
            # Return empty list if scraping fails - no hardcode fallback
            return []
        finally:
            self.cleanup()

    def get_available_price_ranges(self) -> List[dict]:
        """Scrape available price ranges from FPTShop dynamically"""
        try:
            self.setup_driver()
            logger.info("Scraping available price ranges from FPTShop")
            
            self.driver.get(self.BASE_URL)
            time.sleep(3)
            
            price_ranges = []
            
            # Look for price filter elements
            try:
                # Click on filter area to expand
                filter_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'filter') or contains(text(), 'Bộ lọc')]")
                if filter_buttons:
                    filter_buttons[0].click()
                    time.sleep(2)
                
                # Look for price range options
                price_selectors = [
                    "//label[contains(text(), 'triệu')]",
                    "//span[contains(text(), 'triệu')]",
                    "//div[contains(@class, 'price')]//label",
                    "//input[@type='checkbox']/following-sibling::*[contains(text(), 'triệu')]"
                ]
                
                for selector in price_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            text = element.text.strip()
                            if 'triệu' in text and text not in [p['label'] for p in price_ranges]:
                                price_ranges.append({
                                    'label': text,
                                    'value': text.lower().replace(' ', '_').replace('triệu', 'trieu')
                                })
                        except:
                            continue
                            
            except Exception as e:
                logger.error(f"Error extracting price ranges: {e}")
            
            logger.info(f"Found {len(price_ranges)} price ranges: {[p['label'] for p in price_ranges]}")
            return price_ranges
            
        except Exception as e:
            logger.error(f"Error getting price ranges: {e}")
            return []
        finally:
            self.cleanup()

    def get_available_ram_options(self) -> List[str]:
        """Scrape available RAM options from FPTShop dynamically"""
        try:
            self.setup_driver()
            logger.info("Scraping available RAM options from FPTShop")
            
            self.driver.get(self.BASE_URL)
            time.sleep(3)
            
            ram_options = []
            
            try:
                # Look for RAM filter elements
                ram_selectors = [
                    "//label[contains(text(), 'GB') and (contains(text(), 'RAM') or contains(., 'RAM'))]",
                    "//span[contains(text(), 'GB') and contains(text(), 'RAM')]",
                    "//div[contains(@class, 'ram')]//label",
                    "//*[contains(text(), 'GB') and contains(text(), 'RAM')]"
                ]
                
                for selector in ram_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            text = element.text.strip()
                            if 'GB' in text and any(char.isdigit() for char in text):
                                # Extract RAM value like "8 GB"
                                import re
                                ram_match = re.search(r'(\d+)\s*GB', text)
                                if ram_match and f"{ram_match.group(1)} GB" not in ram_options:
                                    ram_options.append(f"{ram_match.group(1)} GB")
                        except:
                            continue
                            
            except Exception as e:
                logger.error(f"Error extracting RAM options: {e}")
            
            logger.info(f"Found {len(ram_options)} RAM options: {ram_options}")
            return ram_options
            
        except Exception as e:
            logger.error(f"Error getting RAM options: {e}")
            return []
        finally:
            self.cleanup()

    def get_available_storage_options(self) -> List[str]:
        """Scrape available storage options from FPTShop dynamically"""
        try:
            self.setup_driver()
            logger.info("Scraping available storage options from FPTShop")
            
            self.driver.get(self.BASE_URL)
            time.sleep(3)
            
            storage_options = []
            
            try:
                # Look for storage filter elements
                storage_selectors = [
                    "//label[contains(text(), 'GB') or contains(text(), 'TB')]",
                    "//span[contains(text(), 'GB') or contains(text(), 'TB')]",
                    "//div[contains(@class, 'storage')]//label",
                    "//*[contains(text(), 'GB') or contains(text(), 'TB')]"
                ]
                
                for selector in storage_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            text = element.text.strip()
                            if ('GB' in text or 'TB' in text) and any(char.isdigit() for char in text):
                                # Extract storage value like "256 GB" or "1 TB"
                                import re
                                storage_match = re.search(r'(\d+)\s*(GB|TB)', text)
                                if storage_match:
                                    value = f"{storage_match.group(1)} {storage_match.group(2)}"
                                    if value not in storage_options:
                                        storage_options.append(value)
                        except:
                            continue
                            
            except Exception as e:
                logger.error(f"Error extracting storage options: {e}")
            
            logger.info(f"Found {len(storage_options)} storage options: {storage_options}")
            return storage_options
            
        except Exception as e:
            logger.error(f"Error getting storage options: {e}")
            return []
        finally:
            self.cleanup()

    def get_available_os_options(self) -> List[str]:
        """Scrape available OS options from FPTShop dynamically"""
        try:
            self.setup_driver()
            logger.info("Scraping available OS options from FPTShop")
            
            self.driver.get(self.BASE_URL)
            time.sleep(3)
            
            os_options = []
            
            try:
                # Look for OS filter elements
                os_selectors = [
                    "//label[contains(text(), 'iOS') or contains(text(), 'Android')]",
                    "//span[contains(text(), 'iOS') or contains(text(), 'Android')]",
                    "//*[contains(text(), 'iOS') or contains(text(), 'Android')]"
                ]
                
                for selector in os_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            text = element.text.strip()
                            if 'iOS' in text and 'iOS' not in os_options:
                                os_options.append('iOS')
                            elif 'Android' in text and 'Android' not in os_options:
                                os_options.append('Android')
                        except:
                            continue
                            
            except Exception as e:
                logger.error(f"Error extracting OS options: {e}")
            
            logger.info(f"Found {len(os_options)} OS options: {os_options}")
            return os_options
            
        except Exception as e:
            logger.error(f"Error getting OS options: {e}")
            return []
        finally:
            self.cleanup()

    def get_available_network_options(self) -> List[str]:
        """Scrape available network options from FPTShop dynamically"""
        try:
            self.setup_driver()
            logger.info("Scraping available network options from FPTShop")
            
            self.driver.get(self.BASE_URL)
            time.sleep(3)
            
            network_options = []
            
            try:
                # Look for network filter elements
                network_selectors = [
                    "//label[contains(text(), '4G') or contains(text(), '5G')]",
                    "//span[contains(text(), '4G') or contains(text(), '5G')]",
                    "//*[contains(text(), '4G') or contains(text(), '5G')]"
                ]
                
                for selector in network_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            text = element.text.strip()
                            if '5G' in text and '5G' not in network_options:
                                network_options.append('5G')
                            elif '4G' in text and '4G' not in network_options:
                                network_options.append('4G')
                        except:
                            continue
                            
            except Exception as e:
                logger.error(f"Error extracting network options: {e}")
            
            logger.info(f"Found {len(network_options)} network options: {network_options}")
            return network_options
            
        except Exception as e:
            logger.error(f"Error getting network options: {e}")
            return []
        finally:
            self.cleanup()

    def get_all_filter_options(self) -> dict:
        """Get all available filter options from FPTShop"""
        logger.info("Getting all FPTShop filter options...")
        
        return {
            'brands': self.get_available_brands(),
            'price_ranges': self.get_available_price_ranges(),
            'ram_options': self.get_available_ram_options(),
            'storage_options': self.get_available_storage_options(),
            'os_options': self.get_available_os_options(),
            'network_options': self.get_available_network_options()
        }

    def _build_filtered_url(self, config: PhoneConfiguration) -> str:
        """Build URL with filters applied"""
        url = self.BASE_URL
        params = []
        
        # Brand filter mapping (URL parameter to brand name)
        brand_mapping = {
            'samsung': 'samsung',
            'apple': 'apple',
            'iphone': 'apple',  # Alternative
            'xiaomi': 'xiaomi', 
            'oppo': 'oppo',
            'honor': 'honor',
            'tecno': 'tecno',
            'realme': 'realme',
            'vivo': 'vivo',
            'nokia': 'nokia',
            'zte': 'zte',
            'redmagic': 'redmagic',
            'inoi': 'inoi',
            'viettel': 'viettel',
            'masstel': 'masstel',
            'benco': 'benco',
            'tcl': 'tcl',
            'itel': 'itel',
            'mobell': 'mobell'
        }
        
        # Add brand filters
        if config.brands and config.brands[0].strip().lower() != "all":
            for brand in config.brands:
                brand_clean = brand.strip().lower()
                
                # Map brand to URL parameter
                if brand_clean in brand_mapping:
                    mapped_brand = brand_mapping[brand_clean]
                    params.append(f"hang-san-xuat={mapped_brand}")
                    logger.info(f"DEBUG: added {brand_clean} filter: hang-san-xuat={mapped_brand}")
                else:
                    # Fallback - use brand as is
                    params.append(f"hang-san-xuat={brand_clean}")
                    logger.info(f"DEBUG: added fallback {brand_clean} filter: hang-san-xuat={brand_clean}")
        
        # Add price filters
        if hasattr(config, 'min_price') and config.min_price:
            params.append(f"price_min={config.min_price}")
        if hasattr(config, 'max_price') and config.max_price:
            params.append(f"price_max={config.max_price}")
        
        # Add sorting
        params.append("sort=noi-bat")  # Sort by featured/popular
        
        if params:
            url += "?" + "&".join(params)
        
        return url

    def _load_all_products(self, max_attempts: int = 5):
        """Load all products using pagination - target search results area only"""
        attempts = 0
        
        while attempts < max_attempts:
            try:
                logger.info(f"Attempting pagination (attempt {attempts + 1})...")
                
                # Multiple strategies to find the pagination button based on MCP analysis
                button_selectors = [
                    # Exact text match with whitespace handling from MCP findings
                    "//button[normalize-space(text())='Xem thêm 8 kết quả']",
                    "//button[contains(normalize-space(text()), 'Xem thêm 8 kết quả')]",
                    "//button[contains(text(), 'Xem thêm 8 kết quả')]",
                    # More flexible number matching
                    "//button[contains(text(), 'Xem thêm') and contains(text(), 'kết quả')]",
                    # Below Samsung filter results area
                    "//button[contains(@class, 'cursor-pointer') and contains(text(), 'Xem thêm')]",
                    # General fallback
                    "//button[contains(text(), 'Xem thêm')]"
                ]
                
                load_more_btn = None
                for selector in button_selectors:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                        logger.info(f"Selector '{selector}' found {len(buttons)} buttons")
                        
                        for btn in buttons:
                            if btn.is_displayed() and "xem thêm" in btn.text.lower():
                                # Check button position - must be in main content area
                                btn_location = btn.location
                                logger.info(f"Found button at y={btn_location['y']}, text: '{btn.text}'")
                                
                                # Skip buttons in carousel/banner area (too high on page)
                                if btn_location['y'] > 1200:  # Below carousel/banner
                                    load_more_btn = btn
                                    logger.info(f"Selected pagination button: '{btn.text}' at y={btn_location['y']}")
                                    break
                                else:
                                    logger.info(f"Skipping button too high on page (likely carousel): y={btn_location['y']}")
                        
                        if load_more_btn:
                            break
                    except Exception as e:
                        logger.warning(f"Error with selector '{selector}': {e}")
                        continue
                
                if not load_more_btn:
                    logger.info("No more pagination button found")
                    break
                
                # Count products before click - ONLY from main content area
                products_before = len(self._get_search_area_products())
                logger.info(f"Products in search area before click: {products_before}")
                
                # Click pagination button
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_btn)
                time.sleep(2)
                self.driver.execute_script("arguments[0].click();", load_more_btn)
                logger.info("Pagination button clicked, waiting for new products...")
                
                # Wait for new products to load
                max_wait = 10
                wait_time = 0
                products_after = products_before
                
                while wait_time < max_wait and products_after <= products_before:
                    time.sleep(2)
                    wait_time += 2
                    products_after = len(self._get_search_area_products())
                    logger.info(f"Waiting... {wait_time}s (search area products: {products_after})")
                
                if products_after > products_before:
                    logger.info(f"New products loaded in search area! {products_before} → {products_after}")
                    attempts += 1
                else:
                    logger.info("No new products loaded in search area, pagination complete")
                    break
                    
            except Exception as e:
                logger.info(f"Pagination completed: {e}")
                break
                
        logger.info(f"Pagination completed after {attempts} attempts")

    def _get_search_area_products(self):
        """Get products ONLY from Samsung search results area, not carousel"""
        search_selectors = [
            # Target the Samsung search results section specifically
            "//div[contains(text(), 'Tìm thấy') and contains(text(), 'kết quả')]/following-sibling::div//a[contains(@href, '/dien-thoai/')]",
            # Samsung results container 
            "//button[text()='Samsung']/../..//div[contains(@class, 'generic')]//a[contains(@href, '/dien-thoai/')]",
            # Main Samsung products section
            "//div[contains(@class, 'generic') and .//strong[text()='24']]//a[contains(@href, '/dien-thoai/')]",
            # Fallback: all product links in main content, filtered by position
            "//main//a[contains(@href, '/dien-thoai/')]"
        ]
        
        for selector in search_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    logger.info(f"Found {len(elements)} products using selector: {selector}")
                    
                    # Filter by position to exclude carousel/banner items
                    filtered_elements = []
                    for elem in elements:
                        try:
                            elem_location = elem.location
                            # Only include elements in main content area (y > 1000)
                            if elem_location['y'] > 1000:
                                filtered_elements.append(elem)
                        except:
                            pass
                    
                    logger.info(f"After position filtering: {len(filtered_elements)} products")
                    if filtered_elements:
                        return filtered_elements
            except Exception as e:
                logger.warning(f"Error with selector '{selector}': {e}")
                continue
        
        return []

    def _extract_phones_from_search_area(self, target_brands: List[str]) -> List[Phone]:
        """Extract phones from the main search results area (avoiding carousel ads)"""
        try:
            # Target the main product grid (avoiding carousels)
            product_selectors = [
                "//main//a[contains(@href, '/dien-thoai/')]",  # Main area product links
            ]
            
            all_products = []
            for selector in product_selectors:
                products = self.driver.find_elements(By.XPATH, selector)
                logger.info(f"Found {len(products)} products using selector: {selector}")
                all_products.extend(products)
            
            if not all_products:
                logger.warning("No products found in search area")
                return []
            
            # Filter by position to avoid carousel items
            # Usually carousel items are at the top, main results are below
            filtered_products = []
            for i, product in enumerate(all_products):
                try:
                    location = product.location
                    # Skip items in top carousel area (typically y < 800)
                    if location['y'] > 600:  # Adjust threshold as needed
                        filtered_products.append(product)
                except:
                    filtered_products.append(product)  # Include if can't get location
                    
            logger.info(f"After position filtering: {len(filtered_products)} products")
            
            # Process filtered products
            phones = []
            logger.info(f"Processing {len(filtered_products)} products from search area")
            
            for product in filtered_products:
                try:
                    # Get product name from link or nearby text
                    name = ""
                    url = ""
                    price = "N/A"
                    
                    # Get URL
                    url = product.get_attribute('href')
                    if not url:
                        continue
                    
                    # Get name from multiple sources
                    name_sources = [
                        product.get_attribute('title'),
                        product.text,
                        product.find_element(By.XPATH, ".//img").get_attribute('alt') if product.find_elements(By.XPATH, ".//img") else None
                    ]
                    
                    for source in name_sources:
                        if source and source.strip():
                            name = source.strip()
                            break
                    
                    # If no name found, try to extract from URL
                    if not name and url:
                        name = url.split('/')[-1].replace('-', ' ').title()
                    
                    if not name:
                        continue
                    
                    # Get price from parent or nearby elements
                    try:
                        parent = product.find_element(By.XPATH, "./ancestor::div[contains(@class, '') or contains(@data-', '')]")
                        price_elements = parent.find_elements(By.XPATH, ".//span[contains(text(), '₫')] | .//p[contains(text(), '₫')] | .//div[contains(text(), '₫')]")
                        
                        for price_elem in price_elements:
                            price_text = price_elem.text.strip()
                            if '₫' in price_text:
                                # Get the actual price (usually the last one or one without strikethrough)
                                if not any(x in price_elem.get_attribute('class') or '' for x in ['old', 'strike', 'through']):
                                    price = price_text
                                    break
                        
                        if price == "N/A" and price_elements:
                            # Fallback to any price found
                            price = price_elements[-1].text.strip()
                            
                    except Exception as e:
                        logger.debug(f"Error getting price for {name}: {e}")
                    
                    # Brand filtering with improved Apple/iPhone detection
                    if target_brands:
                        product_brand = self._extract_brand_from_name(name)
                        should_include = False
                        
                        for target_brand in target_brands:
                            if target_brand.lower() == 'apple':
                                # For Apple, check for iPhone, iPad, etc.
                                if any(keyword in name.lower() for keyword in ['iphone', 'ipad', 'apple']):
                                    should_include = True
                                    break
                            else:
                                # For other brands, check if brand name is in product name
                                if target_brand.lower() in name.lower() or target_brand.lower() in product_brand.lower():
                                    should_include = True
                                    break
                        
                        if not should_include:
                            logger.debug(f"FILTERED OUT (not {target_brands}): {name}")
                            continue
                    
                    phones.append(Phone(
                        name=name,
                        price=price,
                        url=url
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error processing product element: {e}")
                    continue
            
            # Debug info
            brand_counts = {}
            sample_names = []
            for phone in phones:
                brand = self._extract_brand_from_name(phone.name)
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
                if len(sample_names) < 5:
                    sample_names.append(phone.name)
            
            logger.info(f"DEBUG: Found {len(brand_counts)} different brands, {len(phones)} total products")
            logger.info(f"DEBUG: Brand counts: {brand_counts}")
            logger.info(f"DEBUG: Sample products: {sample_names}")
            
            logger.info(f"Final filtered results for {target_brands}: {len(phones)} products")
            return phones
            
        except Exception as e:
            logger.error(f"Error extracting phones from search area: {e}")
            return []

    def _detect_brand_from_name(self, phone_name: str) -> str:
        """Detect brand from phone name"""
        name_lower = phone_name.lower()
        
        brand_keywords = {
            'samsung': ['samsung', 'galaxy'],
            'apple': ['iphone', 'apple'],
            'xiaomi': ['xiaomi', 'redmi', 'poco', 'mi '],
            'oppo': ['oppo', 'oneplus'],
            'honor': ['honor'],
            'tecno': ['tecno'],
            'realme': ['realme'],
            'vivo': ['vivo'],
            'nokia': ['nokia'],
            'huawei': ['huawei'],
            'nubia': ['nubia'],
            'tcl': ['tcl']
        }
        
        for brand, keywords in brand_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return brand
                
        return 'other'

    def _extract_phone_info(self, element) -> Optional[Phone]:
        """Extract phone information from product element"""
        try:
            name = ""
            price = "N/A"
            url = ""
            
            # Extract name and URL
            try:
                if element.tag_name == 'a':
                    url = element.get_attribute('href')
                    name = element.get_attribute('title') or element.text.strip()
                else:
                    link_elem = element.find_element(By.CSS_SELECTOR, "a[href*='/dien-thoai/']")
                    url = link_elem.get_attribute('href') or ""
                    name = link_elem.get_attribute('title') or link_elem.text.strip()
            except:
                pass
            
            # Extract name with multiple strategies
            if not name:
                name_selectors = ["h3", ".product-name", "[class*='title']", "[class*='name']"]
                for selector in name_selectors:
                    try:
                        name_elem = element.find_element(By.CSS_SELECTOR, selector)
                        name_text = name_elem.text.strip()
                        if name_text and len(name_text) > 3:
                            name = name_text
                            break
                    except:
                        continue
            
            # Improved price extraction
            try:
                price_found = False
                
                # Strategy 1: Look for price elements with Vietnamese dong symbol
                price_elements = element.find_elements(By.XPATH, ".//*[contains(text(), '₫') or contains(text(), 'đ') or contains(text(), 'VND')]")
                
                for price_elem in price_elements:
                    price_text = price_elem.text.strip()
                    
                    # Skip promotional text
                    if any(skip_word in price_text.lower() for skip_word in ['giảm', 'tiết kiệm', 'cũ', 'từ', 'đến', 'tối', 'lên', 'giá cũ']):
                        continue
                    
                    # Extract price with Vietnamese dong
                    price_patterns = [
                        r'(\d{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{3})*)\s*₫',
                        r'(\d{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{3})*)\s*đ',
                        r'(\d{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{3})*)\s*VND'
                    ]
                    
                    for pattern in price_patterns:
                        matches = re.findall(pattern, price_text)
                        if matches:
                            # Take the first valid price
                            raw_price = matches[0]
                            # Format the price nicely
                            if ',' in raw_price:
                                price = raw_price + " ₫"
                            else:
                                # Add proper formatting for Vietnamese prices
                                price_num = raw_price.replace('.', '')
                                if len(price_num) >= 6:  # Million range
                                    formatted = f"{price_num[:-6]}.{price_num[-6:-3]}.{price_num[-3:]} ₫"
                                    price = formatted
                                else:
                                    price = raw_price + " ₫"
                            price_found = True
                            break
                    
                    if price_found:
                        break
                
                # Strategy 2: Look in parent elements if not found
                if not price_found:
                    try:
                        parent_text = element.text
                        price_matches = re.findall(r'(\d{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{3})*)\s*₫', parent_text)
                        if price_matches:
                            price = price_matches[0] + " ₫"
                            price_found = True
                    except:
                        pass
                
                # Strategy 3: CSS selector approach
                if not price_found:
                    try:
                        css_price_selectors = [
                            '[class*="price"]',
                            '[class*="cost"]', 
                            '[data-price]',
                            'span:contains("₫")',
                            'p:contains("₫")'
                        ]
                        
                        for css_selector in css_price_selectors:
                            try:
                                price_elems = element.find_elements(By.CSS_SELECTOR, css_selector)
                                for elem in price_elems:
                                    elem_text = elem.text.strip()
                                    if '₫' in elem_text:
                                        price_matches = re.findall(r'(\d{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{3})*)\s*₫', elem_text)
                                        if price_matches:
                                            price = price_matches[0] + " ₫"
                                            price_found = True
                                            break
                                if price_found:
                                    break
                            except:
                                continue
                    except:
                        pass
                        
            except Exception as e:
                logger.debug(f"Price extraction error: {e}")
            
            # Only return if we have meaningful data
            if name or url:
                return Phone(
                    name=name if name else "Unknown Phone",
                    price=price,
                    ram="N/A",
                    storage="N/A", 
                    screen="N/A",
                    camera="N/A",
                    battery="N/A",
                    os="",
                    url=url
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error extracting phone info: {e}")
            return None
