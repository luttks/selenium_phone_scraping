from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time
from typing import List, Optional

# Assuming these are defined elsewhere
from selenium_.model.filter_list import FilterList
from selenium_.model.phone_configuration import PhoneConfiguration
from selenium_.model.result import Result

class TGDD:
    # Fixed CSS selector for product tiles
    PRODUCT_LOCATOR = (By.CSS_SELECTOR, "ul.listproduct li.item a.main-contain h3")
    VIEW_RESULTS_LOCATOR = (
        By.XPATH,
        "//div[contains(@class, 'filter-button') and contains(@class, 'total')]//a[contains(@class, 'btn-filter-readmore')]"
    )
    LIST_CONTAINER_LOCATOR = (By.CSS_SELECTOR, "ul.listproduct")
    SEE_MORE_LINK = (By.CSS_SELECTOR, "div.view-more > a")
    PRICE_FILTER_LOCATOR = (By.XPATH, "(//div[contains(@class,'filter-list') and contains(@class,'price')])[1]/a")
    RAM_FILTER_LOCATOR = (By.CSS_SELECTOR, ".filter-list.filter-list--ram a")
    STORAGE_FILTER_LOCATOR = (By.CSS_SELECTOR, ".filter-list.filter-list--dung-luong-luu-tru a")

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.js = driver
        self.wait = WebDriverWait(self.driver, 10)  # Reduced timeout for faster execution
        self.base_url = "https://www.thegioididong.com/"
        self.url = self.base_url + "dtdd"
        self.default_number = 20
        self.total_product = 0
        self.results = []
        self.seen_ids = set()

    def run(self, phone: PhoneConfiguration, all_results: List[Result]) -> str:
        print("Starting run method with config:", str(phone))
        try:
            self.connect(self.url)
            self.get_filter_elements()
            self.filter_brand(phone.get_brand())
            self.filter_price(phone.get_price_range())
            self.filter_ram(phone.get_ram())
            self.filter_storage(phone.get_storage())
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
            # self.driver.quit()

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
            for e in self.brand_list:
                try:
                    if s.lower() in (e.get_attribute("data-name") or "").lower():
                        self.wait.until(EC.element_to_be_clickable(e))
                        self.scroll_to_element(e)
                        self.js.execute_script("arguments[0].click();", e)
                        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
                        break
                except:
                    continue

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

    def filter_ram(self, ram_list: Optional[List[str]]):
        if not ram_list:
            return
        try:
            for ram in ram_list:
                for e in self.driver.find_elements(*self.RAM_FILTER_LOCATOR):
                    if e.text.strip() == ram:
                        self.wait.until(EC.element_to_be_clickable(e))
                        self.scroll_to_element(e)
                        self.js.execute_script("arguments[0].click();", e)
                        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
                        break
        except:
            pass

    def filter_storage(self, storage_list: Optional[List[str]]):
        if not storage_list:
            return
        try:
            for storage in storage_list:
                for e in self.driver.find_elements(*self.STORAGE_FILTER_LOCATOR):
                    if e.text.strip() == storage:
                        self.wait.until(EC.element_to_be_clickable(e))
                        self.scroll_to_element(e)
                        self.js.execute_script("arguments[0].click();", e)
                        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
                        break
        except:
            pass

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
                self.js.execute_script("arguments[0].click();", result_button)
                self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR))
            self.load_all_product()
        except Exception as e:
            print(f"Error clicking view products: {str(e)}")
            raise

    def load_all_product(self):
        if self.total_product <= 0:
            return
        try:
            current = len(self.driver.find_elements(*self.PRODUCT_LOCATOR))
            target = self.total_product
            attempts_without_growth = 0
            while current < target:
                try:
                    more_btns = self.driver.find_elements(*self.SEE_MORE_LINK)
                    if more_btns and more_btns[0].is_displayed() and more_btns[0].is_enabled():
                        self.js.execute_script("arguments[0].click();", more_btns[0])
                except:
                    pass
                self.js.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                try:
                    self.wait.until(
                        lambda d: len(d.find_elements(*self.PRODUCT_LOCATOR)) > current
                    )
                except:
                    pass
                new_count = len(self.driver.find_elements(*self.PRODUCT_LOCATOR))
                if new_count <= current:
                    attempts_without_growth += 1
                    if attempts_without_growth >= 3:
                        break
                else:
                    attempts_without_growth = 0
                    current = new_count
        except Exception as e:
            print(f"Error loading products: {str(e)}")

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
            # Get parent li.item for context
            parent = element.find_element(By.XPATH, "./ancestor::li[contains(@class, 'item')]")
            data_id = parent.get_attribute("data-id") or ""
            if data_id in self.seen_ids:
                return
            if data_id:
                self.seen_ids.add(data_id)

            # Image
            img_url = "N/A"
            try:
                img = parent.find_element(By.CSS_SELECTOR, ".item-img img:not(.lbliconimg)")
                img_url = self._pick_img_src(img)
            except:
                pass

            # Name
            name = (element.text or element.get_attribute("title") or "").strip()
            if not name:
                return

            # Link
            link = "N/A"
            try:
                a = parent.find_element(By.CSS_SELECTOR, "a.main-contain")
                link = self._abs_url(a.get_attribute("href") or a.get_attribute("data-url") or "")
            except:
                pass

            # Price
            price = "Không có thông tin"
            try:
                price = parent.find_element(By.CSS_SELECTOR, "strong.price").text.strip()
            except:
                pass

            # Details
            details = []
            try:
                details = [p.text.strip() for p in parent.find_elements(By.CSS_SELECTOR, ".utility p") if p.text.strip()]
            except:
                pass

            self.results.append(Result(img_url, name, price, link, details))
        except StaleElementReferenceException:
            pass
        except Exception:
            pass

    def get_results(self, phone: PhoneConfiguration) -> List[Result]:
        self.results = []
        self.seen_ids.clear()
        try:
            self.js.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._wait_for_product_list_stable(self.total_product)
            result_elements = self.driver.find_elements(*self.PRODUCT_LOCATOR)
            for element in result_elements:
                self.collect_product(element, phone)
        except Exception as e:
            print(f"Error in get_results: {str(e)}")
        return self.results

    def _wait_for_product_list_stable(self, expected_total: int, timeout: float = 10.0, poll: float = 0.2):
        end = time.time() + timeout
        last = -1
        stable_ticks = 0
        try:
            self.wait.until(EC.presence_of_all_elements_located(self.PRODUCT_LOCATOR))
        except:
            return
        while time.time() < end:
            try:
                count = len(self.driver.find_elements(*self.PRODUCT_LOCATOR))
                if count != last:
                    last = count
                    stable_ticks = 0
                else:
                    stable_ticks += 1
                if (expected_total == 0 or count >= expected_total) and stable_ticks >= int(1.0 / poll):
                    return
                time.sleep(poll)
            except:
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