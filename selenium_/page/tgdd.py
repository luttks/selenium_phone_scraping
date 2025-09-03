from typing import List, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time

from selenium_.model.filter_list import FilterList
from selenium_.model.phone_configuration import PhoneConfiguration
from selenium_.model.result import Result

class TGDD:
    PRODUCT_LOCATOR = (By.CSS_SELECTOR, "ul.listproduct li.item.ajaxed.__cate_42")
    VIEW_RESULTS_LOCATOR = (
        By.XPATH,
        "//div[contains(@class, 'filter-button') and contains(@class, 'total')]//a[contains(@class, 'btn-filter-readmore')]"
    )
    LIST_CONTAINER_LOCATOR = (By.CSS_SELECTOR, "ul.listproduct")
    SEE_MORE_LINK = (By.CSS_SELECTOR, "div.view-more > a")
    PRICE_FILTER_LOCATOR = (By.XPATH, "(//div[contains(@class,'filter-list') and contains(@class,'price')])[1]/a")
    RAM_FILTER_LOCATOR = (By.CSS_SELECTOR, ".filter-list.filter-list--ram a")
    STORAGE_FILTER_LOCATOR = (By.CSS_SELECTOR, ".filter-list.filter-list--dung-luong-luu-tru a")
    RESOLUTION_FILTER_LOCATOR = (By.CSS_SELECTOR, ".filter-list.filter-list--do-phan-giai a")
    REFRESH_RATE_FILTER_LOCATOR = (By.CSS_SELECTOR, ".filter-list.filter-list--tan-so-quet a")

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.js = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.base_url = "https://www.thegioididong.com/"
        self.url = self.base_url + "dtdd"
        self.default_number = 20
        self.total_product = 0
        self.results = []
        self.seen_ids = set()
        self.filter_list = FilterList()

    def run(self, phone: PhoneConfiguration, all_results: List[Result]) -> str:
        print("Starting run method with config:", str(phone))
        try:
            self.connect(self.url)
            self.get_filter_elements()
            self.filter_brand(phone.get_brand())
            self.filter_price(phone.get_price_range())
            self.filter_ram(phone.get_ram())
            self.filter_storage(phone.get_storage())
            self.filter_resolutions(phone.get_resolutions())
            self.filter_refresh_rates(phone.get_refresh_rates())
            result_button, total_count = self.get_product_count()
            self.total_product = total_count
            print("Total products found:", self.total_product)
            if self.total_product == 0:
                return ""
            self.click_view_products(result_button)
            self.load_all_product()
            all_results.extend(self.get_results(phone))
            self.print_results()
            return ""
        except Exception as e:
            print("Error in run method:", str(e))
            return str(e)
        finally:
            print("Closing WebDriver")

    def connect(self, url: str):
        self.driver.get(url)

    def get_filter_elements(self):
        try:
            show_filter_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Lọc']")))
            show_filter_button.click()
            self.brand_list = self.driver.find_elements(
                By.XPATH, "(//div[@class='filter-list filter-list--hang manu'])[1]/a")
        except Exception as e:
            print(f"Error in get_filter_elements: {str(e)}")
            raise

    def scroll_to_element(self, element):
        try:
            self.js.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        except:
            pass

    def filter_brand(self, strings: List[str]):
        if not strings:
            return
        for s in strings:
            found = False
            for e in self.brand_list:
                try:
                    brand_name = (e.get_attribute("data-name") or "").lower()
                    print(f"Kiểm tra hãng: {brand_name}, So sánh với: {s.lower()}")
                    if s.lower() in brand_name:
                        self.wait.until(EC.element_to_be_clickable(e))
                        self.scroll_to_element(e)
                        self.js.execute_script("arguments[0].click();", e)
                        print(f"Đã chọn hãng: {brand_name}")
                        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
                        found = True
                        break
                except:
                    continue
            if not found:
                print(f"Không tìm thấy hãng: {s}")

    def filter_price(self, price_href: Optional[str]):
        if not price_href:
            return
        try:
            for e in self.driver.find_elements(*self.PRICE_FILTER_LOCATOR):
                if e.get_attribute("data-href") == price_href:
                    self.wait.until(EC.element_to_be_clickable(e))
                    self.scroll_to_element(e)
                    self.js.execute_script("arguments[0].click();", e)
                    self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
                    break
        except:
            pass

    def filter_ram(self, ram: Optional[Tuple[str, str]]):
        if not ram:
            return
        value, operator = ram
        try:
            filter_elements = self.driver.find_elements(*self.RAM_FILTER_LOCATOR)
            print(f"Found {len(filter_elements)} RAM filter elements")
            for e in filter_elements:
                text = e.text.strip()
                print(f"Available RAM filter: {text}")
            valid_rams = self.filter_list.get_filtered_memory(value, operator, self.filter_list.ram_options)
            print(f"Valid RAM options for {value} {operator}: {valid_rams}")
            for ram_value in valid_rams:
                found = False
                for e in filter_elements:
                    text = e.text.strip()
                    # Normalize text for comparison (e.g., "6 GB" vs "6GB")
                    normalized_text = text.replace(" ", "")
                    normalized_ram_value = ram_value.replace(" ", "")
                    if normalized_text == normalized_ram_value:
                        self.wait.until(EC.element_to_be_clickable(e))
                        self.scroll_to_element(e)
                        self.js.execute_script("arguments[0].click();", e)
                        print(f"Clicked RAM filter: {ram_value}")
                        time.sleep(1)  # Allow page to update
                        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
                        found = True
                        break
                if not found:
                    print(f"Could not find RAM filter element for: {ram_value}")
        except Exception as e:
            print(f"Error filtering RAM: {str(e)}")
            pass

    def filter_storage(self, storage: Optional[Tuple[str, str]]):
        if not storage:
            return
        value, operator = storage
        try:
            valid_storages = self.filter_list.get_filtered_memory(value, operator, self.filter_list.storage_options)
            for storage_value in valid_storages:
                for e in self.driver.find_elements(*self.STORAGE_FILTER_LOCATOR):
                    if e.text.strip() == storage_value:
                        self.wait.until(EC.element_to_be_clickable(e))
                        self.scroll_to_element(e)
                        self.js.execute_script("arguments[0].click();", e)
                        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
                        break
        except Exception as e:
            print(f"Error filtering storage: {str(e)}")
            pass

    def filter_resolutions(self, resolutions: List[str]):
        if not resolutions:
            return
        try:
            valid_resolutions = self.filter_list.get_filtered_resolutions(resolutions)
            for resolution in valid_resolutions:
                resolution_href = resolution.lower().replace(" ", "-").replace("+", "-plus").replace("(", "").replace(")", "")
                for e in self.driver.find_elements(*self.RESOLUTION_FILTER_LOCATOR):
                    if e.get_attribute("data-href") == resolution_href:
                        self.wait.until(EC.element_to_be_clickable(e))
                        self.scroll_to_element(e)
                        self.js.execute_script("arguments[0].click();", e)
                        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
                        break
        except Exception as e:
            print(f"Error filtering resolutions: {str(e)}")
            pass

    def filter_refresh_rates(self, refresh_rates: List[str]):
        if not refresh_rates:
            return
        try:
            filter_elements = self.driver.find_elements(*self.REFRESH_RATE_FILTER_LOCATOR)
            print(f"Found {len(filter_elements)} refresh rate filter elements")
            # Create a mapping of display text to data-href
            href_mapping = {e.text.strip(): e.get_attribute("data-href") or "" for e in filter_elements if
                            e.text.strip()}
            for text, href in href_mapping.items():
                print(f"Available refresh rate filter: {href} ({text})")
            valid_refresh_rates = self.filter_list.get_filtered_refresh_rates(refresh_rates)
            for refresh_rate in valid_refresh_rates:
                # Use the mapping if available, else fallback to manual conversion
                refresh_rate_href = href_mapping.get(
                    refresh_rate,
                    refresh_rate.lower().replace(" ", "-").replace("hz", "hz")  # Fallback: "120 Hz" -> "120-hz"
                )
                print(f"Attempting to filter refresh rate: {refresh_rate} (href: {refresh_rate_href})")
                for e in filter_elements:
                    if e.get_attribute("data-href") == refresh_rate_href:
                        self.wait.until(EC.element_to_be_clickable(e))
                        self.scroll_to_element(e)
                        self.js.execute_script("arguments[0].click();", e)
                        print(f"Clicked refresh rate filter: {refresh_rate}")
                        time.sleep(1)  # Allow page to update
                        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
                        break
                else:
                    print(f"Could not find filter element for refresh rate: {refresh_rate} (href: {refresh_rate_href})")
        except Exception as e:
            print(f"Error filtering refresh rates: {str(e)}")
            raise  # Raise for debugging, revert to pass in production


    def get_product_count(self):
        try:
            result_button = self.wait.until(EC.presence_of_element_located(self.VIEW_RESULTS_LOCATOR))
            total_text_elem = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[contains(@class, 'filter-button') and contains(@class, 'total')]//b[contains(@class, 'total-reloading')]"
                ))
            )
            self.wait.until(lambda d: total_text_elem.text.strip().isdigit())
            total_count = int(total_text_elem.text.strip())
            return result_button, total_count
        except:
            product_items = self.driver.find_elements(*self.PRODUCT_LOCATOR)
            return None, len(product_items)

    def click_view_products(self, result_button):
        try:
            if result_button:
                self.wait.until(EC.element_to_be_clickable(self.VIEW_RESULTS_LOCATOR))
                print("Waiting 1-2 seconds before clicking 'Xem kết quả' button")
                time.sleep(1)
                self.scroll_to_element(result_button)
                self.js.execute_script("arguments[0].click();", result_button)
                self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
        except Exception as e:
            print(f"Error clicking view products: {str(e)}")
            raise

    def load_all_product(self):
        time.sleep(2)
        if self.total_product <= 0:
            print("Không có sản phẩm để tải.")
            return
        try:
            current = len(self.driver.find_elements(*self.PRODUCT_LOCATOR))
            target = self.total_product
            attempts_without_growth = 0
            max_attempts = 5
            print(f"Bắt đầu tải sản phẩm. Hiện tại: {current}, Mục tiêu: {target}")

            if target <= self.default_number:
                print(f"Số sản phẩm ({target}) nhỏ hơn hoặc bằng {self.default_number}, không cần tải thêm.")
                return

            while current < target:
                try:
                    more_btns = self.driver.find_elements(*self.SEE_MORE_LINK)
                    if more_btns and more_btns[0].is_displayed() and more_btns[0].is_enabled():
                        print("Nhấp nút 'Xem thêm'")
                        self.scroll_to_element(more_btns[0])
                        self.js.execute_script("arguments[0].click();", more_btns[0])
                        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
                        time.sleep(2)
                    else:
                        print("Không tìm thấy hoặc không nhấp được nút 'Xem thêm'")
                        attempts_without_growth += 1
                        if attempts_without_growth >= max_attempts:
                            print(f"Dừng tải vì không có sản phẩm mới sau {max_attempts} lần thử.")
                            break
                except Exception as e:
                    print(f"Lỗi khi nhấp nút 'Xem thêm': {str(e)}")
                    attempts_without_growth += 1
                    if attempts_without_growth >= max_attempts:
                        print(f"Dừng tải vì không có sản phẩm mới sau {max_attempts} lần thử.")
                        break

                self.js.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_count = len(self.driver.find_elements(*self.PRODUCT_LOCATOR))
                print(f"Số sản phẩm hiện tại: {new_count}")
                if new_count <= current:
                    attempts_without_growth += 1
                    if attempts_without_growth >= max_attempts:
                        print(f"Dừng tải vì không có sản phẩm mới sau {max_attempts} lần thử.")
                        break
                else:
                    attempts_without_growth = 0
                    current = new_count
            print(f"Tải hoàn tất với {current} sản phẩm")
        except Exception as e:
            print(f"Lỗi khi tải sản phẩm: {str(e)}")

    def _abs_url(self, url: str) -> str:
        if not url:
            return "N/A"
        url = url.strip()
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.base_url.rstrip("/") + url
        return url

    def _pick_img_src(self, img_el) -> str:
        try:
            for attr in ("src", "data-src", "data-original"):
                val = (img_el.get_attribute(attr) or "").strip()
                if val:
                    return self._abs_url(val)
            return "N/A"
        except:
            return "N/A"

    def collect_product(self, element, phone: PhoneConfiguration):
        try:
            data_id = element.get_attribute("data-id") or ""
            if data_id in self.seen_ids:
                print(f"Bỏ qua sản phẩm trùng lặp với data-id: {data_id}")
                return
            if data_id:
                self.seen_ids.add(data_id)
            else:
                print("Cảnh báo: Sản phẩm không có data-id")

            name = "N/A"
            try:
                name_elem = element.find_element(By.CSS_SELECTOR, "a.main-contain h3")
                name = (name_elem.text or name_elem.get_attribute("title") or "").strip()
                if not name:
                    print("Bỏ qua sản phẩm không có tên")
                    return
                print(f"Thu thập sản phẩm: {name}")
            except Exception as e:
                print(f"Lỗi lấy tên sản phẩm: {str(e)}")
                return

            img_url = "N/A"
            try:
                img = element.find_element(By.CSS_SELECTOR, ".item-img.item-img_42 img:not(.lbliconimg)")
                img_url = self._pick_img_src(img)
            except Exception as e:
                print(f"Lỗi lấy hình ảnh cho {name}: {str(e)}")

            link = "N/A"
            try:
                a = element.find_element(By.CSS_SELECTOR, "a.main-contain")
                link = self._abs_url(a.get_attribute("href") or a.get_attribute("data-url") or "")
            except Exception as e:
                print(f"Lỗi lấy liên kết cho {name}: {str(e)}")

            price = "Không có thông tin"
            try:
                for selector in [
                    "strong.price",
                    "span.price",
                    "div.price"
                ]:
                    try:
                        price_elem = element.find_element(By.CSS_SELECTOR, selector)
                        price = price_elem.text.strip() if price_elem.text.strip() else "Không có thông tin"
                        if price != "Không có thông tin":
                            break
                    except:
                        continue
                if price == "Không có thông tin":
                    print(f"Không tìm thấy giá cho {name} với các bộ chọn đã thử")
            except Exception as e:
                print(f"Lỗi lấy giá cho {name}: {str(e)}")

            details = []
            try:
                details = [p.text.strip() for p in element.find_elements(By.CSS_SELECTOR, ".utility p") if p.text.strip()]
                if not details:
                    print(f"Không tìm thấy thông số trong .utility p cho {name}, thử bộ chọn khác")
                    details = [p.text.strip() for p in element.find_elements(By.CSS_SELECTOR, ".item-compare span") if p.text.strip()]
                if not details:
                    print(f"Vẫn không tìm thấy thông số cho {name}")
            except Exception as e:
                print(f"Lỗi lấy thông số cho {name}: {str(e)}")

            self.results.append(Result(img_url, name, price, link, details))
            print(f"Đã thêm sản phẩm: {name}, Giá: {price}, Link: {link}, Hình ảnh: {img_url}, Thông số: {details}")
        except StaleElementReferenceException:
            print(f"Phần tử cũ cho sản phẩm: {name}")
        except Exception as e:
            print(f"Lỗi thu thập sản phẩm: {str(e)}")

    def get_results(self, phone: PhoneConfiguration) -> List[Result]:
        self.results = []
        self.seen_ids.clear()
        try:
            self.load_all_product()
            self.js.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._wait_for_product_list_stable(self.total_product)
            result_elements = self.driver.find_elements(*self.PRODUCT_LOCATOR)
            print(f"Tìm thấy {len(result_elements)} sản phẩm trong ul.listproduct")
            for i, element in enumerate(result_elements, 1):
                try:
                    name = "Không có tên"
                    try:
                        name_elem = element.find_element(By.CSS_SELECTOR, "a.main-contain h3")
                        name = (name_elem.text or name_elem.get_attribute("title") or "").strip()
                    except:
                        pass
                    print(f"Xử lý sản phẩm {i}: {name}")
                    self.collect_product(element, phone)
                except StaleElementReferenceException:
                    print(f"Phần tử cũ cho sản phẩm số {i}: {name}")
                    try:
                        element = self.driver.find_element(By.XPATH,
                                                           f"//h3[contains(text(), '{name}')]//ancestor::li[contains(@class, 'item') and contains(@class, 'ajaxed') and contains(@class, '__cate_42')]")
                        self.collect_product(element, phone)
                    except:
                        print(f"Không thể tìm lại sản phẩm {name}")
                except Exception as e:
                    print(f"Lỗi xử lý sản phẩm số {i}: {str(e)}")
            print(f"Tổng cộng thu thập được {len(self.results)} sản phẩm")
        except Exception as e:
            print(f"Lỗi trong get_results: {str(e)}")
        return self.results

    def _wait_for_product_list_stable(self, expected_total: int, timeout: float = 20.0, poll: float = 0.5):
        end = time.time() + timeout
        last = -1
        stable_ticks = 0
        try:
            self.wait.until(EC.presence_of_all_elements_located(self.PRODUCT_LOCATOR))
        except Exception as e:
            print(f"Lỗi chờ danh sách sản phẩm: {str(e)}")
            return
        while time.time() < end:
            try:
                count = len(self.driver.find_elements(*self.PRODUCT_LOCATOR))
                print(f"Kiểm tra danh sách sản phẩm: {count} sản phẩm")
                if count != last:
                    last = count
                    stable_ticks = 0
                else:
                    stable_ticks += 1
                if (expected_total == 0 or count >= expected_total) and stable_ticks >= int(2.0 / poll):
                    print(f"Danh sách sản phẩm ổn định với {count} sản phẩm")
                    return
                time.sleep(poll)
            except Exception as e:
                print(f"Lỗi khi kiểm tra danh sách sản phẩm: {str(e)}")
                time.sleep(poll)

    def _print_product(self, r: Result, idx: int):
        print(f"[{idx}] {r.name}")
        print(f"  Giá  : {r.price}")
        print(f"  Link : {r.product_link or 'N/A'}")
        print(f"  Ảnh  : {r.image_link or 'N/A'}")
        if r.details:
            print("  Thông số nổi bật:")
            for d in r.details:
                print(f"   - {d}")
        print("-" * 60)

    def print_results(self, results: List[Result] = None):
        results = results or self.results
        if not results:
            print("Chưa có kết quả để in.")
            return
        for i, r in enumerate(results, 1):
            self._print_product(r, i)