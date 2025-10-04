"""
Adaptive filter applier that dynamically finds and applies filters
based on current page structure rather than hardcoded selectors
"""

import logging
import time
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..model.phone_configuration import PhoneConfiguration

logger = logging.getLogger(__name__)


class AdaptiveFilterApplier:
    """Dynamically applies filters based on current page structure"""
    
    def __init__(self, driver: WebDriver, source: str):
        self.driver = driver
        self.source = source.lower()
        
    def apply_filters_adaptively(self, config: PhoneConfiguration) -> bool:
        """Apply filters using adaptive strategies"""
        try:
            success_count = 0
            
            # Apply brand filters
            if config.brands:
                if self._apply_brand_filters_adaptive(config.brands):
                    success_count += 1
            
            # Apply price filters
            if config.price_ranges:
                if self._apply_price_filters_adaptive(config.price_ranges):
                    success_count += 1
                    
            # Apply RAM filters  
            if config.ram:
                if self._apply_ram_filters_adaptive(config.ram):
                    success_count += 1
                    
            # Apply storage filters
            if config.storage:
                if self._apply_storage_filters_adaptive(config.storage):
                    success_count += 1
                    
            # Source-specific filters
            if self.source == 'tgdd':
                if config.resolutions and self._apply_resolution_filters_adaptive(config.resolutions):
                    success_count += 1
                if config.refresh_rates and self._apply_refresh_rate_filters_adaptive(config.refresh_rates):
                    success_count += 1
            elif self.source == 'fptshop':
                if config.os and self._apply_os_filters_adaptive(config.os):
                    success_count += 1
                if config.network and self._apply_network_filters_adaptive(config.network):
                    success_count += 1
                if config.battery and self._apply_battery_filters_adaptive(config.battery):
                    success_count += 1
            
            logger.info(f"Applied {success_count} filter categories successfully")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error in adaptive filter application: {e}")
            return False
            
    def _apply_brand_filters_adaptive(self, brands: List[str]) -> bool:
        """Apply brand filters using multiple detection strategies"""
        try:
            applied_count = 0
            
            for brand in brands:
                # Strategy 1: Look for buttons/links with brand images
                brand_elements = self._find_brand_elements_with_images(brand)
                
                # Strategy 2: Look for text-based brand elements
                if not brand_elements:
                    brand_elements = self._find_brand_elements_with_text(brand)
                    
                # Strategy 3: Look for brand in any clickable element
                if not brand_elements:
                    brand_elements = self._find_brand_elements_generic(brand)
                
                # Try to click the brand element
                for element in brand_elements[:1]:  # Take first match
                    if self._safe_click(element, f"brand filter: {brand}"):
                        applied_count += 1
                        break
                        
            logger.info(f"Applied {applied_count}/{len(brands)} brand filters")
            return applied_count > 0
            
        except Exception as e:
            logger.error(f"Error applying brand filters: {e}")
            return False
    
    def _find_brand_elements_with_images(self, brand: str) -> List[WebElement]:
        """Find brand elements that contain images with brand name"""
        selectors = [
            f"//img[contains(@alt, '{brand}')]/parent::*",
            f"//img[contains(@src, '{brand.lower()}')]/parent::*", 
            f"//img[contains(@title, '{brand}')]/parent::*",
            f"//button//img[contains(@alt, '{brand}')]/ancestor::button",
            f"//a//img[contains(@alt, '{brand}')]/ancestor::a"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend(found)
            except:
                continue
                
        return elements
    
    def _find_brand_elements_with_text(self, brand: str) -> List[WebElement]:
        """Find brand elements with text content"""
        selectors = [
            f"//button[contains(text(), '{brand}')]",
            f"//a[contains(text(), '{brand}')]",
            f"//label[contains(text(), '{brand}')]",
            f"//span[contains(text(), '{brand}')]",
            f"//*[@class and contains(text(), '{brand}')]"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend(found)
            except:
                continue
                
        return elements
    
    def _find_brand_elements_generic(self, brand: str) -> List[WebElement]:
        """Generic search for brand elements"""
        try:
            # Search all clickable elements containing brand name
            elements = self.driver.find_elements(By.XPATH, 
                f"//*[self::button or self::a or self::input or self::label][contains(text(), '{brand}') or contains(@*, '{brand}')]")
            return elements
        except:
            return []
    
    def _apply_price_filters_adaptive(self, price_ranges: List[str]) -> bool:
        """Apply price filters adaptively"""
        try:
            applied_count = 0
            
            for price_range in price_ranges:
                # Extract price keywords from range
                price_keywords = self._extract_price_keywords(price_range)
                
                # Find price filter elements
                price_elements = self._find_price_elements(price_keywords)
                
                # Try to apply filter
                for element in price_elements[:1]:
                    if self._safe_click(element, f"price filter: {price_range}"):
                        applied_count += 1
                        break
                        
            logger.info(f"Applied {applied_count}/{len(price_ranges)} price filters")
            return applied_count > 0
            
        except Exception as e:
            logger.error(f"Error applying price filters: {e}")
            return False
    
    def _extract_price_keywords(self, price_range: str) -> List[str]:
        """Extract meaningful price keywords from range string"""
        keywords = []
        
        # Common price range patterns
        if 'duoi' in price_range.lower() or 'under' in price_range.lower():
            keywords.extend(['dưới', 'under'])
        if 'tren' in price_range.lower() or 'over' in price_range.lower():
            keywords.extend(['trên', 'over'])
        if 'trieu' in price_range.lower():
            keywords.append('triệu')
        if 'million' in price_range.lower():
            keywords.append('million')
            
        # Extract number ranges
        import re
        numbers = re.findall(r'\d+', price_range)
        keywords.extend(numbers)
        
        return keywords
    
    def _find_price_elements(self, keywords: List[str]) -> List[WebElement]:
        """Find price filter elements"""
        elements = []
        
        # Look for elements containing price-related text
        for keyword in keywords:
            selectors = [
                f"//input[@type='checkbox']/following-sibling::*[contains(text(), '{keyword}')]",
                f"//label[contains(text(), '{keyword}')]",
                f"//button[contains(text(), '{keyword}')]",
                f"//*[contains(text(), '{keyword}') and contains(text(), 'triệu')]"
            ]
            
            for selector in selectors:
                try:
                    found = self.driver.find_elements(By.XPATH, selector)
                    elements.extend(found)
                except:
                    continue
                    
        return elements
    
    def _apply_ram_filters_adaptive(self, ram_options: List[str]) -> bool:
        """Apply RAM filters adaptively"""
        return self._apply_spec_filters_adaptive(ram_options, 'ram', ['gb', 'ram'])
    
    def _apply_storage_filters_adaptive(self, storage_options: List[str]) -> bool:
        """Apply storage filters adaptively"""
        return self._apply_spec_filters_adaptive(storage_options, 'storage', ['gb', 'storage', 'bộ nhớ'])
    
    def _apply_spec_filters_adaptive(self, options: List[str], filter_type: str, keywords: List[str]) -> bool:
        """Generic method for applying spec filters (RAM, storage, etc.)"""
        try:
            applied_count = 0
            
            for option in options:
                # Extract numeric value
                import re
                numbers = re.findall(r'\d+', option)
                
                # Find spec filter elements
                spec_elements = []
                for keyword in keywords:
                    for number in numbers:
                        selectors = [
                            f"//*[contains(text(), '{number}') and contains(text(), '{keyword}')]",
                            f"//label[contains(text(), '{number}') and contains(text(), '{keyword}')]",
                            f"//button[contains(text(), '{number}') and contains(text(), '{keyword}')]"
                        ]
                        
                        for selector in selectors:
                            try:
                                found = self.driver.find_elements(By.XPATH, selector)
                                spec_elements.extend(found)
                            except:
                                continue
                
                # Try to apply filter
                for element in spec_elements[:1]:
                    if self._safe_click(element, f"{filter_type} filter: {option}"):
                        applied_count += 1
                        break
                        
            logger.info(f"Applied {applied_count}/{len(options)} {filter_type} filters")
            return applied_count > 0
            
        except Exception as e:
            logger.error(f"Error applying {filter_type} filters: {e}")
            return False
    
    def _apply_resolution_filters_adaptive(self, resolutions: List[str]) -> bool:
        """Apply resolution filters for TGDD"""
        return self._apply_spec_filters_adaptive(resolutions, 'resolution', ['x', 'resolution', 'độ phân giải'])
    
    def _apply_refresh_rate_filters_adaptive(self, rates: List[str]) -> bool:
        """Apply refresh rate filters for TGDD"""
        return self._apply_spec_filters_adaptive(rates, 'refresh rate', ['hz', 'tần số'])
    
    def _apply_os_filters_adaptive(self, os_options: List[str]) -> bool:
        """Apply OS filters for FPTShop"""
        return self._apply_spec_filters_adaptive(os_options, 'os', ['android', 'ios', 'hệ điều hành'])
    
    def _apply_network_filters_adaptive(self, network_options: List[str]) -> bool:
        """Apply network filters for FPTShop"""
        return self._apply_spec_filters_adaptive(network_options, 'network', ['4g', '5g', 'wifi', 'mạng'])
    
    def _apply_battery_filters_adaptive(self, battery_options: List[str]) -> bool:
        """Apply battery filters for FPTShop"""
        return self._apply_spec_filters_adaptive(battery_options, 'battery', ['mah', 'pin'])
    
    def _safe_click(self, element: WebElement, description: str) -> bool:
        """Safely click an element with error handling"""
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # Try regular click first
            if element.is_enabled() and element.is_displayed():
                element.click()
                logger.info(f"Successfully applied {description}")
                time.sleep(1)  # Wait for filter to apply
                return True
            else:
                # Try JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
                logger.info(f"Successfully applied {description} (JS click)")
                time.sleep(1)
                return True
                
        except Exception as e:
            logger.warning(f"Failed to apply {description}: {e}")
            return False
