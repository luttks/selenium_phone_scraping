from typing import List

class FilterList:
    def __init__(self):
        self.brands = [
            "Samsung", "iPhone (Apple)", "OPPO", "Xiaomi", "vivo", "realme",
            "HONOR", "TCL", "Tecno", "Nokia", "Masstel", "Mobell", "Viettel", "Benco"
        ]

    def get_brands(self):
        return self.brands

    def get_price_ranges(self):
        return self.price_ranges