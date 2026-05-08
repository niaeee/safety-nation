"""특보 → 보고서 초안 E2E 처리시간 측정.

사용: python scripts/benchmark_e2e.py [iterations]
출력: logs/benchmark_e2e.jsonl 추가, 콘솔에 통계 요약.
"""
import json
import sys
import time
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.school_data import load_alerts, load_schools, load_manuals
from ai.alert_matcher import match_schools
from ai.risk_engine import score
from ai.report_drafter import get_drafter


def run(iterations: int = 3):
    drafter = get_drafter()
    alerts = load_alerts()
    schools = load_schools()
    manuals = load_manuals()
    log_path = Path(__file__).resolve().parent.parent / "logs" / "benchmark_e2e.jsonl"
    log_path.parent.mkdir(exist_ok=True)

    samples = []
    for i in range(iterations):
        for alert in alerts:
            t0 = time.time()
            affected = match_schools(alert, schools)
            scored = [{**s, **score(s, alert)} for s in affected]
            ctx = {"alert": alert, "affected_schools": scored, "manual": manuals.get(alert["type"], {})}
            r = drafter.draft(ctx)
            elapsed = time.time() - t0
            samples.append(elapsed)
            entry = {
                "iter": i, "alert": alert["id"], "affected": len(affected),
                "source": r.source, "elapsed_sec": round(elapsed, 3), "error": r.error,
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(entry)

    if samples:
        print(f"\n=== 통계 (n={len(samples)}) ===")
        print(f"  mean   : {statistics.mean(samples):.2f}s")
        print(f"  median : {statistics.median(samples):.2f}s")
        print(f"  max    : {max(samples):.2f}s")
        print(f"  min    : {min(samples):.2f}s")


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
