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
from services.school_data import (
    load_schools,
    load_alerts,
    load_manuals,
    search_schools,
    find_within_radius,
)
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
        return render_template(
            "index.html",
            demo_mode=config.DEMO_MODE,
            map_provider=config.MAP_PROVIDER,
            vworld_api_key=config.VWORLD_API_KEY,
        )

    @app.get("/api/alerts")
    def api_alerts():
        return jsonify(load_alerts())

    @app.get("/api/schools")
    def api_schools():
        # 12K 통째 반환 방어: region/level/limit/offset 미지정이면 전체 반환하지 않음
        region = request.args.get("region")
        level = request.args.get("level")
        q = request.args.get("q")
        try:
            limit = min(int(request.args.get("limit", 100)), 500)
            offset = max(int(request.args.get("offset", 0)), 0)
        except ValueError:
            return jsonify({"error": "limit/offset must be int"}), 400

        if not any([region, level, q]) and request.args.get("all") != "1":
            return jsonify({
                "error": "전국 전체 반환은 ?all=1 필요. 또는 region/level/q 파라미터 사용",
                "hint": "예: /api/schools?region=울산  /api/schools?region=서울&level=초",
            }), 400

        rows = search_schools(query=q, region=region, level=level,
                              limit=limit, offset=offset)
        return jsonify({"count": len(rows), "limit": limit, "offset": offset, "items": rows})

    @app.get("/api/schools/meta")
    def api_schools_meta():
        """현재 활성 데이터셋의 전체 카운트 + 시도/학교급 분포."""
        from collections import Counter
        schools = load_schools()
        by_region = dict(Counter(s["region"] for s in schools))
        by_level = dict(Counter(s["level"] for s in schools))
        return jsonify({
            "total": len(schools),
            "by_region": by_region,
            "by_level": by_level,
        })

    @app.get("/api/schools/map")
    def api_schools_map():
        """지도용 경량 응답: id/이름/학교급/시도/위경도만 반환.

        조회 우선순위: bbox > region > all=1
            ?bbox=south,west,north,east  : 좌표 박스 내 학교 (지도 viewport)
            ?region=서울                  : 시도 전체
            ?all=1                       : 전국 (페이지네이션 없음, 주의)
            ?level=초|중|고               : 모든 모드와 조합 가능
        """
        from services.school_data import find_by_region
        bbox = request.args.get("bbox")
        region = request.args.get("region")
        level = request.args.get("level")

        if bbox:
            try:
                south, west, north, east = (float(x) for x in bbox.split(","))
            except (ValueError, AttributeError):
                return jsonify({"error": "bbox=south,west,north,east (float)"}), 400
            if south > north or west > east:
                return jsonify({"error": "bbox 좌표 순서 오류 (south<=north, west<=east)"}), 400
            base = find_by_region(region) if region else load_schools()
            items = [s for s in base
                     if south <= s["lat"] <= north and west <= s["lng"] <= east]
        elif region:
            items = find_by_region(region)
        elif request.args.get("all") == "1":
            items = load_schools()
        else:
            return jsonify({"error": "bbox 또는 region 또는 all=1 필요"}), 400

        if level:
            items = [s for s in items if s["level"] == level]

        return jsonify([
            {"id": s["id"], "n": s["name"], "lv": s["level"],
             "r": s["region"], "lat": s["lat"], "lng": s["lng"]}
            for s in items
        ])

    @app.get("/api/schools/near")
    def api_schools_near():
        try:
            lat = float(request.args["lat"])
            lng = float(request.args["lng"])
            km = float(request.args.get("km", 5))
            limit = min(int(request.args.get("limit", 50)), 500)
        except (KeyError, ValueError):
            return jsonify({"error": "lat,lng,km(float), limit(int) required"}), 400
        rows = find_within_radius(lat, lng, km, limit=limit)
        return jsonify({"count": len(rows), "center": {"lat": lat, "lng": lng}, "km": km, "items": rows})

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
