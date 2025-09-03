from typing import List, Optional, Tuple

class PhoneConfiguration:
    def __init__(
        self,
        brand: Optional[List[str]] = None,
        price_range: Optional[str] = None,
        ram: Optional[Tuple[str, str]] = None,  # (value, operator)
        storage: Optional[Tuple[str, str]] = None,  # (value, operator)
        resolutions: Optional[List[str]] = None,
        refresh_rates: Optional[List[str]] = None
    ):
        self._brand = brand or []
        self._price_range = price_range
        self._ram = ram
        self._storage = storage
        self._resolutions = resolutions or []
        self._refresh_rates = refresh_rates or []

    def get_brand(self) -> List[str]:
        return self._brand

    def get_price_range(self) -> Optional[str]:
        return self._price_range

    def get_ram(self) -> Optional[Tuple[str, str]]:
        return self._ram

    def get_storage(self) -> Optional[Tuple[str, str]]:
        return self._storage

    def get_resolutions(self) -> List[str]:
        return self._resolutions

    def get_refresh_rates(self) -> List[str]:
        return self._refresh_rates

    def __str__(self) -> str:
        return (f"PhoneConfiguration(brand={self._brand}, "
                f"price_range={self._price_range}, "
                f"ram={self._ram}, storage={self._storage}, "
                f"resolutions={self._resolutions}, refresh_rates={self._refresh_rates})")