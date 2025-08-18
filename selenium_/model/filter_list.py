# from typing import List
#
# class FilterList:
#     def __init__(self):
#         self.brands = [
#             "Samsung", "iPhone (Apple)", "OPPO", "Xiaomi", "vivo", "realme",
#             "HONOR", "TCL", "Tecno", "Nokia", "Masstel", "Mobell", "Viettel", "Benco"
#         ]
#
#     def get_brands(self):
#         return self.brands
#
#     def get_price_ranges(self):
#         return self.price_ranges
#

from typing import List, Dict

class FilterList:
    def __init__(self):
        self.brands = [
            "Samsung", "iPhone (Apple)", "OPPO", "Xiaomi", "vivo", "realme",
            "HONOR", "TCL", "Tecno", "Nokia", "Masstel", "Mobell", "Viettel", "Benco"
        ]
        self.price_ranges = [
            {"name": "Dưới 2 triệu", "data-from": "-1", "data-to": "1999999", "data-href": "duoi-2-trieu"},
            {"name": "Từ 2 - 4 triệu", "data-from": "2000000", "data-to": "4000000", "data-href": "tu-2-4-trieu"},
            {"name": "Từ 4 - 7 triệu", "data-from": "4000000", "data-to": "7000000", "data-href": "tu-4-7-trieu"},
            {"name": "Từ 7 - 13 triệu", "data-from": "7000000", "data-to": "13000000", "data-href": "tu-7-13-trieu"},
            {"name": "Từ 13 - 20 triệu", "data-from": "13000000", "data-to": "20000000", "data-href": "tu-13-20-trieu"},
            {"name": "Trên 20 triệu", "data-from": "20000001", "data-to": "-1", "data-href": "tren-20-trieu"}
        ]
        self.ram_options = ["3 GB", "4 GB", "6 GB", "8 GB", "12 GB", "16 GB"]
        self.storage_options = ["64 GB", "128 GB", "256 GB", "512 GB", "1 TB"]

    def get_brands(self) -> List[str]:
        return self.brands

    def get_price_ranges(self) -> List[Dict[str, str]]:
        return self.price_ranges

    def get_ram_options(self) -> List[str]:
        return self.ram_options

    def get_storage_options(self) -> List[str]:
        return self.storage_options