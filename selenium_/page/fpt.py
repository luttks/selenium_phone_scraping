from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
import time
from selenium_.model.filter_list import FilterList
from selenium_.model.phone_configuration import PhoneConfiguration
from selenium_.model.result import Result


class FPTShop:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)
        self.base_url = "https://fptshop.com.vn"
        self.url = self.base_url + "/dien-thoai"
        self.results = []
        self.filter_list = FilterList()

    def run(self, phone: PhoneConfiguration, all_results: List[Result]):
        print("[FPT] Starting run...")
        try:
            self.driver.get(self.url)
            print("[FPT] Đang đợi trang load...")
            time.sleep(2)  # Đợi filter load xong
            # Scroll nhẹ để kích hoạt lazy-load/render động
            try:
                self.driver.execute_script("window.scrollTo(0, 600);")
                time.sleep(0.5)
                self.driver.execute_script("window.scrollTo(0, 0);")
            except Exception:
                pass
            
            # Đợi cho các filter elements load
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".accordion-0 .Selection_button__vX7ZX")
                ))
                print("[FPT] Filter elements đã load xong")
            except:
                print("[FPT] Cảnh báo: Không thể đợi filter elements load")

            # Áp dụng filter theo đúng selector đã kiểm chứng
            self.filter_brand(phone.get_brand())
            self.filter_price(phone.get_price_range())
            self.filter_ram(phone.get_ram())
            self.filter_storage(phone.get_storage())
            self.filter_resolutions(phone.get_resolutions())
            self.filter_refresh_rates(phone.get_refresh_rates())

            time.sleep(3)  # Đợi kết quả cập nhật lâu hơn
            all_results.extend(self.get_results())
            print(f"[FPT] Đã thu thập {len(self.results)} sản phẩm")

        except Exception as e:
            print(f"[FPT] LỖI: {e}")
            import traceback
            traceback.print_exc()

    def _click_button_by_text(self, buttons: List, target: str) -> bool:
        """Click nút có text chính xác bằng target (case-sensitive)."""
        for btn in buttons:
            try:
                if btn.text.strip() == target:
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.5)
                    return True
            except:
                continue
        print(f"[FPT] Không tìm thấy nút: '{target}'")
        return False

    # =============== FILTER FUNCTIONS ===============
    def filter_brand(self, brands: List[str]):
        if not brands:
            return
        
        print(f"[FPT] Filtering brands: {brands}")
        # Mapping từ TGDD → FPT
        fpt_brands = [self.filter_list.BRAND_TGDD_TO_FPT.get(b, b) for b in brands]
        print(f"[FPT] Mapped FPT brands: {fpt_brands}")
        
        # Sử dụng selector đã được verify từ debug
        brand_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".accordion-0 .Selection_button__vX7ZX")
        print(f"[FPT] Found {len(brand_buttons)} brand buttons")
        
        for b in fpt_brands:
            found = False
            for btn in brand_buttons:
                try:
                    # Thử lấy text từ img alt
                    img_elements = btn.find_elements(By.TAG_NAME, "img")
                    if img_elements:
                        brand_text = img_elements[0].get_attribute("alt").strip()
                        print(f"[FPT] Checking brand button: '{brand_text}' vs '{b}'")
                        
                        if self._fpt_brand_matches(b, brand_text):
                            self.driver.execute_script("arguments[0].click();", btn)
                            time.sleep(0.5)
                            print(f"[FPT] Đã chọn hãng: {brand_text}")
                            found = True
                            break
                    else:
                        # Fallback: lấy text từ button
                        button_text = btn.text.strip()
                        if button_text and self._fpt_brand_matches(b, button_text):
                            self.driver.execute_script("arguments[0].click();", btn)
                            time.sleep(0.5)
                            print(f"[FPT] Đã chọn hãng (text): {button_text}")
                            found = True
                            break
                except Exception as ex:
                    print(f"[FPT] Error processing brand button: {ex}")
                    continue
                    
            if not found:
                print(f"[FPT] Không tìm thấy hãng: {b}")

    def _fpt_brand_matches(self, target_brand: str, element_brand: str) -> bool:
        """So sánh brand name cho FPT"""
        target = target_brand.lower().strip()
        element = element_brand.lower().strip()
        
        # Exact match hoặc contains
        return target == element or target in element or element in target

    def filter_price(self, price_href: Optional[str]):
        if not price_href:
            return
            
        print(f"[FPT] Filtering price: {price_href}")
        # Lấy tên hiển thị từ FilterList
        price_name = ""
        for p in self.filter_list.price_ranges:
            if p["data-href"] == price_href:
                price_name = p["name"]
                break
        if not price_name:
            print(f"[FPT] Không tìm thấy price name cho href: {price_href}")
            return
            
        print(f"[FPT] Looking for price: {price_name}")
        
        # Sử dụng selector chính xác theo thông tin bạn cung cấp
        price_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, ".priceFilterWrapper input[type='checkbox']")
        print(f"[FPT] Found {len(price_checkboxes)} price checkboxes")
        
        for checkbox in price_checkboxes:
            try:
                # Tìm label tương ứng với checkbox
                checkbox_id = checkbox.get_attribute("id")
                if checkbox_id:
                    label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{checkbox_id}']")
                    label_text = label.text.strip()
                    print(f"[FPT] Checking price option: '{label_text}' vs '{price_name}'")
                    
                    if label_text == price_name:
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        print(f"[FPT] Đã chọn khoảng giá: {price_name}")
                        time.sleep(0.5)
                        break
            except Exception as ex:
                print(f"[FPT] Error processing price checkbox: {ex}")
                continue

    def filter_ram(self, ram: Optional[tuple]):
        if not ram:
            return
        value, op = ram
        print(f"[FPT] Filtering RAM: {value} {op}")
        valid_rams = self.filter_list.get_filtered_memory(value, op, self.filter_list.ram_options)
        print(f"[FPT] Valid RAM options: {valid_rams}")
        
        # Selector chính xác theo thông tin bạn cung cấp: nhóm thứ 5
        ram_buttons = self.driver.find_elements(By.XPATH, "(//div[@class='flex flex-wrap gap-2'])[5]//button")
        print(f"[FPT] Found {len(ram_buttons)} RAM buttons")
        
        for r in valid_rams:
            if self._click_button_by_text(ram_buttons, r):
                print(f"[FPT] Đã chọn RAM: {r}")

    def filter_storage(self, storage: Optional[tuple]):
        if not storage:
            return
        value, op = storage
        print(f"[FPT] Filtering Storage: {value} {op}")
        valid_storages = self.filter_list.get_filtered_memory(value, op, self.filter_list.storage_options)
        # Map sang định dạng FPT
        fpt_storages = {self.filter_list.STORAGE_TGDD_TO_FPT.get(s, s) for s in valid_storages}
        print(f"[FPT] Valid FPT storage options: {fpt_storages}")
        
        # Selector chính xác theo thông tin bạn cung cấp: nhóm thứ 2
        storage_buttons = self.driver.find_elements(By.XPATH, "(//div[@class='flex flex-wrap gap-2'])[2]//button")
        print(f"[FPT] Found {len(storage_buttons)} storage buttons")
        
        for s in fpt_storages:
            if self._click_button_by_text(storage_buttons, s):
                print(f"[FPT] Đã chọn Storage: {s}")

    def filter_resolutions(self, resolutions: List[str]):
        if not resolutions:
            return
        print(f"[FPT] Filtering Resolutions: {resolutions}")
        fpt_resolutions = [self.filter_list.RESOLUTION_TGDD_TO_FPT.get(r, r) for r in resolutions]
        print(f"[FPT] FPT resolution options: {fpt_resolutions}")
        
        # Selector chính xác theo thông tin bạn cung cấp: nhóm thứ 6
        res_buttons = self.driver.find_elements(By.XPATH, "(//div[@class='flex flex-wrap gap-2'])[6]//button")
        print(f"[FPT] Found {len(res_buttons)} resolution buttons")
        
        for r in fpt_resolutions:
            if self._click_button_by_text(res_buttons, r):
                print(f"[FPT] Đã chọn Resolution: {r}")

    def filter_refresh_rates(self, refresh_rates: List[str]):
        if not refresh_rates:
            return
        print(f"[FPT] Filtering Refresh Rates: {refresh_rates}")
        fpt_rates = [self.filter_list.REFRESH_RATE_TGDD_TO_FPT.get(r, r) for r in refresh_rates]
        print(f"[FPT] FPT refresh rate options: {fpt_rates}")
        
        # Selector chính xác theo thông tin bạn cung cấp: nhóm thứ 7
        rate_buttons = self.driver.find_elements(By.XPATH, "(//div[@class='flex flex-wrap gap-2'])[7]//button")
        print(f"[FPT] Found {len(rate_buttons)} refresh rate buttons")
        
        for r in fpt_rates:
            if self._click_button_by_text(rate_buttons, r):
                print(f"[FPT] Đã chọn Refresh Rate: {r}")

    # =============== GET RESULTS ===============
    def get_results(self) -> List[Result]:
        self.results.clear()
        try:
            # Đợi grid container load
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".grid.grid-cols-2.gap-2")
            ))
            time.sleep(2)  # Đợi thêm để sản phẩm load hết

            # Tự động click "Xem thêm" để load hết sản phẩm
            self._load_all_products()

            # Lấy tất cả sản phẩm theo selector từ hướng dẫn
            items = self.driver.find_elements(By.CSS_SELECTOR, ".grid.grid-cols-2.gap-2 .flex-1")
            print(f"[FPT] Tìm thấy {len(items)} sản phẩm")

            for i, item in enumerate(items, 1):
                try:
                    if i == 1:  # Debug item đầu tiên
                        print(f"[FPT] Debug item 1 HTML: {item.get_attribute('outerHTML')[:500]}...")
                    
                    # Tên sản phẩm
                    name = "N/A"
                    try:
                        name_elem = item.find_element(By.CSS_SELECTOR, ".ProductCard_cardTitle__HlwIo")
                        name = name_elem.text.strip()
                    except:
                        # Fallback selector - thử nhiều selector khác
                        try:
                            name_elem = item.find_element(By.CSS_SELECTOR, "h3")
                            name = name_elem.text.strip()
                        except:
                            try:
                                name_elem = item.find_element(By.CSS_SELECTOR, ".card-title")
                                name = name_elem.text.strip()
                            except:
                                try:
                                    name_elem = item.find_element(By.CSS_SELECTOR, "a[title]")
                                    name = name_elem.get_attribute("title").strip()
                                except:
                                    print(f"[FPT] Không tìm thấy tên cho sản phẩm")
                                    continue

                    # Link sản phẩm
                    link = "N/A"
                    try:
                        link_elem = item.find_element(By.CSS_SELECTOR, "a")
                        link = link_elem.get_attribute("href") or "N/A"
                        if link.startswith("/"):
                            link = self.base_url + link
                    except:
                        pass

                    # Giá sản phẩm
                    price = "Không có thông tin"
                    try:
                        price_elem = item.find_element(By.CSS_SELECTOR, ".Price_currentPrice__PBYcv")
                        price = price_elem.text.strip()
                    except:
                        # Fallback selectors
                        try:
                            price_elem = item.find_element(By.CSS_SELECTOR, ".price")
                            price = price_elem.text.strip()
                        except:
                            pass

                    # Hình ảnh sản phẩm
                    img = "N/A"
                    try:
                        img_elem = item.find_element(By.CSS_SELECTOR, "a.flex-1 img")
                        img = img_elem.get_attribute("src") or img_elem.get_attribute("data-src") or "N/A"
                    except:
                        # Fallback
                        try:
                            img_elem = item.find_element(By.TAG_NAME, "img")
                            img = img_elem.get_attribute("src") or img_elem.get_attribute("data-src") or "N/A"
                        except:
                            pass

                    # Thông số kỹ thuật
                    details = []
                    try:
                        specs = item.find_elements(By.CSS_SELECTOR, ".ProductCard_keySellingPoint__426Jm")
                        details = [s.text.strip() for s in specs if s.text.strip()]
                    except:
                        # Fallback
                        try:
                            specs = item.find_elements(By.CSS_SELECTOR, ".specification span")
                            details = [s.text.strip() for s in specs if s.text.strip()]
                        except:
                            pass

                    if name != "N/A":
                        self.results.append(Result(img, name, price, link, details))
                        print(f"[FPT] Đã thêm: {name} - {price}")

                except Exception as e:
                    print(f"[FPT] Lỗi xử lý sản phẩm: {e}")
                    continue

        except Exception as e:
            print(f"[FPT] Lỗi get_results: {e}")
            import traceback
            traceback.print_exc()
        
        return self.results

    def _load_all_products(self):
        """Tự động click nút 'Xem thêm' để load hết sản phẩm"""
        max_clicks = 10  # Giới hạn số lần click để tránh vòng lặp vô hạn
        clicks = 0
        
        while clicks < max_clicks:
            try:
                # Scroll xuống cuối trang trước khi tìm nút "Xem thêm"
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Tìm nút "Xem thêm" với selector chính xác theo HTML bạn cung cấp
                load_more_selectors = [
                    # Selector chính xác nhất: trong div container + button classes
                    "div.flex.justify-center button.Button_root__LQsbl.Button_btnSmall__aXxTy.Button_whitePrimary__nkoMI.Button_btnIconRight__4VSUO",
                    # Selector chính xác theo class CSS
                    "button.Button_root__LQsbl.Button_btnSmall__aXxTy.Button_whitePrimary__nkoMI.Button_btnIconRight__4VSUO",
                    # Fallback với container div
                    "div.flex.justify-center button[class*='Button_root'][class*='Button_btnSmall']",
                    # Fallback selector đơn giản hơn
                    "button[class*='Button_root'][class*='Button_btnSmall']",
                    # Tìm theo text có chứa "Xem thêm" và "kết quả" trong container
                    "//div[contains(@class, 'flex') and contains(@class, 'justify-center')]//button[contains(text(), 'Xem thêm') and contains(text(), 'kết quả')]",
                    # Fallback XPath đơn giản
                    "//button[contains(text(), 'Xem thêm') and contains(text(), 'kết quả')]"
                ]
                
                load_more_button = None
                for selector in load_more_selectors:
                    try:
                        if selector.startswith("//"):
                            # XPath selector
                            buttons = self.driver.find_elements(By.XPATH, selector)
                        else:
                            # CSS selector
                            buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        if buttons:
                            load_more_button = buttons[0]
                            print(f"[FPT] Tìm thấy nút 'Xem thêm' với selector: {selector}")
                            break
                    except Exception as e:
                        continue
                
                if not load_more_button:
                    print("[FPT] Không tìm thấy nút 'Xem thêm'")
                    break
                
                # Kiểm tra nút có hiển thị và clickable không
                if load_more_button.is_displayed() and load_more_button.is_enabled():
                    button_text = load_more_button.text.strip()
                    
                    # Chỉ click nếu là nút "Xem thêm", không click "Thu gọn"
                    if "Xem thêm" in button_text and "kết quả" in button_text:
                        print(f"[FPT] Click nút 'Xem thêm' lần {clicks + 1}: '{button_text}'")
                        
                        # Đếm số sản phẩm trước khi click
                        products_before = len(self.driver.find_elements(By.CSS_SELECTOR, ".grid.grid-cols-2.gap-2 .flex-1"))
                        
                        # Scroll đến nút trước khi click
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
                        time.sleep(0.5)
                        
                        # Click nút
                        self.driver.execute_script("arguments[0].click();", load_more_button)
                        time.sleep(3)  # Đợi content load lâu hơn
                        
                        # Kiểm tra có load thêm sản phẩm không
                        products_after = len(self.driver.find_elements(By.CSS_SELECTOR, ".grid.grid-cols-2.gap-2 .flex-1"))
                        
                        if products_after > products_before:
                            print(f"[FPT] Đã load thêm {products_after - products_before} sản phẩm ({products_before} → {products_after})")
                            clicks += 1
                        else:
                            print("[FPT] Không load thêm được sản phẩm, dừng lại")
                            break
                    else:
                        print(f"[FPT] Bỏ qua nút '{button_text}' (không phải nút Xem thêm)")
                        break
                else:
                    print("[FPT] Nút 'Xem thêm' không khả dụng hoặc không hiển thị")
                    break
                    
            except Exception as e:
                print(f"[FPT] Lỗi khi click 'Xem thêm': {e}")
                break
        
        print(f"[FPT] Đã click 'Xem thêm' {clicks} lần")
        
        # Scroll về đầu trang để chuẩn bị scrape
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)