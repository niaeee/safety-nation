"""학교 데이터 로더. DEMO_MODE에서는 data/demo/만 사용."""
import json
from pathlib import Path
import config

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_schools():
    if config.DEMO_MODE:
        with open(DATA_DIR / "demo" / "schools.json", encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError("운영 데이터 로딩은 아직 구현되지 않았습니다. DEMO_MODE=true 로 실행하세요.")


def load_alerts():
    if config.DEMO_MODE:
        with open(DATA_DIR / "demo" / "weather_alerts.json", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_manuals():
    with open(DATA_DIR / "demo" / "manuals.json", encoding="utf-8") as f:
        return json.load(f)
