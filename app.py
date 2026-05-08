"""safety-nation Flask app — 특보 기반 자동보고 데모.

핵심 흐름: GET /api/alerts → POST /api/draft (alert_id) → 영향학교 매칭 + 룰 영향도 + AI 초안
"""
import json
import logging
import secrets
import time
from pathlib import Path
from flask import Flask, jsonify, render_template, request

import config
from services.school_data import load_schools, load_alerts, load_manuals
from ai.alert_matcher import match_schools
from ai.risk_engine import score as risk_score
from ai.report_drafter import get_drafter

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("safety-nation")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY or secrets.token_hex(32)
    app.json.ensure_ascii = False

    drafter = get_drafter()

    @app.get("/")
    def index():
        return render_template("index.html", demo_mode=config.DEMO_MODE)

    @app.get("/api/alerts")
    def api_alerts():
        return jsonify(load_alerts())

    @app.get("/api/schools")
    def api_schools():
        return jsonify(load_schools())

    @app.post("/api/draft")
    def api_draft():
        body = request.get_json(force=True, silent=True) or {}
        alert_id = body.get("alert_id")
        alerts = {a["id"]: a for a in load_alerts()}
        if alert_id not in alerts:
            return jsonify({"error": "unknown alert_id"}), 400
        alert = alerts[alert_id]
        affected = match_schools(alert, load_schools())
        scored = [{**s, **risk_score(s, alert)} for s in affected]
        manual = load_manuals().get(alert["type"], {})
        context = {"alert": alert, "affected_schools": scored, "manual": manual}

        t0 = time.time()
        draft = drafter.draft(context)
        elapsed = round(time.time() - t0, 3)

        log_entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "alert_id": alert_id,
            "matched_schools": len(affected),
            "draft_source": draft.source,
            "draft_elapsed_sec": draft.elapsed_sec,
            "endpoint_elapsed_sec": elapsed,
            "input_hash": draft.input_hash,
            "error": draft.error,
        }
        with open(LOG_DIR / "benchmark.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        logger.info("draft generated: %s", log_entry)

        return jsonify({
            "alert": alert,
            "affected_count": len(affected),
            "scored_schools": scored,
            "draft": {
                "text": draft.text,
                "source": draft.source,
                "elapsed_sec": draft.elapsed_sec,
                "error": draft.error,
            },
            "disclaimer": "본 초안은 AI 보조판단 결과이며 최종 판단·결재는 안전 담당자가 수행합니다.",
        })

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=(config.FLASK_ENV != "production"))
