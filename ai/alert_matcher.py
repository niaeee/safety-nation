"""특보 → 영향권 학교 매칭. 1차 출품판은 region 키 기반 결정론 매칭."""
from typing import List, Dict


def match_schools(alert: Dict, schools: List[Dict]) -> List[Dict]:
    regions = set(alert.get("regions", []))
    return [s for s in schools if s.get("region") in regions]
