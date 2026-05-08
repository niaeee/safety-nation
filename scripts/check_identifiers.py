"""제출 전 식별정보 스캔. 발견 시 종료코드 1.

사용: python scripts/check_identifiers.py
"""
import re
import sys
import io
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ["templates", "static", "data/demo", "ai/prompts"]
SCAN_FILES_GLOB = ["*.py", "*.html", "*.json", "*.md", "*.txt"]

BANNED = [
    r"울산", r"광역시교육청(?!.*○○)", r"태화강", r"이홍우",
    r"고래\.?I", r"안전총괄과", r"정책관 정책기획팀",
    r"safety-production-218b",
]
# 학교명 휴리스틱 (○○ 학교 A-001 같은 비식별 형식은 통과)
SCHOOL_NAME_RX = re.compile(r"[가-힣]{2,}(초등학교|중학교|고등학교|특수학교)")


def scan() -> int:
    hits = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for pattern in SCAN_FILES_GLOB:
            for path in base.rglob(pattern):
                text = path.read_text(encoding="utf-8", errors="ignore")
                for rx in BANNED:
                    for m in re.finditer(rx, text):
                        hits.append((path, rx, m.group()))
                for m in SCHOOL_NAME_RX.finditer(text):
                    hits.append((path, "학교명", m.group()))

    if hits:
        print("[FAIL] 식별정보 의심 항목 발견:")
        for p, rx, sample in hits:
            print(f"  - {p.relative_to(ROOT)} : [{rx}] '{sample}'")
        return 1
    print("[PASS] 식별정보 스캔 통과")
    return 0


if __name__ == "__main__":
    sys.exit(scan())
