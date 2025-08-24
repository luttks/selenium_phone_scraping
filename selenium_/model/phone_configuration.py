# from typing import List, Optional
#
# class PhoneConfiguration:
#     def __init__(self, brand: Optional[List[str]] = None):
#         self.brand = brand
#
#     def get_brand(self):
#         return self.brand
#
#     def __str__(self):
#         return f"PhoneConfiguration(brand={self.brand})"

# from typing import List, Optional
#
# class PhoneConfiguration:
#     def __init__(
#         self,
#         brand: Optional[List[str]] = None,
#         price_range: Optional[str] = None,
#         ram: Optional[List[str]] = None,
#         storage: Optional[List[str]] = None
#     ):
#         self.brand = brand
#         self.price_range = price_range  # e.g., "duoi-2-trieu"
#         self.ram = ram  # e.g., ["4 GB", "8 GB"]
#         self.storage = storage  # e.g., ["128 GB", "256 GB"]
#
#     def get_brand(self) -> Optional[List[str]]:
#         return self.brand
#
#     def get_price_range(self) -> Optional[str]:
#         return self.price_range
#
#     def get_ram(self) -> Optional[List[str]]:
#         return self.ram
#
#     def get_storage(self) -> Optional[List[str]]:
#         return self.storage
#
#     def __str__(self) -> str:
#         return (f"PhoneConfiguration(brand={self.brand}, price_range={self.price_range}, "
#                 f"ram={self.ram}, storage={self.storage})")

from typing import List, Optional, Tuple

class PhoneConfiguration:
    def __init__(
        self,
        brand: Optional[List[str]] = None,
        price_range: Optional[str] = None,
        ram: Optional[Tuple[str, str]] = None,  # (value, operator)
        storage: Optional[Tuple[str, str]] = None  # (value, operator)
    ):
        self._brand = brand or []
        self._price_range = price_range
        self._ram = ram
        self._storage = storage

    def get_brand(self) -> List[str]:
        return self._brand

    def get_price_range(self) -> Optional[str]:
        return self._price_range

    def get_ram(self) -> Optional[Tuple[str, str]]:
        return self._ram

    def get_storage(self) -> Optional[Tuple[str, str]]:
        return self._storage

    def __str__(self) -> str:
        return (f"PhoneConfiguration(brand={self._brand}, "
                f"price_range={self._price_range}, "
                f"ram={self._ram}, storage={self._storage})")