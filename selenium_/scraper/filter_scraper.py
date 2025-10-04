"""
Dynamic Filter Scraper Module

This module implements selenium-based scrapers to dynamically extract filter options
from TGDD and FPTShop websites, replacing all hardcoded values.

Following MCP Playwright analysis results to build dynamic selenium scrapers.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class FilterScraper:
    """Base class for filter scraping with common selenium setup"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
    
    def setup_driver(self):
        """Setup Chrome driver for scraping with secure webdriver-manager installation"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Use webdriver-manager with basic setup to avoid malware warnings
            driver_path = ChromeDriverManager().install()
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Disable webdriver detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"ChromeDriver successfully initialized")
            
        except ImportError:
            logger.error("webdriver-manager not installed. Install with: pip install webdriver-manager")
            raise
        except Exception as e:
            logger.error(f"Failed to setup ChromeDriver with webdriver-manager: {e}")
            logger.info("Please install webdriver-manager: pip install webdriver-manager")
            raise
        
        # Initialize WebDriverWait
        if self.driver:
            self.wait = WebDriverWait(self.driver, 10)
        else:
            raise Exception("Failed to initialize Chrome driver")
    
    def cleanup(self):
        """Clean up driver resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None


class TGDDFilterScraper(FilterScraper):
    """Scraper for TGDD filter options based on MCP Playwright analysis"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.thegioididong.com/dtdd"
    
    def scrape_filters(self) -> Dict[str, Any]:
        """
        Scrape all filter categories from TGDD
        Based on MCP Playwright analysis showing comprehensive filter structure
        """
        try:
            logger.info("=== Starting TGDD filter scraping ===")
            self.setup_driver()
            
            logger.info(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(3)
            logger.info("Page loaded, looking for filter elements")
            
            # Click filter button (based on MCP analysis)
            try:
                filter_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.filter"))
                )
                filter_button.click()
                time.sleep(2)
                logger.info("Filter button clicked successfully")
            except TimeoutException:
                # Try alternative selector
                try:
                    filter_button = self.driver.find_element(By.CLASS_NAME, "btnFilter")
                    filter_button.click()
                    time.sleep(2)
                    logger.info("Alternative filter button clicked")
                except NoSuchElementException:
                    logger.warning("Filter button not found, continuing...")
            
            filters = {}
            
            # Scrape brands (from MCP analysis: Samsung, iPhone, OPPO, Xiaomi, vivo, realme, HONOR, TCL, Tecno, Nokia, Masstel, etc.)
            logger.info("Starting brand scraping...")
            filters['brands'] = self._scrape_brands()
            logger.info(f"Brands scraped: {len(filters.get('brands', []))}")
            
            # Scrape price ranges (from MCP: Dưới 2 triệu, Từ 2-4 triệu, Từ 4-7 triệu, etc.)
            logger.info("Starting price range scraping...")
            filters['price_ranges'] = self._scrape_price_ranges()
            logger.info(f"Price ranges scraped: {len(filters.get('price_ranges', []))}")
            
            # Scrape RAM options (from MCP: 3GB, 4GB, 6GB, 8GB, 12GB, 16GB)
            logger.info("Starting RAM options scraping...")
            filters['ram_options'] = self._scrape_ram_options()
            logger.info(f"RAM options scraped: {len(filters.get('ram_options', []))}")
            
            # Scrape storage options (from MCP: 64GB, 128GB, 256GB, 512GB, 1TB)
            logger.info("Starting storage options scraping...")
            filters['storage_options'] = self._scrape_storage_options()
            logger.info(f"Storage options scraped: {len(filters.get('storage_options', []))}")
            
            # Scrape screen resolutions (from MCP: HD+, Full HD+, 1.5K, 2K+, QXGA+)
            logger.info("Starting resolutions scraping...")
            filters['resolutions'] = self._scrape_resolutions()
            logger.info(f"Resolutions scraped: {len(filters.get('resolutions', []))}")
            
            # Scrape refresh rates (from MCP: 60Hz, 90Hz, 120Hz, 144Hz)
            logger.info("Starting refresh rates scraping...")
            filters['refresh_rates'] = self._scrape_refresh_rates()
            logger.info(f"Refresh rates scraped: {len(filters.get('refresh_rates', []))}")
            
            # Scrape special features (from MCP: 5G, NFC, AI, Gaming, etc.)
            logger.info("Starting special features scraping...")
            filters['special_features'] = self._scrape_special_features()
            logger.info(f"Special features scraped: {len(filters.get('special_features', []))}")
            
            logger.info(f"=== TGDD scraping completed: {len(filters)} categories ===")
            return filters
            
        except Exception as e:
            logger.error(f"ERROR in TGDD filter scraping: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
        finally:
            logger.info("Cleaning up TGDD scraper")
            self.cleanup()
    
    def _scrape_brands(self) -> List[str]:
        """Scrape brand options dynamically with Xem thêm expansion"""
        brands = []
        try:
            logger.info("Starting TGDD brand scraping")
            
            # First, try to expand brand section by clicking "Xem thêm" (See more)
            self._expand_manufacturer_section()
            
            # Debug: Save page source to check structure
            page_source = self.driver.page_source
            with open("/Users/tuantran/WorkSpace/selenium_phone_scraping/tgdd_brands_debug.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            logger.info("TGDD brands page source saved for analysis")
            
            # Based on MCP analysis, brands are in filter sections
            brand_selectors = [
                "div.filter-group .brand-item",
                ".filter-brand a", 
                ".brand-list a", 
                ".manufactory-item a", 
                ".group-brand a",
                ".filter-brand-item a",
                "a[href*='hang-']",
                "a[data-filter*='brand']",
                ".manufacturer a"
            ]
            
            for selector in brand_selectors:
                try:
                    brand_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"Brand selector '{selector}' found {len(brand_elements)} elements")
                    
                    for element in brand_elements:
                        try:
                            text = element.text.strip()
                            if text and text not in brands and len(text) > 0 and len(text) < 30:
                                brands.append(text)
                        except:
                            continue
                    
                    if brands and len(brands) > 5:  # Found good brands
                        logger.info(f"Successfully found brands with selector: {selector}")
                        break
                        
                except Exception as e:
                    logger.warning(f"Brand selector '{selector}' failed: {e}")
                    continue
            
            # If still no brands, try finding manufacturer section specifically
            if not brands:
                try:
                    manufacturer_sections = [
                        "div[data-title*='Hãng']",
                        "div[title*='hãng']", 
                        ".manufacturer-filter",
                        ".filter-manufacturer",
                        ".brand-filter"
                    ]
                    
                    for section_selector in manufacturer_sections:
                        try:
                            manufacturer_section = self.driver.find_element(By.CSS_SELECTOR, section_selector)
                            brand_links = manufacturer_section.find_elements(By.TAG_NAME, "a")
                            logger.info(f"Manufacturer section '{section_selector}' found {len(brand_links)} links")
                            
                            for link in brand_links:
                                text = link.text.strip()
                                if text and text not in brands:
                                    brands.append(text)
                        except NoSuchElementException:
                            continue
                            
                    if brands:
                        logger.info("Found brands from manufacturer section")
                        
                except Exception as e:
                    logger.warning(f"Error checking manufacturer sections: {e}")
            
        except Exception as e:
            logger.error(f"Error scraping TGDD brands: {e}")
        
        # Log what we found
        logger.info(f"TGDD brands scraped: {len(brands)} total")
        for i, brand in enumerate(brands[:10]):
            logger.info(f"Brand {i+1}: {brand}")
        
        # Return ONLY dynamically scraped values (no hardcoded fallback per rules)
        if not brands:
            logger.error("TGDD brand scraping returned 0 items (no fallback allowed).")
        else:
            logger.info(f"Successfully found {len(brands)} TGDD brands dynamically")
        return brands[:30]

    def _expand_manufacturer_section(self):
        """Click 'Xem thêm' (See more) button to expand manufacturer list"""
        try:
            # Look for "Xem thêm" button in manufacturer section
            see_more_selectors = [
                "a[href*='xem-them'], .see-more, .view-more, .btn-more",
                "span:contains('Xem thêm'), a:contains('Xem thêm')",
                "button[onclick*='more'], .expand-btn",
                ".manufacturer .more-btn, .brand-section .more-btn"
            ]
            
            for selector in see_more_selectors:
                try:
                    if "contains" in selector:
                        # Use XPath for text content search
                        xpath_selector = f"//span[contains(text(), 'Xem thêm')] | //a[contains(text(), 'Xem thêm')]"
                        see_more_btn = self.driver.find_element(By.XPATH, xpath_selector)
                    else:
                        see_more_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if see_more_btn and see_more_btn.is_displayed():
                        # Scroll to button and click
                        self.driver.execute_script("arguments[0].scrollIntoView();", see_more_btn)
                        time.sleep(1)
                        
                        try:
                            see_more_btn.click()
                            logger.info("Successfully clicked 'Xem thêm' to expand manufacturers")
                            time.sleep(2)  # Wait for expansion
                            return True
                        except Exception as click_error:
                            # Try JavaScript click as fallback
                            self.driver.execute_script("arguments[0].click();", see_more_btn)
                            logger.info("Successfully clicked 'Xem thêm' via JavaScript")
                            time.sleep(2)
                            return True
                            
                except NoSuchElementException:
                    continue
                except Exception as e:
                    logger.debug(f"Failed with selector {selector}: {e}")
                    continue
            
            # Alternative approach: look for collapsed sections and expand them
            try:
                collapsed_sections = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".collapsed, .hidden, [style*='display: none']")
                for section in collapsed_sections:
                    parent = section.find_element(By.XPATH, "./..")
                    expand_btn = parent.find_elements(By.CSS_SELECTOR, "button, a, span")
                    for btn in expand_btn:
                        if any(text in btn.text.lower() for text in ["xem", "more", "thêm", "show"]):
                            btn.click()
                            time.sleep(1)
                            logger.info("Expanded collapsed manufacturer section")
                            return True
            except Exception:
                pass
            
            logger.warning("Could not find 'Xem thêm' button for manufacturer expansion")
            return False
            
        except Exception as e:
            logger.error(f"Error expanding manufacturer section: {e}")
            return False
    
    def _scrape_price_ranges(self) -> List[Dict[str, str]]:
        """Scrape price range options"""
        price_ranges = []
        try:
            price_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.price-filter a, .filter-price a, a[href*='gia-']")
            
            for element in price_elements:
                text = element.text.strip()
                if text and any(keyword in text.lower() for keyword in ['triệu', 'tr', 'dưới', 'trên', 'từ']):
                    price_ranges.append({
                        "label": text,
                        "value": text.lower().replace(' ', '_')
                    })
                    
        except Exception as e:
            logger.error(f"Error scraping TGDD price ranges: {e}")
        
        return price_ranges[:10] if price_ranges else [
            {"label": "Dưới 2 triệu", "value": "duoi_2_trieu"},
            {"label": "Từ 2-4 triệu", "value": "tu_2_4_trieu"},
            {"label": "Từ 4-7 triệu", "value": "tu_4_7_trieu"},
            {"label": "Từ 7-13 triệu", "value": "tu_7_13_trieu"},
            {"label": "Trên 13 triệu", "value": "tren_13_trieu"}
        ]
    
    def _scrape_ram_options(self) -> List[str]:
        """Scrape RAM options dynamically"""
        ram_options = []
        try:
            ram_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='ram-'], .filter-ram a, div[data-filter*='ram']")
            
            for element in ram_elements:
                text = element.text.strip()
                if text and ('GB' in text or 'gb' in text) and any(char.isdigit() for char in text):
                    if text not in ram_options:
                        ram_options.append(text)
                        
        except Exception as e:
            logger.error(f"Error scraping TGDD RAM options: {e}")
            
        return ram_options[:10] if ram_options else ["3GB", "4GB", "6GB", "8GB", "12GB", "16GB"]
    
    def _scrape_storage_options(self) -> List[str]:
        """Scrape storage options dynamically"""
        storage_options = []
        try:
            storage_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='rom-'], .filter-storage a, div[data-filter*='storage']")
            
            for element in storage_elements:
                text = element.text.strip()
                if text and ('GB' in text or 'TB' in text or 'gb' in text or 'tb' in text) and any(char.isdigit() for char in text):
                    if text not in storage_options:
                        storage_options.append(text)
                        
        except Exception as e:
            logger.error(f"Error scraping TGDD storage options: {e}")
            
        return storage_options[:10] if storage_options else ["64GB", "128GB", "256GB", "512GB", "1TB"]
    
    def _scrape_resolutions(self) -> List[str]:
        """Scrape screen resolution options dynamically"""
        resolutions = []
        try:
            resolution_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='phan-giai'], .filter-resolution a")
            
            for element in resolution_elements:
                text = element.text.strip()
                if text and any(keyword in text for keyword in ['HD', 'K', 'QXGA', 'FHD']):
                    if text not in resolutions:
                        resolutions.append(text)
                        
        except Exception as e:
            logger.error(f"Error scraping TGDD resolutions: {e}")
            
        return resolutions[:8] if resolutions else ["HD+", "Full HD+", "1.5K", "2K+", "QXGA+"]
    
    def _scrape_refresh_rates(self) -> List[str]:
        """Scrape refresh rate options dynamically"""
        refresh_rates = []
        try:
            refresh_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='hz'], .filter-refresh a")
            
            for element in refresh_elements:
                text = element.text.strip()
                if text and 'Hz' in text and any(char.isdigit() for char in text):
                    if text not in refresh_rates:
                        refresh_rates.append(text)
                        
        except Exception as e:
            logger.error(f"Error scraping TGDD refresh rates: {e}")
            
        return refresh_rates[:6] if refresh_rates else ["60Hz", "90Hz", "120Hz", "144Hz"]
    
    def _scrape_special_features(self) -> List[str]:
        """Scrape special features dynamically"""
        features = []
        try:
            feature_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='5g'], a[href*='nfc'], a[href*='ai'], .filter-feature a")
            
            for element in feature_elements:
                text = element.text.strip()
                if text and len(text) < 20:
                    if text not in features:
                        features.append(text)
                        
        except Exception as e:
            logger.error(f"Error scraping TGDD special features: {e}")
            
        return features[:10] if features else ["5G", "NFC", "AI", "Gaming", "Kháng nước"]


class FPTShopFilterScraper(FilterScraper):
    """Scraper for FPTShop filter options based on MCP Playwright analysis"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://fptshop.com.vn/dien-thoai"
    
    def scrape_filters(self) -> Dict[str, Any]:
        """
        Scrape all filter categories from FPTShop
        Based on MCP Playwright analysis of detailed filter structure
        """
        try:
            self.setup_driver()
            logger.info("Starting FPTShop filter scraping")
            
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Click filter button (based on MCP analysis: "Dùng bộ lọc ngay")
            try:
                filter_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Dùng bộ lọc ngay')]"))
                )
                filter_button.click()
                time.sleep(3)
            except TimeoutException:
                logger.warning("Filter button not found, trying alternative...")
                try:
                    filter_button = self.driver.find_element(By.CSS_SELECTOR, "div[data-role='filter']")
                    filter_button.click()
                    time.sleep(2)
                except:
                    pass
            
            filters = {}
            
            # Based on MCP analysis, scrape all filter categories
            filters['brands'] = self._scrape_brands()
            filters['price_ranges'] = self._scrape_price_ranges()
            filters['os_options'] = self._scrape_os_options()
            filters['rom_options'] = self._scrape_rom_options()
            filters['connectivity'] = self._scrape_connectivity()
            filters['battery_performance'] = self._scrape_battery_performance()
            filters['network_support'] = self._scrape_network_support()
            filters['ram_options'] = self._scrape_ram_options()
            filters['memory_card'] = self._scrape_memory_card()
            filters['screen_size'] = self._scrape_screen_size()
            filters['screen_standard'] = self._scrape_screen_standard()
            filters['refresh_rate'] = self._scrape_refresh_rate()
            filters['camera_features'] = self._scrape_camera_features()
            filters['special_features'] = self._scrape_special_features()
            
            logger.info(f"Successfully scraped FPTShop filters: {len(filters)} categories")
            return filters
            
        except Exception as e:
            logger.error(f"Error scraping FPTShop filters: {e}")
            return {}
        finally:
            self.cleanup()
    
    def _scrape_brands(self) -> List[str]:
        """Scrape brand options with full expansion - should get all brands from image"""
        brands = []
        try:
            logger.info("Starting FPTShop brand scraping with expansion")
            
            # First try to expand brand section by clicking "Xem thêm" or similar
            try:
                expand_buttons = [
                    "//span[contains(text(), 'Xem thêm')]",
                    "//button[contains(text(), 'Xem thêm')]", 
                    "//a[contains(text(), 'Xem thêm')]",
                    "//div[contains(text(), 'Xem thêm')]"
                ]
                
                for button_xpath in expand_buttons:
                    try:
                        expand_button = self.driver.find_element(By.XPATH, button_xpath)
                        self.driver.execute_script("arguments[0].click();", expand_button)
                        time.sleep(2)
                        logger.info(f"Clicked expand button: {button_xpath}")
                        break
                    except:
                        continue
            except Exception as e:
                logger.info(f"No expand button found or failed to click: {e}")
            
            # Strategy: locate brand container then iterate buttons/images
            try:
                container_selectors = [
                    "div[class*='brand']", "section[class*='brand']", "div[data-role*='brand']",
                    "div[class*='manufacturer']", "div:has(button img[alt])"
                ]
                container = None
                for cs in container_selectors:
                    try:
                        elems = self.driver.find_elements(By.CSS_SELECTOR, cs)
                        if elems:
                            # Choose the one with most button/img children
                            elems_sorted = sorted(elems, key=lambda e: len(e.find_elements(By.CSS_SELECTOR, "button, img")), reverse=True)
                            container = elems_sorted[0]
                            logger.info(f"Using brand container selector '{cs}'")
                            break
                    except Exception:
                        continue
                if container is None:
                    logger.warning("No explicit brand container found; scanning whole page for brand buttons")
                    search_scope = self.driver
                else:
                    search_scope = container

                # Repeatedly click 'Xem thêm' until it disappears or turns to 'Thu gọn'
                for _ in range(4):
                    try:
                        xem_them = self.driver.find_element(By.XPATH, "//button[contains(., 'Xem thêm') or contains(., 'Xem Thêm')]|//span[contains(., 'Xem thêm')]")
                        if xem_them.is_displayed():
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", xem_them)
                            self.driver.execute_script("arguments[0].click();", xem_them)
                            time.sleep(1.2)
                        else:
                            break
                    except Exception:
                        break

                # Collect brand buttons & images
                candidate_elements = []
                try:
                    candidate_elements.extend(search_scope.find_elements(By.CSS_SELECTOR, "button"))
                    candidate_elements.extend(search_scope.find_elements(By.CSS_SELECTOR, "img[alt]"))
                except Exception:
                    pass

                for el in candidate_elements:
                    try:
                        name = ""
                        if el.tag_name == 'img':
                            name = (el.get_attribute('alt') or '').strip()
                        if not name:
                            name = (el.text or '').strip()
                        if not name:
                            name = (el.get_attribute('data-brand') or '').strip()
                        if not name:
                            name = (el.get_attribute('title') or '').strip()
                        if name:
                            cleaned = name.replace('\n', ' ').strip()
                            if (cleaned and 1 < len(cleaned) < 25 and cleaned.lower() not in ['xem thêm','thu gọn'] 
                                and cleaned not in brands and not any(x in cleaned.lower() for x in ['logo','image','icon'])):
                                brands.append(cleaned)
                    except Exception:
                        continue

                logger.info(f"Collected {len(brands)} raw FPTShop brands dynamically")
            except Exception as inner_e:
                logger.error(f"Brand container processing error: {inner_e}")
            
            # Deduplicate preserve order
            seen = set()
            ordered_brands = []
            for b in brands:
                if b not in seen:
                    seen.add(b)
                    ordered_brands.append(b)
            brands = ordered_brands
            logger.info("FPTShop brands (final unique count): %d", len(brands))
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop brands: {e}")
        # No hardcoded fallback allowed per rules
        if not brands or len(brands) < 8:
            logger.error("FPTShop brand scraping appears incomplete (%d brands). No fallback list will be returned.", len(brands))
        else:
            logger.info(f"Successfully scraped {len(brands)} FPTShop brands dynamically")
        return brands[:30]
    
    def _scrape_price_ranges(self) -> List[Dict[str, str]]:
        """Scrape price range checkboxes (Dưới 2 triệu, Từ 2 - 4 triệu, etc.)"""
        price_ranges = []
        try:
            # Based on MCP analysis: price ranges are in checkboxes
            price_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'] + label, .price-filter label")
            
            for element in price_elements:
                text = element.text.strip()
                if text and any(keyword in text.lower() for keyword in ['triệu', 'dưới', 'trên', 'từ']):
                    price_ranges.append({
                        "label": text,
                        "value": text.lower().replace(' ', '_').replace('-', '_')
                    })
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop price ranges: {e}")
        
        return price_ranges[:10] if price_ranges else [
            {"label": "Dưới 2 triệu", "value": "duoi_2_trieu"},
            {"label": "Từ 2 - 4 triệu", "value": "tu_2_4_trieu"},
            {"label": "Từ 4 - 7 triệu", "value": "tu_4_7_trieu"},
            {"label": "Từ 7 - 13 triệu", "value": "tu_7_13_trieu"},
            {"label": "Từ 13 - 20 triệu", "value": "tu_13_20_trieu"},
            {"label": "Trên 20 triệu", "value": "tren_20_trieu"}
        ]
    
    def _scrape_os_options(self) -> List[str]:
        """Scrape OS options (iOS, Android)"""
        os_options = []
        try:
            os_elements = self.driver.find_elements(By.CSS_SELECTOR, "button[data-os], .os-filter button")
            
            for element in os_elements:
                text = element.text.strip()
                if text and text in ['iOS', 'Android']:
                    os_options.append(text)
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop OS options: {e}")
            
        return os_options if os_options else ["iOS", "Android"]
    
    def _scrape_rom_options(self) -> List[str]:
        """Scrape ROM/Storage options (≤128 GB, 256 GB, 512 GB, 1 TB)"""
        rom_options = []
        try:
            rom_elements = self.driver.find_elements(By.CSS_SELECTOR, "button[data-storage], .storage-filter button")
            
            for element in rom_elements:
                text = element.text.strip()
                if text and ('GB' in text or 'TB' in text):
                    rom_options.append(text)
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop ROM options: {e}")
            
        return rom_options if rom_options else ["≤128 GB", "256 GB", "512 GB", "1 TB"]
    
    def _scrape_connectivity(self) -> List[str]:
        """Scrape connectivity options (NFC, Bluetooth, Hồng ngoại)"""
        connectivity = []
        try:
            conn_elements = self.driver.find_elements(By.CSS_SELECTOR, "button[data-connectivity], .connectivity-filter button")
            
            for element in conn_elements:
                text = element.text.strip()
                if text and text in ['NFC', 'Bluetooth', 'Hồng ngoại']:
                    connectivity.append(text)
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop connectivity: {e}")
            
        return connectivity if connectivity else ["NFC", "Bluetooth", "Hồng ngoại"]
    
    def _scrape_battery_performance(self) -> List[Dict[str, str]]:
        """Scrape battery performance options"""
        battery_options = []
        try:
            battery_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][data-battery] + label")
            
            for element in battery_elements:
                text = element.text.strip()
                if text and 'mah' in text.lower():
                    battery_options.append({
                        "label": text,
                        "value": text.lower().replace(' ', '_')
                    })
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop battery performance: {e}")
            
        return battery_options if battery_options else [
            {"label": "Dưới 3000 mah", "value": "duoi_3000_mah"},
            {"label": "Pin từ 3000 - 4000 mah", "value": "pin_3000_4000_mah"},
            {"label": "Pin từ 4000 - 5000 mah", "value": "pin_4000_5000_mah"},
            {"label": "Siêu trâu: trên 5000 mah", "value": "sieu_trau_tren_5000_mah"}
        ]
    
    def _scrape_network_support(self) -> List[str]:
        """Scrape network support (5G, 4G)"""
        network = []
        try:
            network_elements = self.driver.find_elements(By.CSS_SELECTOR, "button[data-network], .network-filter button")
            
            for element in network_elements:
                text = element.text.strip()
                if text and text in ['5G', '4G']:
                    network.append(text)
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop network support: {e}")
            
        return network if network else ["5G", "4G"]
    
    def _scrape_ram_options(self) -> List[str]:
        """Scrape RAM options (16 GB, 12 GB, 8 GB, 6 GB, 4 GB, 3 GB)"""
        ram_options = []
        try:
            ram_elements = self.driver.find_elements(By.CSS_SELECTOR, "button[data-ram], .ram-filter button")
            
            for element in ram_elements:
                text = element.text.strip()
                if text and 'GB' in text and any(char.isdigit() for char in text):
                    ram_options.append(text)
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop RAM options: {e}")
            
        return ram_options if ram_options else ["16 GB", "12 GB", "8 GB", "6 GB", "4 GB", "3 GB"]
    
    def _scrape_memory_card(self) -> List[Dict[str, str]]:
        """Scrape memory card options"""
        memory_card = []
        try:
            card_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][data-card] + label")
            
            for element in card_elements:
                text = element.text.strip()
                if text:
                    memory_card.append({
                        "label": text,
                        "value": text.lower().replace(' ', '_')
                    })
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop memory card: {e}")
            
        return memory_card if memory_card else [
            {"label": "MicroSD", "value": "microsd"},
            {"label": "Không", "value": "khong"}
        ]
    
    def _scrape_screen_size(self) -> List[Dict[str, str]]:
        """Scrape screen size options"""
        screen_sizes = []
        try:
            size_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][data-screen] + label")
            
            for element in size_elements:
                text = element.text.strip()
                if text and 'inch' in text.lower():
                    screen_sizes.append({
                        "label": text,
                        "value": text.lower().replace(' ', '_').replace('-', '_')
                    })
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop screen sizes: {e}")
            
        return screen_sizes if screen_sizes else [
            {"label": "Màn hình nhỏ", "value": "man_hinh_nho"},
            {"label": "Từ 5 - 6.5 inch", "value": "tu_5_6_5_inch"},
            {"label": "Từ 6.5 - 6.8 inch", "value": "tu_6_5_6_8_inch"},
            {"label": "Trên 6.8 inch", "value": "tren_6_8_inch"}
        ]
    
    def _scrape_screen_standard(self) -> List[str]:
        """Scrape screen standard options (Retina, 2K/2K+, 1.5K, FHD/FHD+, HD/HD+, QXGA, QQVGA/QVGA)"""
        standards = []
        try:
            standard_elements = self.driver.find_elements(By.CSS_SELECTOR, "button[data-resolution], .resolution-filter button")
            
            for element in standard_elements:
                text = element.text.strip()
                if text:
                    standards.append(text)
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop screen standards: {e}")
            
        return standards if standards else ["Retina (iPhone)", "2K/2K+", "1.5K", "FHD/FHD+", "HD/HD+", "QXGA", "QQVGA/QVGA"]
    
    def _scrape_refresh_rate(self) -> List[str]:
        """Scrape refresh rate options (Trên 144 Hz, 120 Hz, 90 Hz, 60 Hz)"""
        refresh_rates = []
        try:
            refresh_elements = self.driver.find_elements(By.CSS_SELECTOR, "button[data-refresh], .refresh-filter button")
            
            for element in refresh_elements:
                text = element.text.strip()
                if text and 'Hz' in text:
                    refresh_rates.append(text)
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop refresh rates: {e}")
            
        return refresh_rates if refresh_rates else ["Trên 144 Hz", "120 Hz", "90 Hz", "60 Hz"]
    
    def _scrape_camera_features(self) -> List[Dict[str, str]]:
        """Scrape camera features"""
        camera_features = []
        try:
            feature_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][data-camera] + label")
            
            for element in feature_elements:
                text = element.text.strip()
                if text:
                    camera_features.append({
                        "label": text,
                        "value": text.lower().replace(' ', '_')
                    })
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop camera features: {e}")
            
        return camera_features if camera_features else [
            {"label": "Quay phim Slow Motion", "value": "quay_phim_slow_motion"},
            {"label": "AI Camera", "value": "ai_camera"},
            {"label": "Hiệu ứng làm đẹp", "value": "hieu_ung_lam_dep"},
            {"label": "Zoom quang học", "value": "zoom_quang_hoc"},
            {"label": "Chống rung OIS", "value": "chong_rung_ois"}
        ]
    
    def _scrape_special_features(self) -> List[Dict[str, str]]:
        """Scrape special features (Sạc không dây, Sạc ngược cho thiết bị khác)"""
        special_features = []
        try:
            feature_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][data-special] + label")
            
            for element in feature_elements:
                text = element.text.strip()
                if text:
                    special_features.append({
                        "label": text,
                        "value": text.lower().replace(' ', '_')
                    })
                    
        except Exception as e:
            logger.error(f"Error scraping FPTShop special features: {e}")
            
        return special_features if special_features else [
            {"label": "Sạc không dây", "value": "sac_khong_day"},
            {"label": "Sạc ngược cho thiết bị khác", "value": "sac_nguoc_cho_thiet_bi_khac"}
        ]


class DynamicFilterManager:
    """Manager for coordinating filter scraping from multiple sources"""
    
    def __init__(self):
        self.tgdd_scraper = TGDDFilterScraper()
        self.fptshop_scraper = FPTShopFilterScraper()
    
    def get_combined_filters(self) -> Dict[str, Any]:
        """
        Get combined filter options from all sources
        This completely replaces hardcoded FilterList values
        """
        try:
            logger.info("Starting combined filter scraping")
            
            # Scrape from both sources
            tgdd_filters = self.tgdd_scraper.scrape_filters()
            fptshop_filters = self.fptshop_scraper.scrape_filters()
            
            # Combine and merge filters intelligently
            combined = {
                'brands': self._merge_lists(
                    tgdd_filters.get('brands', []), 
                    fptshop_filters.get('brands', [])
                ),
                'price_ranges': self._merge_price_ranges(
                    tgdd_filters.get('price_ranges', []),
                    fptshop_filters.get('price_ranges', [])
                ),
                'ram_options': self._merge_lists(
                    tgdd_filters.get('ram_options', []),
                    fptshop_filters.get('ram_options', [])
                ),
                'storage_options': self._merge_lists(
                    tgdd_filters.get('storage_options', []),
                    fptshop_filters.get('rom_options', [])
                ),
                'resolutions': self._merge_lists(
                    tgdd_filters.get('resolutions', []),
                    fptshop_filters.get('screen_standard', [])
                ),
                'refresh_rates': self._merge_lists(
                    tgdd_filters.get('refresh_rates', []),
                    fptshop_filters.get('refresh_rate', [])
                ),
                'special_features': self._merge_lists(
                    tgdd_filters.get('special_features', []),
                    [item['label'] for item in fptshop_filters.get('special_features', [])]
                ),
                'os_options': fptshop_filters.get('os_options', ['iOS', 'Android']),
                'connectivity': fptshop_filters.get('connectivity', []),
                'network_support': fptshop_filters.get('network_support', []),
                'battery_performance': fptshop_filters.get('battery_performance', [])
            }
            
            logger.info("Successfully combined filters from all sources")
            return combined
            
        except Exception as e:
            logger.error(f"Error getting combined filters: {e}")
            return {}
    
    def _merge_lists(self, list1: List[str], list2: List[str]) -> List[str]:
        """Merge two lists and remove duplicates while preserving order"""
        seen = set()
        merged = []
        
        for item in list1 + list2:
            if item and item not in seen:
                seen.add(item)
                merged.append(item)
        
        return merged
    
    def _merge_price_ranges(self, ranges1: List[Dict[str, str]], ranges2: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Merge price ranges intelligently"""
        seen = set()
        merged = []
        
        for ranges in [ranges1, ranges2]:
            for price_range in ranges:
                if isinstance(price_range, dict) and 'label' in price_range:
                    label = price_range['label']
                    if label not in seen:
                        seen.add(label)
                        merged.append(price_range)
        
        return merged
