"""공통 유틸리티 함수"""


def parse_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
