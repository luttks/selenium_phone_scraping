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
        print("Starting run method with brand:", phone.get_brand())
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

                # QUAN TRỌNG: Bấm 'Xem kết quả' để rời panel lọc và sang trang danh sách
            self.click_view_results()

            # Tải toàn bộ (nếu cần)
            self.load_all_product()


            # Thu thập kết quả
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
        if strings:
            for s in strings:
                print("Filtering for brand:", s)
                for e in self.brand_list:
                    brand_name = e.get_attribute("data-name")
                    print("Checking brand:", brand_name)
                    if s.lower() in brand_name.lower():
                        self.wait.until(EC.element_to_be_clickable(e))
                        print("Found matching brand:", brand_name)
                        self.js.execute_script("arguments[0].click();", e)
                        print("Clicked brand:", brand_name)
                        break
        print("Finished filter_brand")


    def get_total_number(self):
        print("Starting get_total_number")
        try:
            total_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "b.total-reloading"))
            )
            # chờ có text
            self.wait.until(lambda d: total_element.text.strip() != "",
                            message="Timeout waiting for text in total-reloading")

            # Lọc tất cả chữ số để tránh ký tự lạ
            digits = re.sub(r"\D", "", total_element.text)
            print("Found total element with text:", total_element.text)
            print("Total element HTML:", total_element.get_attribute("outerHTML"))

            self.total_product = int(digits) if digits else 0
            print("Parsed total products:", self.total_product)
        except Exception as e:
            print("Error in get_total_number:", str(e))
            raise

    def click_view_results(self):
        """
        Nếu có nút 'Xem kết quả' thì bấm để chuyển sang trang danh sách.
        Chờ URL đổi hoặc grid danh sách xuất hiện.
        """
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
            # Có thể trang đã ở dạng danh sách, nên không sao
            print("No 'Xem kết quả' button or could not click it:", str(e))

    def load_all_product(self):
        if self.total_product <= 0:
            return

        # Đợi lô đầu tiên
        self._wait_for_min_products(min(self.default_number, self.total_product),
                                    "Timeout waiting for first batch after navigation")

        current = len(self.driver.find_elements(*self.PRODUCT_LOCATOR))
        target = self.total_product
        attempts_without_growth = 0

        while current < target:
            clicked = False
            # Thử click "Xem thêm" nếu xuất hiện
            try:
                more_btns = self.driver.find_elements(By.CSS_SELECTOR, "div.view-more > a")
                if more_btns and more_btns[0].is_displayed() and more_btns[0].is_enabled():
                    self.js.execute_script("arguments[0].click();", more_btns[0])
                    clicked = True
            except:
                pass

            if not clicked:
                # Fallback: scroll để lazy-load
                self.js.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Chờ số item tăng
            self.wait.until(
                lambda d: len(d.find_elements(*self.PRODUCT_LOCATOR)) > current,
                message=f"Timeout waiting for more products (> {current})"
            )

            new_count = len(self.driver.find_elements(*self.PRODUCT_LOCATOR))
            if new_count <= current:
                attempts_without_growth += 1
                if attempts_without_growth >= 3:
                    break
            else:
                attempts_without_growth = 0
                current = new_count

    def collect_product(self, element, phone: PhoneConfiguration):
        # Đưa chuột để lazyload ảnh (nếu có)
        try:
            ActionChains(self.driver).move_to_element(element).perform()
        except:
            pass

        # Ảnh
        try:
            img = element.find_element(By.CSS_SELECTOR, ".item-img img").get_attribute("src") or ""
        except:
            img = ""

        # Tên máy – ưu tiên text h3, fallback title
        name = ""
        try:
            h3 = element.find_element(By.CSS_SELECTOR, "h3")
            name = (h3.text or "").strip() or (h3.get_attribute("title") or "").strip()
        except:
            pass

        # Link (nếu có, nhưng không bắt buộc)
        link = ""
        try:
            a = element.find_element(By.CSS_SELECTOR, "a.main-contain")
            link = a.get_attribute("href") or ""
        except:
            # fallback: lấy thẻ a đầu tiên trong item
            try:
                a_any = element.find_element(By.CSS_SELECTOR, "a[href]")
                link = a_any.get_attribute("href") or ""
            except:
                link = ""

        # Giá
        try:
            price = element.find_element(By.CSS_SELECTOR, "strong.price").text.strip()
        except:
            price = "Không có thông tin"

        # Details ngay trong list (không vào trang chi tiết)
        details = []
        try:
            for p in element.find_elements(By.CSS_SELECTOR, ".utility p"):
                t = p.text.strip()
                if t:
                    details.append(t)
        except:
            pass

        # Nếu tên trống thì bỏ qua item rác/quảng cáo
        if not name:
            return

        self.results.append(Result(img, name, price, link, details))


    def get_results(self, phone: PhoneConfiguration) -> List[Result]:
        # Đợi có ít nhất 1 item trong listproduct
        result_elements = self.wait.until(
            lambda d: len(d.find_elements(*self.PRODUCT_LOCATOR)) > 0 and d.find_elements(*self.PRODUCT_LOCATOR),
            message="Timeout waiting for first batch of products in .listproduct"
        )
        for element in result_elements:
            self.collect_product(element, phone)
        return self.results

    def _wait_for_min_products(self, min_count: int, timeout_msg: str):
        """
        Chờ đến khi số lượng thẻ sản phẩm >= min_count.
        Dùng trong quá trình bấm 'Xem thêm' để đảm bảo đã load đủ lô tiếp theo.
        """
        self.wait.until(
            lambda d: len(d.find_elements(*self.PRODUCT_LOCATOR)) >= min_count,
            message=timeout_msg
        )

    def _print_product(self, r: Result, idx: int):
        """In thông tin 1 sản phẩm theo format dễ đọc."""
        print(f"[{idx}] {getattr(r, 'name', 'N/A')}")
        print(f"  Giá  : {getattr(r, 'price', 'N/A')}")
        print(f"  Link : {getattr(r, 'link', 'N/A')}")
        print(f"  Ảnh  : {getattr(r, 'img', getattr(r, 'image', 'N/A'))}")
        details = getattr(r, 'details', None)
        if details:
            print("  Thông số nổi bật:")
            for d in details:
                print(f"   - {d}")
        print("-" * 60)

    def print_results(self, results: List[Result] = None):
        """
        In toàn bộ danh sách sản phẩm (nếu không truyền thì dùng self.results).
        """
        results = results if results is not None else self.results
        if not results:
            print("Chưa có kết quả để in.")
            return
        for i, r in enumerate(results, 1):
            self._print_product(r, i)




