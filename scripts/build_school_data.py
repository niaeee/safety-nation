"""학교위치 표준데이터 CSV → 정규화 JSON 빌더.

입력:  data/raw/schoolinfo/전국초중등학교위치표준데이터.csv (CP949)
출력:  data/processed/schools.json
       data/processed/schools.meta.json
       data/processed/schools.ulsan.json (선택)

사용:  python scripts/build_school_data.py
       python scripts/build_school_data.py --no-subset

특징:
    - 표준 라이브러리만 사용 (csv, json, datetime, pathlib)
    - 멱등 실행: 같은 입력 → 같은 출력
    - 원자적 쓰기: .tmp 파일 작성 후 교체
    - 실패 즉시 종료: 학교급/시도 매핑 누락, 위경도 변환 실패, ID 중복
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SOURCE_CSV = ROOT / "data" / "raw" / "schoolinfo" / "전국초중등학교위치표준데이터.csv"
OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_JSON = OUTPUT_DIR / "schools.json"
OUTPUT_META = OUTPUT_DIR / "schools.meta.json"
OUTPUT_ULSAN = OUTPUT_DIR / "schools.ulsan.json"

# 시도교육청명 → 시도 정규화 (17개)
REGION_MAP = {
    "서울특별시교육청": "서울",
    "부산광역시교육청": "부산",
    "대구광역시교육청": "대구",
    "인천광역시교육청": "인천",
    "광주광역시교육청": "광주",
    "대전광역시교육청": "대전",
    "울산광역시교육청": "울산",
    "세종특별자치시교육청": "세종",
    "경기도교육청": "경기",
    "강원특별자치도교육청": "강원",
    "충청북도교육청": "충북",
    "충청남도교육청": "충남",
    "전북특별자치도교육청": "전북",
    "전라남도교육청": "전남",
    "경상북도교육청": "경북",
    "경상남도교육청": "경남",
    "제주특별자치도교육청": "제주",
}

# 학교급구분 → 단축형
LEVEL_MAP = {
    "초등학교": "초",
    "중학교": "중",
    "고등학교": "고",
}

# 한반도 대략 bbox (제주 ~ 백두산 한참 미만, 독도 제외 본토 + 제주)
KR_LAT_MIN, KR_LAT_MAX = 33.0, 39.0
KR_LNG_MIN, KR_LNG_MAX = 124.0, 132.0


def _normalize_region(office_name: str) -> str:
    region = REGION_MAP.get(office_name.strip())
    if region is None:
        raise ValueError(f"알 수 없는 시도교육청명: {office_name!r}")
    return region


def _normalize_level(level_str: str) -> str:
    level = LEVEL_MAP.get(level_str.strip())
    if level is None:
        raise ValueError(f"알 수 없는 학교급구분: {level_str!r}")
    return level


def _pick_address(road: str, jibun: str) -> str:
    road = (road or "").strip()
    if road:
        return road
    jibun = (jibun or "").strip()
    return jibun


def _parse_coord(lat_str: str, lng_str: str, school_id: str) -> tuple[float, float]:
    try:
        lat = float(lat_str)
        lng = float(lng_str)
    except (TypeError, ValueError) as e:
        raise ValueError(f"위경도 변환 실패 (id={school_id}, lat={lat_str!r}, lng={lng_str!r}): {e}")
    if not (KR_LAT_MIN <= lat <= KR_LAT_MAX) or not (KR_LNG_MIN <= lng <= KR_LNG_MAX):
        raise ValueError(f"한반도 bbox 벗어남 (id={school_id}, lat={lat}, lng={lng})")
    return lat, lng


def _atomic_write_json(path: Path, data, *, indent: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


def build(*, write_subset: bool = True) -> int:
    if not SOURCE_CSV.exists():
        print(f"[FAIL] 원본 CSV 없음: {SOURCE_CSV.relative_to(ROOT)}")
        return 1

    schools: list[dict] = []
    seen_ids: set[str] = set()

    with open(SOURCE_CSV, "r", encoding="cp949", newline="") as f:
        reader = csv.DictReader(f)
        for row_no, row in enumerate(reader, start=2):  # 헤더가 1행
            sid = (row.get("학교ID") or "").strip()
            if not sid:
                raise ValueError(f"학교ID 누락 (row={row_no})")
            if sid in seen_ids:
                raise ValueError(f"학교ID 중복: {sid} (row={row_no})")
            seen_ids.add(sid)

            level = _normalize_level(row.get("학교급구분", ""))
            region = _normalize_region(row.get("시도교육청명", ""))
            address = _pick_address(row.get("소재지도로명주소", ""), row.get("소재지지번주소", ""))
            lat, lng = _parse_coord(row.get("위도", ""), row.get("경도", ""), sid)

            schools.append({
                "id": sid,
                "name": (row.get("학교명") or "").strip(),
                "level": level,
                "region": region,
                "address": address,
                "lat": lat,
                "lng": lng,
                "office": (row.get("시도교육청명") or "").strip(),
                "district_office": (row.get("교육지원청명") or "").strip(),
                "establishment_type": (row.get("설립형태") or "").strip(),
                "branch_type": (row.get("본교분교구분") or "").strip(),
                "source_updated_at": (row.get("데이터기준일자") or "").strip(),
            })

    # 정렬: region → level → name → id (멱등성 보장)
    level_order = {"초": 0, "중": 1, "고": 2}
    schools.sort(key=lambda s: (s["region"], level_order[s["level"]], s["name"], s["id"]))

    # 메타
    by_region: dict[str, int] = {}
    by_level: dict[str, int] = {}
    for s in schools:
        by_region[s["region"]] = by_region.get(s["region"], 0) + 1
        by_level[s["level"]] = by_level.get(s["level"], 0) + 1

    meta = {
        "total": len(schools),
        "by_region": dict(sorted(by_region.items(), key=lambda kv: -kv[1])),
        "by_level": {k: by_level.get(k, 0) for k in ("초", "중", "고")},
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_file": str(SOURCE_CSV.relative_to(ROOT)).replace("\\", "/"),
        "schema_version": 1,
    }

    _atomic_write_json(OUTPUT_JSON, schools)
    _atomic_write_json(OUTPUT_META, meta)

    print(f"[PASS] {OUTPUT_JSON.relative_to(ROOT)} ({len(schools):,}건)")
    print(f"[PASS] {OUTPUT_META.relative_to(ROOT)}")

    if write_subset:
        ulsan = [s for s in schools if s["region"] == "울산"]
        _atomic_write_json(OUTPUT_ULSAN, ulsan)
        print(f"[PASS] {OUTPUT_ULSAN.relative_to(ROOT)} (울산 {len(ulsan):,}건)")

    print()
    print("=== 시도별 ===")
    for region, n in meta["by_region"].items():
        print(f"  {region:>4} : {n:>5,}")
    print("=== 학교급별 ===")
    for level, n in meta["by_level"].items():
        print(f"  {level:>4} : {n:>5,}")
    print(f"=== 합계 : {meta['total']:,} ===")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--no-subset", action="store_true", help="울산 서브셋 생성 건너뛰기")
    args = parser.parse_args()
    return build(write_subset=not args.no_subset)


if __name__ == "__main__":
    sys.exit(main())
