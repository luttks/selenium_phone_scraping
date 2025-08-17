from typing import List, Optional

class PhoneConfiguration:
    def __init__(self, brand: Optional[List[str]] = None):
        self.brand = brand

    def get_brand(self):
        return self.brand

    def __str__(self):
        return f"PhoneConfiguration(brand={self.brand})"