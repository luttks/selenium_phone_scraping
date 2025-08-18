from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
import requests
from bs4 import BeautifulSoup
from typing import List
from selenium_.model.filter_list import FilterList
from selenium_.model.phone_configuration import PhoneConfiguration
from selenium_.model.result import Result
import re
import time

class TGDD:
    PRODUCT_LOCATOR = (By.CSS_SELECTOR, ".listproduct li.item")
    VIEW_RESULTS_LOCATOR = (
        By.XPATH,
        "//div[contains(@class, 'filter-button') and contains(@class, 'total')]//a[contains(@class, 'btn-filter-readmore')]"
    )
    LIST_CONTAINER_LOCATOR = (By.CSS_SELECTOR, ".listproduct")
    SEE_MORE_CONTAINER = (By.CSS_SELECTOR, "div.view-more")
    SEE_MORE_LINK = (By.CSS_SELECTOR, "div.view-more > a")
    SEE_MORE_REMAIN = (By.CSS_SELECTOR, "div.view-more .remain")

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.js = driver
        self.wait = WebDriverWait(self.driver, 30)
        self.base_url = "https://www.thegioididong.com/"
        self.url = self.base_url + "dtdd"
        self.default_number = 20
        self.total_product = 0
        self.results = []

    def run(self, phone: PhoneConfiguration, all_results: List[Result]) -> str:
        print("Starting run method with config:", str(phone))
        try:
            self.connect(self.url)
            print("Connected to URL:", self.url)
            self.get_filter_elements()
            print("Finished get_filter_elements")
            self.filter_brand(phone.get_brand())
            print("Finished filter_brand")
            self.get_total_number()
            print("Total products found:", self.total_product)
            if self.total_product == 0:
                print("No products found, returning empty string")
                return ""

            # Click 'Xem kết quả' to navigate to the product listing
            self.click_view_results()

            # Load all products
            self.load_all_product()

            # Collect results
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
        print("Connecting to URL:", url)
        self.driver.get(url)

    def get_filter_elements(self):
        print("Starting get_filter_elements")
        try:
            show_filter_button = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[text()='Lọc']")))
            print("Found filter button with text:", show_filter_button.text)
            show_filter_button.click()
            print("Clicked filter button")
            self.brand_list = self.driver.find_elements(
                By.XPATH, "(//div[@class='filter-list filter-list--hang manu'])[1]/a")
            print("Found", len(self.brand_list), "brand elements")
            for e in self.brand_list:
                print("Brand name:", e.get_attribute("data-name"))
        except Exception as e:
            print("Error in get_filter_elements:", str(e))
            raise

    def filter_brand(self, strings: List[str]):
        print("Starting filter_brand with brands:", strings)
        if not strings:
            print("No brands provided, skipping filter")
            return

        for s in strings:
            print("Filtering for brand:", s)
            try:
                # Re-fetch brand list to avoid stale elements
                self.brand_list = self.driver.find_elements(
                    By.XPATH, "(//div[@class='filter-list filter-list--hang manu'])[1]/a")
                for e in self.brand_list:
                    try:
                        brand_name = e.get_attribute("data-name")
                        print("Checking brand:", brand_name)
                        if s.lower() in brand_name.lower():
                            self.wait.until(EC.element_to_be_clickable(e))
                            print("Found matching brand:", brand_name)
                            self.js.execute_script("arguments[0].click();", e)
                            print("Clicked brand:", brand_name)
                            # Wait for product list to update
                            self.wait.until(
                                EC.presence_of_element_located(self.LIST_CONTAINER_LOCATOR),
                                message=f"Timeout waiting for product list after clicking {brand_name}"
                            )
                            time.sleep(2)  # Extended delay for DOM stabilization
                            break
                    except Exception as e:
                        print(f"Error processing brand {brand_name}: {str(e)}")
                        continue
            except Exception as e:
                print(f"Error filtering brand {s}: {str(e)}")
                continue
        print("Finished filter_brand")

    def get_total_number(self):
        print("Starting get_total_number")
        try:
            total_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "b.total-reloading"))
            )
            self.wait.until(lambda d: total_element.text.strip() != "",
                            message="Timeout waiting for text in total-reloading")
            digits = re.sub(r"\D", "", total_element.text)
            print("Found total element with text:", total_element.text)
            print("Total element HTML:", total_element.get_attribute("outerHTML"))
            self.total_product = int(digits) if digits else 0
            print("Parsed total products:", self.total_product)
        except Exception as e:
            print("Error in get_total_number:", str(e))
            raise

    def click_view_results(self):
        try:
            btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.VIEW_RESULTS_LOCATOR)
            )
            current_url = self.driver.current_url
            self.js.execute_script("arguments[0].click();", btn)
            WebDriverWait(self.driver, 20).until(
                lambda d: d.current_url != current_url or
                          len(d.find_elements(*self.LIST_CONTAINER_LOCATOR)) > 0 or
                          len(d.find_elements(*self.PRODUCT_LOCATOR)) > 0
            )
            print("Clicked 'Xem kết quả' and navigated to listing.")
        except Exception as e:
            print("No 'Xem kết quả' button or could not click it:", str(e))

    def load_all_product(self):
        if self.total_product <= 0:
            return

        self._wait_for_min_products(min(self.default_number, self.total_product),
                                    "Timeout waiting for first batch after navigation")

        current = len(self.driver.find_elements(*self.PRODUCT_LOCATOR))
        target = self.total_product
        attempts_without_growth = 0

        while current < target:
            clicked = False
            try:
                more_btns = self.driver.find_elements(*self.SEE_MORE_LINK)
                if more_btns and more_btns[0].is_displayed() and more_btns[0].is_enabled():
                    self.js.execute_script("arguments[0].click();", more_btns[0])
                    clicked = True
            except:
                pass

            if not clicked:
                self.js.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            try:
                self.wait.until(
                    lambda d: len(d.find_elements(*self.PRODUCT_LOCATOR)) > current,
                    message=f"Timeout waiting for more products (> {current})"
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
        for attr in ("src", "data-src", "data-original"):
            val = (img_el.get_attribute(attr) or "").strip()
            if val:
                print(f"Image attribute {attr} found: {val}")
                return self._abs_url(val)
        return "N/A"

    def collect_product(self, element, phone: PhoneConfiguration):
        # Check if the element is a valid product (has data-id and data-price)
        data_id = element.get_attribute("data-id")
        data_price = element.get_attribute("data-price")
        if not data_id or not data_price:
            print(f"Skipping non-product item: {element.get_attribute('outerHTML')[:200]}...")
            return

        try:
            ActionChains(self.driver).move_to_element(element).perform()
            print("Hovered over element for lazy-loading")
            time.sleep(0.5)  # Small delay to ensure image loads
        except:
            print("Failed to hover over element for lazy-loading")

        # Re-fetch the element to avoid stale reference
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, f".listproduct li.item[data-id='{data_id}']")
        except:
            print(f"Error re-fetching element with data-id={data_id}")
            return

        # Image
        img_url = "N/A"
        try:
            img_box = element.find_element(By.CSS_SELECTOR, ".item-img[class*='item-img_']")
            img = WebDriverWait(element, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img:not(.lbliconimg)"))
            )
            img_url = self._pick_img_src(img)
            if img_url == "N/A":
                print("No valid image URL found")
            else:
                print(
                    f"Image found for product: src={img.get_attribute('src')}, data-src={img.get_attribute('data-src')}, resolved_url={img_url}")
        except Exception as e:
            print(f"Error extracting image: {str(e)}")

        # Name
        name = ""
        try:
            h3 = element.find_element(By.CSS_SELECTOR, "h3")
            name = (h3.text or "").strip() or (h3.get_attribute("title") or "").strip()
            print(f"Product name extracted from h3: {name}")
        except:
            try:
                a = element.find_element(By.CSS_SELECTOR, "a.main-contain")
                name = (a.get_attribute("data-name") or "").strip()
                print(f"Product name extracted from data-name: {name}")
            except:
                print(f"Error extracting product name: {element.get_attribute('outerHTML')[:200]}...")
        if not name:
            print("Skipping item due to missing name")
            return

        # Link
        link = "N/A"
        try:
            a = element.find_element(By.CSS_SELECTOR, "a.main-contain")
            href = (a.get_attribute("href") or "").strip()
            if href:
                link = self._abs_url(href)
                print(f"Product link extracted: {link}")
            else:
                data_url = (a.get_attribute("data-url") or "").strip()
                if data_url and data_url != "//":
                    link = self._abs_url(data_url)
                    print(f"Product link (data-url) extracted: {link}")
        except:
            try:
                act = element.find_element(By.CSS_SELECTOR, ".prods-group li.item.act")
                data_url = (act.get_attribute("data-url") or "").strip()
                if data_url and data_url != "//":
                    link = self._abs_url(data_url)
                    print(f"Product link (active version) extracted: {link}")
            except:
                print("Error extracting product link")

        # Price
        try:
            price = element.find_element(By.CSS_SELECTOR, "strong.price").text.strip()
            print(f"Product price extracted: {price}")
        except:
            price = "Không có thông tin"
            print("Error extracting price, defaulting to 'Không có thông tin'")

        # Details
        details = []
        try:
            for p in element.find_elements(By.CSS_SELECTOR, ".utility p"):
                t = p.text.strip()
                if t:
                    details.append(t)
            print(f"Product details extracted: {details}")
        except:
            print("Error extracting product details")

        self.results.append(Result(img_url, name, price, link, details))
        print(f"Product added to results: {name}")

    def get_results(self, phone: PhoneConfiguration) -> List[Result]:
        self.results = []  # Clear previous results
        # Scroll to trigger lazy-loading of images
        try:
            self.js.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Allow lazy-loaded images to load
            print("Scrolled to bottom to trigger lazy-loading")
        except:
            print("Failed to scroll for lazy-loading")

        result_elements = self.wait.until(
            lambda d: len(d.find_elements(*self.PRODUCT_LOCATOR)) > 0 and d.find_elements(*self.PRODUCT_LOCATOR),
            message="Timeout waiting for first batch of products in .listproduct"
        )
        print(f"Found {len(result_elements)} product elements")
        for element in result_elements:
            self.collect_product(element, phone)
        print(f"Collected {len(self.results)} results")
        return self.results

    def _wait_for_min_products(self, min_count: int, timeout_msg: str):
        self.wait.until(
            lambda d: len(d.find_elements(*self.PRODUCT_LOCATOR)) >= min_count,
            message=timeout_msg
        )

    def _print_product(self, r: Result, idx: int):
        print(f"[{idx}] {r.name}")
        print(f"  Giá  : {r.price}")
        print(f"  Link : {r.product_link if r.product_link and r.product_link.strip() else 'N/A'}")
        print(f"  Ảnh  : {r.image_link if r.image_link and r.image_link.strip() else 'N/A'}")
        if r.details:
            print("  Thông số nổi bật:")
            for d in r.details:
                print(f"   - {d}")
        print("-" * 60)

    def print_results(self, results: List[Result] = None):
        results = results if results is not None else self.results
        if not results:
            print("Chưa có kết quả để in.")
            return
        for i, r in enumerate(results, 1):
            self._print_product(r, i)