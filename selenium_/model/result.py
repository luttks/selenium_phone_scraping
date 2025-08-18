from typing import List

class Result:
    def __init__(self, img_url: str, name: str, price: str, product_link: str, details: List[str]):
        self.image_link = img_url
        self.name = name
        self.price = price
        self.product_link = product_link
        self.details = details

    def __str__(self):
        return (f"Result(image_link={self.image_link}, name={self.name}, price={self.price}, "
                f"product_link={self.product_link}, details={self.details})")