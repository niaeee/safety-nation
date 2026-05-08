"""룰 기반 영향도 산정. AI가 아닌 '설명 가능한 영향도 산정 엔진'으로 표기."""
from typing import Dict

LEVEL_WEIGHT = {"경보": 3, "주의보": 2, "예비특보": 1}
SCHOOL_LEVEL_WEIGHT = {"초": 1.2, "특": 1.3, "중": 1.0, "고": 0.9, "각": 1.0}


def score(school: Dict, alert: Dict) -> Dict:
    base = LEVEL_WEIGHT.get(alert.get("level"), 1)
    factor = SCHOOL_LEVEL_WEIGHT.get(school.get("level"), 1.0)
    raw = base * factor
    if raw >= 3.5:
        grade = "상"
    elif raw >= 2.0:
        grade = "중"
    else:
        grade = "하"
    return {
        "school_id": school["id"],
        "score": round(raw, 2),
        "grade": grade,
        "reason": f"{alert.get('type')} {alert.get('level')} × {school.get('level')}급",
    }
