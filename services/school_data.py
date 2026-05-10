"""학교 데이터 로더 — DEMO/운영 통일 스키마, 메모리 캐시 + 인덱스.

데이터 소스 결정 (config.DEMO_MODE, config.SCHOOL_DATASET):
    DEMO_MODE=true                              → data/demo/schools.json (가짜 데이터)
    DEMO_MODE=false, SCHOOL_DATASET=national    → data/processed/schools.json (12,011건)
    DEMO_MODE=false, SCHOOL_DATASET=ulsan       → data/processed/schools.ulsan.json (245건)

표준 스키마 (필수 키): id, name, level, region, address, lat, lng
운영 추가 필드: office, district_office, establishment_type, branch_type, source_updated_at

캐시 정책: 프로세스 시작 시 1회 로드 (lru_cache). 재배포로 갱신.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import config

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEMO_PATH = DATA_DIR / "demo" / "schools.json"
PROCESSED_NATIONAL = DATA_DIR / "processed" / "schools.json"
PROCESSED_ULSAN = DATA_DIR / "processed" / "schools.ulsan.json"

REQUIRED_KEYS = ("id", "name", "level", "region", "address", "lat", "lng")


def _resolve_schools_path() -> Path:
    if config.DEMO_MODE:
        return DEMO_PATH
    if (config.SCHOOL_DATASET or "national") == "ulsan":
        return PROCESSED_ULSAN
    return PROCESSED_NATIONAL


def _validate_record(rec: dict, idx: int) -> dict:
    missing = [k for k in REQUIRED_KEYS if k not in rec]
    if missing:
        raise ValueError(f"학교 레코드 키 누락 (idx={idx}): {missing}")
    return rec


@lru_cache(maxsize=1)
def _load_tuple() -> tuple:
    """파일을 1회 읽어 immutable tuple로 반환."""
    path = _resolve_schools_path()
    if not path.exists():
        raise FileNotFoundError(
            f"학교 데이터 파일 없음: {path}. "
            "운영 모드라면 'python scripts/build_school_data.py'로 생성하세요."
        )
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"학교 데이터 최상위가 list가 아님: {path}")
    return tuple(_validate_record(r, i) for i, r in enumerate(data))


@lru_cache(maxsize=1)
def _index_by_region() -> dict:
    idx: dict[str, list] = {}
    for s in _load_tuple():
        idx.setdefault(s["region"], []).append(s)
    return {k: tuple(v) for k, v in idx.items()}


@lru_cache(maxsize=1)
def _index_by_level() -> dict:
    idx: dict[str, list] = {}
    for s in _load_tuple():
        idx.setdefault(s["level"], []).append(s)
    return {k: tuple(v) for k, v in idx.items()}


@lru_cache(maxsize=1)
def _index_by_id() -> dict:
    return {s["id"]: s for s in _load_tuple()}


def _reset_cache() -> None:
    """테스트/운영 환경 전환 시에만 사용."""
    _load_tuple.cache_clear()
    _index_by_region.cache_clear()
    _index_by_level.cache_clear()
    _index_by_id.cache_clear()


# ---------- public API ----------

def load_schools() -> list:
    """모든 학교 레코드 반환 (기존 시그니처 호환)."""
    return list(_load_tuple())


def load_alerts() -> list:
    if config.DEMO_MODE:
        with open(DATA_DIR / "demo" / "weather_alerts.json", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_manuals() -> dict:
    with open(DATA_DIR / "demo" / "manuals.json", encoding="utf-8") as f:
        return json.load(f)


def get_school_by_id(school_id: str) -> dict | None:
    return _index_by_id().get(school_id)


def find_by_region(region: str) -> list:
    return list(_index_by_region().get(region, ()))


def find_by_level(level: str) -> list:
    return list(_index_by_level().get(level, ()))


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 간 대원 거리(km). 지구 반지름 6371km 가정."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def find_within_radius(lat: float, lng: float, km: float, *, limit: int = 100) -> list:
    """기준 좌표에서 km 반경 내 학교를 가까운 순으로 반환. 각 항목에 distance_km 추가."""
    if km <= 0:
        return []
    # bbox 사전 필터로 후보 축소 (1도 ≈ 111 km, 경도는 cos(위도) 보정)
    dlat = km / 111.0
    cos_lat = math.cos(math.radians(lat))
    dlng = km / (111.0 * (abs(cos_lat) or 1e-9))
    out = []
    for s in _load_tuple():
        if abs(s["lat"] - lat) > dlat or abs(s["lng"] - lng) > dlng:
            continue
        d = _haversine_km(lat, lng, s["lat"], s["lng"])
        if d <= km:
            out.append({**s, "distance_km": round(d, 3)})
    out.sort(key=lambda x: x["distance_km"])
    return out[:limit]


def search_schools(
    *,
    query: str | None = None,
    region: str | None = None,
    level: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list:
    """이름/지역/학교급 복합 필터. region 필터는 인덱스 사용."""
    if region:
        rows = list(_index_by_region().get(region, ()))
    else:
        rows = list(_load_tuple())
    if level:
        rows = [s for s in rows if s["level"] == level]
    if query:
        q = query.strip().lower()
        rows = [s for s in rows if q in s["name"].lower()]
    return rows[offset:offset + limit]
