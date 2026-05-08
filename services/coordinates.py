"""좌표 관련 서비스: 주소 정규화, 유효성 검증, 지오코딩, 거리 계산"""
import math
import time
import logging
from collections import OrderedDict

import requests
from config import KAKAO_API_KEY
from services.utils import parse_float  # noqa: E402

logger = logging.getLogger(__name__)
KAKAO_TIMEOUT_SEC = 5
MAX_ADDRESS_LENGTH = 200

GEOCODE_CACHE: OrderedDict = OrderedDict()
GEOCODE_CACHE_TTL_SEC = 60 * 60 * 24
GEOCODE_CACHE_MAX = 300

REQUEST_SESSION = requests.Session()


def normalize_address(address):
    """주소 정규화 및 길이 제한

    Returns:
        str: 정규화된 주소 문자열
        None: 유효하지 않은 입력인 경우
    """
    if address is None:
        return ""
    if not isinstance(address, str):
        return None  # 비문자열 타입은 None 반환 (호출측에서 400 처리)

    addr = " ".join(address.split())
    if len(addr) > MAX_ADDRESS_LENGTH:
        addr = addr[:MAX_ADDRESS_LENGTH]
    return addr


def validate_coordinates(lat, lng):
    """좌표 유효성 검증

    Args:
        lat: 위도 (float or None)
        lng: 경도 (float or None)

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if lat is None or lng is None:
        return False, "좌표 정보가 필요합니다."

    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return False, "좌표는 숫자여야 합니다."

    # 대한민국 범위: 위도 33~43, 경도 124~132
    # 여유를 두어 조금 더 넓은 범위 허용
    if not (32.0 <= lat_f <= 44.0):
        return False, "위도가 유효한 범위(32~44)를 벗어났습니다."

    if not (123.0 <= lng_f <= 133.0):
        return False, "경도가 유효한 범위(123~133)를 벗어났습니다."

    return True, None


def cleanup_expired_cache():
    """만료된 캐시 항목 정리"""
    now = time.time()
    expired_keys = [
        k for k, v in GEOCODE_CACHE.items()
        if now - v["ts"] >= GEOCODE_CACHE_TTL_SEC
    ]
    for key in expired_keys:
        del GEOCODE_CACHE[key]


def cache_coordinates(address, lat, lng):
    """좌표를 캐시에 저장 (LRU 정책 적용)"""
    now = time.time()

    # 주기적으로 만료된 항목 정리 (캐시가 50% 이상 찼을 때)
    if len(GEOCODE_CACHE) >= GEOCODE_CACHE_MAX // 2:
        cleanup_expired_cache()

    # 캐시가 가득 찼으면 가장 오래된 항목 제거 (LRU)
    if len(GEOCODE_CACHE) >= GEOCODE_CACHE_MAX:
        GEOCODE_CACHE.popitem(last=False)

    GEOCODE_CACHE[address] = {"lat": lat, "lng": lng, "ts": now}


def get_coordinates(address):
    """Kakao 로컬 API로 주소를 위도/경도로 변환 (주소 검색 실패 시 키워드 검색)"""
    address = normalize_address(address)
    if not address:
        return None, None

    if not KAKAO_API_KEY:
        return None, None

    now = time.time()

    # 캐시 조회 (LRU: 조회된 항목을 맨 뒤로 이동)
    if address in GEOCODE_CACHE:
        cached = GEOCODE_CACHE[address]
        if now - cached["ts"] < GEOCODE_CACHE_TTL_SEC:
            GEOCODE_CACHE.move_to_end(address)  # LRU 갱신
            return cached["lat"], cached["lng"]
        else:
            del GEOCODE_CACHE[address]  # 만료된 항목 제거

    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

    # 1차: 주소 검색 시도, 2차: 키워드 검색
    for url in (
        "https://dapi.kakao.com/v2/local/search/address.json",
        "https://dapi.kakao.com/v2/local/search/keyword.json",
    ):
        params = {"query": address}
        try:
            response = REQUEST_SESSION.get(
                url,
                headers=headers,
                params=params,
                timeout=KAKAO_TIMEOUT_SEC,
            )
            if response.status_code != 200:
                continue
            data = response.json()
        except (requests.RequestException, ValueError):
            logger.warning("Kakao API 요청 실패", exc_info=True)
            continue

        if data.get('documents'):
            doc = data['documents'][0]
            lat = parse_float(doc.get('y'))
            lng = parse_float(doc.get('x'))
            if lat is not None and lng is not None:
                cache_coordinates(address, lat, lng)
                return lat, lng

    return None, None


def haversine(lat1, lng1, lat2, lng2):
    """Haversine 공식으로 두 좌표 간 거리 계산 (km)"""
    R = 6371  # 지구 반지름 (km)

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
