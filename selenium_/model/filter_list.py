# from typing import List, Dict, Optional
#
# class FilterList:
#     def __init__(self):
#         self.brands = [
#             "Samsung", "iPhone (Apple)", "OPPO", "Xiaomi", "vivo", "realme",
#             "HONOR", "TCL", "Tecno", "Nokia", "Masstel", "Mobell", "Viettel", "Benco"
#         ]
#         self.price_ranges = [
#             {"name": "Dưới 2 triệu", "data-from": "-1", "data-to": "1999999", "data-href": "duoi-2-trieu"},
#             {"name": "Từ 2 - 4 triệu", "data-from": "2000000", "data-to": "4000000", "data-href": "tu-2-4-trieu"},
#             {"name": "Từ 4 - 7 triệu", "data-from": "4000000", "data-to": "7000000", "data-href": "tu-4-7-trieu"},
#             {"name": "Từ 7 - 13 triệu", "data-from": "7000000", "data-to": "13000000", "data-href": "tu-7-13-trieu"},
#             {"name": "Từ 13 - 20 triệu", "data-from": "13000000", "data-to": "20000000", "data-href": "tu-13-20-trieu"},
#             {"name": "Trên 20 triệu", "data-from": "20000001", "data-to": "-1", "data-href": "tren-20-trieu"}
#         ]
#         self.ram_options = ["3 GB", "4 GB", "6 GB", "8 GB", "12 GB", "16 GB"]
#         self.storage_options = ["64 GB", "128 GB", "256 GB", "512 GB", "1 TB"]
#         self.resolution_options = [
#             "QXGA+", "QQVGA", "QVGA", "HD+", "Full HD+", "1.5K", "1.5K+", "2K+", "Retina (iPhone)"
#         ]
#         self.refresh_rate_options = ["60 Hz", "90 Hz", "120 Hz", "144 Hz"]
#
#     def get_brands(self) -> List[str]:
#         return self.brands
#
#     def get_price_ranges(self) -> List[Dict[str, str]]:
#         return self.price_ranges
#
#     def get_ram_options(self) -> List[str]:
#         return self.ram_options
#
#     def get_storage_options(self) -> List[str]:
#         return self.storage_options
#
#     def get_resolution_options(self) -> List[str]:
#         return self.resolution_options
#
#     def get_refresh_rate_options(self) -> List[str]:
#         return self.refresh_rate_options
#
#     def _parse_memory_value(self, value: str) -> float:
#         """Convert memory value (e.g., '6 GB' or '1 TB') to a numeric value in GB."""
#         value = value.strip()
#         if value.endswith("TB"):
#             return float(value.replace(" TB", "")) * 1024
#         return float(value.replace(" GB", ""))
#
#     def get_filtered_memory(self, value: str, operator: str, options: List[str]) -> List[str]:
#         """
#         Return a list of memory options based on the comparison operator and value.
#         Args:
#             value: Memory value (e.g., '6 GB').
#             operator: Comparison operator ('>=', '<=', '=').
#             options: List of available options (e.g., ram_options or storage_options).
#         Returns:
#             List of memory options that satisfy the comparison.
#         """
#         if not value or value not in options:
#             return []
#         if operator not in [">=", "<=", "="]:
#             return [value] if value in options else []
#
#         target = self._parse_memory_value(value)
#         filtered = []
#
#         for opt in options:
#             opt_value = self._parse_memory_value(opt)
#             if operator == ">=" and opt_value >= target:
#                 filtered.append(opt)
#             elif operator == "<=" and opt_value <= target:
#                 filtered.append(opt)
#             elif operator == "=" and opt_value == target:
#                 filtered.append(opt)
#
#         return filtered
#
#     def get_filtered_resolutions(self, resolutions: List[str]) -> List[str]:
#         """Validate and return a list of valid resolution options."""
#         return [r for r in resolutions if r in self.resolution_options]
#
#     def get_filtered_refresh_rates(self, refresh_rates: List[str]) -> List[str]:
#         """Validate and return a list of valid refresh rate options."""
#         return [r for r in refresh_rates if r in self.refresh_rate_options]



#newFile
from typing import List, Dict

class FilterList:
    def __init__(self):
        # Chuẩn chung: dùng TGDD làm chuẩn
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
        self.resolution_options = [
            "QXGA+", "QQVGA", "QVGA", "HD+", "Full HD+", "1.5K", "1.5K+", "2K+", "Retina (iPhone)"
        ]
        self.refresh_rate_options = ["60 Hz", "90 Hz", "120 Hz", "144 Hz"]

    # --- Mapping từ chuẩn chung sang FPT ---
    BRAND_TGDD_TO_FPT = {
        "iPhone (Apple)": "Apple",
        "realme": "Realme",
        "vivo": "Vivo",
        "Samsung": "Samsung",
        "Xiaomi": "Xiaomi",
        "OPPO": "OPPO",
        "HONOR": "HONOR",
        "TCL": "TCL",
        "Tecno": "Tecno",
        "Nokia": "Nokia",
        "Masstel": "Masstel",
        "Mobell": "Mobell",
        "Viettel": "Viettel",
        "Benco": "Benco"
    }
    REFRESH_RATE_TGDD_TO_FPT = {
        "60 Hz": "60 Hz",
        "90 Hz": "90 Hz",
        "120 Hz": "120 Hz",
        "144 Hz": "Trên 144 Hz"  # Map sang giá trị duy nhất FPT có
    }

    STORAGE_TGDD_TO_FPT = {
        "64 GB": "≤128 GB",
        "128 GB": "≤128 GB",
        "256 GB": "256 GB",
        "512 GB": "512 GB",
        "1 TB": "1 TB"
    }

    RESOLUTION_TGDD_TO_FPT = {
        "Full HD+": "FHD/FHD+",
        "HD+": "HD/HD+",
        "2K+": "2K/2K+",
        "QXGA+": "QXGA",
        "QQVGA": "QQVGA/QVGA",
        "QVGA": "QQVGA/QVGA",
        "1.5K": "1.5K",
        "1.5K+": "1.5K",
        "Retina (iPhone)": "Retina (iPhone)"
    }

    # --- Getter ---
    def get_brands(self) -> List[str]:
        return self.brands

    def get_price_ranges(self) -> List[Dict[str, str]]:
        return self.price_ranges

    def get_ram_options(self) -> List[str]:
        return self.ram_options

    def get_storage_options(self) -> List[str]:
        return self.storage_options

    def get_resolution_options(self) -> List[str]:
        return self.resolution_options

    def get_refresh_rate_options(self) -> List[str]:
        return self.refresh_rate_options

    def _parse_memory_value(self, value: str) -> float:
        value = value.strip()
        if value.endswith("TB"):
            return float(value.replace(" TB", "")) * 1024
        return float(value.replace(" GB", ""))

    def get_filtered_memory(self, value: str, operator: str, options: List[str]) -> List[str]:
        if not value or value not in options:
            return []
        if operator not in [">=", "<=", "="]:
            return [value] if value in options else []
        target = self._parse_memory_value(value)
        filtered = []
        for opt in options:
            opt_value = self._parse_memory_value(opt)
            if operator == ">=" and opt_value >= target:
                filtered.append(opt)
            elif operator == "<=" and opt_value <= target:
                filtered.append(opt)
            elif operator == "=" and opt_value == target:
                filtered.append(opt)
        return filtered

    def get_filtered_resolutions(self, resolutions: List[str]) -> List[str]:
        return [r for r in resolutions if r in self.resolution_options]

    def get_filtered_refresh_rates(self, refresh_rates: List[str]) -> List[str]:
        """Chỉ giữ các refresh rate hợp lệ theo chuẩn chung."""
        return [r for r in refresh_rates if r in self.refresh_rate_options]

    # --- Thêm phương thức map sang FPT ---
    def map_refresh_rates_to_fpt(self, refresh_rates: List[str]) -> List[str]:
        """Chuyển đổi refresh rate từ chuẩn chung sang định dạng FPT."""
        mapped = []
        for r in refresh_rates:
            if r in self.REFRESH_RATE_TGDD_TO_FPT:
                mapped.append(self.REFRESH_RATE_TGDD_TO_FPT[r])
        return mapped