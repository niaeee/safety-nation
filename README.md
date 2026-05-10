# safety-nation — AI 학교 재난영향 예측·자동보고 시스템

> 제8회 교육 공공데이터 AI 활용대회 출품작 (전국 확장판 데모)
> 합의 방향: **기존 코드 이식 + 3개 권역 비식별 데모 + 특보 기반 자동보고 시나리오 + AI 보고서 초안 + 정량 측정 로그**

## 핵심 시나리오 (1개 완결 업무흐름)

`기상특보 입력 → 영향권 학교 자동 식별 → 룰 기반 영향도 산정 → AI(claude -p) 보고서 초안 → 담당자 결재 배지 → 처리시간 로그 저장`

## 빠른 시작 (데모 모드)

```bash
cd safety-nation
python -m venv .venv && .venv/Scripts/activate    # Windows
pip install -r requirements.txt
cp .env.example .env                              # DEMO_MODE=true
python app.py                                     # http://localhost:5000
```

## 운영 모드 (전국 12,011개 학교)

```bash
# 1) 원본 CSV (학교알리미 표준데이터, CP949) 배치
#    data/raw/schoolinfo/전국초중등학교위치표준데이터.csv

# 2) 정규화 JSON 빌드 (멱등 실행, 표준 라이브러리만)
python scripts/build_school_data.py
#  → data/processed/schools.json        (12,011건)
#  → data/processed/schools.meta.json   (시도/학교급별 통계 + 생성시각)
#  → data/processed/schools.ulsan.json  (울산 245건, 시연/성능 테스트용)

# 3) 운영 모드 실행
DEMO_MODE=false SCHOOL_DATASET=national python app.py
#   SCHOOL_DATASET=ulsan 로 바꾸면 울산 245개만 로드
#   MAP_PROVIDER=vworld + VWORLD_API_KEY=... 로 VWorld 타일 전환 가능
```

### 학교 검색 API

```
GET /api/schools?region=울산&level=초&limit=10
GET /api/schools/near?lat=37.57&lng=126.97&km=3
GET /api/schools/map?bbox=37.4,126.7,37.7,127.2   # 지도 viewport용 경량
```

## E2E 처리시간 측정

```bash
python scripts/benchmark_e2e.py 5
# logs/benchmark_e2e.jsonl 에 누적
```

## 제출 전 식별정보 스캔

```bash
python scripts/check_identifiers.py
```

## 폴더 구조

```
safety-nation/
├── app.py                  Flask app + /api/draft 엔드포인트
├── config.py               환경변수 중앙 설정
├── ai/
│   ├── alert_matcher.py    특보 → 영향학교 매칭 (결정론)
│   ├── risk_engine.py      룰 기반 영향도 산정 (AI 아님 — 명확히 분리)
│   ├── report_drafter.py   ClaudeCliDrafter + TemplateDrafter fallback
│   └── prompts/disaster_report.md
├── data/
│   ├── demo/               비식별 fixture (schools/alerts/manuals)
│   ├── raw/schoolinfo/     원본 학교 위치 CSV (CP949)
│   └── processed/          빌드 산출 JSON (전국/울산/메타)
├── services/
│   ├── school_data.py      DEMO/운영 분기 + lru_cache + region/level 인덱스 + Haversine 반경 검색
│   └── (exporters, weather, coordinates 등 기존 이식분)
├── scripts/
│   ├── build_school_data.py CP949 CSV → 정규화 JSON 빌더
│   ├── benchmark_e2e.py    처리시간 측정
│   └── check_identifiers.py 제출 전 식별정보 스캔
├── templates/index.html    Leaflet 지도 + markercluster + AI disclaimer
└── logs/                   benchmark.jsonl (gitignore)
```

## 운영 원칙

- **AI 보조판단, 최종 결재는 사람.** 모든 보고서 초안 하단·UI 푸터 고정 배치.
- **DEMO_MODE 기본 ON.** 운영 데이터 로딩 차단.
- **claude -p는 timeout 60초 + TemplateDrafter fallback.** 시연 안전.
- **룰베이스 영향도는 AI라 부르지 않는다.** AI 활용도는 보고서 초안 생성에서 입증.

## 다음 작업

1. `claude -p` 설치 확인 후 `python scripts/benchmark_e2e.py 5` 실행 → 측정값 확보
2. 새 GitHub repo 생성 → 초기 커밋 푸시 → Railway 배포
3. 실제 KMA/NEIS API 키 발급되면 `services/weather.py` 활성화 (DEMO_MODE=false 분기)
4. 기획서 본문(3~15쪽) 작성 시 logs/benchmark.jsonl 수치를 정량 효과 근거로 인용
