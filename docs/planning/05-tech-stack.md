# 기술 스택 (Tech Stack)

safety-nation의 기술 선택 및 의사결정

---

## 1. 백엔드 프레임워크

### 선택: Flask 3.0

| 항목 | 내용 |
|---|---|
| **선택** | Flask 3.0 |
| **WSGI 서버** | gunicorn |
| **Python 버전** | 3.12.7 (Railway) |

**선택 이유:**
- 마이크로프레임워크로 단순하고 빠른 학습곡선
- 단일 개발자가 관리하기 좋음 (복잡도 최소)
- RESTful API 구축 최적화
- 공공데이터 처리(JSON) 편리

**대안 검토:**

| 프레임워크 | 장점 | 단점 | 선택 이유 |
|---|---|---|---|
| **FastAPI** | 빠름, 현대적 | 새로운 문법, 실무 노하우 부족 | 검증된 안정성 우선 |
| **Django** | 풍부한 생태계, ORM | 과도, 단일 개발자에겐 부담 | 복잡도 과다 |
| **Flask** | 단순, 유연, 커뮤니티 | 상대적으로 느림 (전체 응답 <100ms 목표이므로 무관) | **선택** |

**트레이드오프:**
- `장점`: 빠른 개발, 유지보수 용이, 확장 자유도
- `단점`: 크기 제한이 있을 경우 성능 조정 필요 (미래 고려)

---

## 2. 데이터베이스

### 선택: SQLite 3 (표준 라이브러리)

| 항목 | 내용 |
|---|---|
| **선택** | SQLite 3 |
| **위치** | `data/reports.db` |
| **스키마** | 최소 2개 테이블 (reports 중심) |

**선택 이유:**
- 파일 기반으로 별도 서버 불필요
- Python 표준 라이브러리 (`sqlite3`)에 포함
- 단일 개발자 운영에 적합 (0 관리 오버헤드)
- 배포 시 `data/` 디렉토리만 포함하면 됨
- 조회만 많은 본 시스템에 충분

**대안 검토:**

| DB | 장점 | 단점 | 선택 이유 |
|---|---|---|---|
| **PostgreSQL** | 확장성, 강력 | 서버 관리 필요, Railway 비용 증가 | 과도한 인프라 |
| **MongoDB** | 유연한 스키마 | NoSQL 학습곡선, 과도 | 스키마 단순 |
| **SQLite** | 경량, 파일 기반, 표준 | 동시성 제약 (읽기만 주로) | **선택** |
| **JSON 파일** | 초간단 | 동시성 없음, 검색 비효율 | 점점 부족할 것 예상 |

**트레이드오프:**
- `장점`: 배포 단순성, 0 관리 비용
- `단점`: 고동시성이 필요하면 차후 PostgreSQL 전환 필요 (현재 불필요)

**마이그레이션 전략** (미래):
```python
# 현재: SQLite
# 미래: PostgreSQL로 변경 시
#   1. 구조는 동일 (SQL 호환성)
#   2. 연결문자열만 변경
#   3. 최소 코드 수정
```

---

## 3. 캐싱 및 인메모리

### 선택: Python 표준 라이브러리 (`functools.lru_cache`)

| 항목 | 내용 |
|---|---|
| **선택** | `functools.lru_cache` |
| **용도** | 학교 데이터, 지역 경계 정보 |
| **TTL** | 없음 (프로세스 단위, 재배포 시 갱신) |

**선택 이유:**
- 데코레이터로 간단하게 적용
- 외부 의존성 없음
- 공공데이터는 자주 변하지 않음 (주 1회 재배포 모형)
- Railway는 무상태(stateless) 지향 → 프로세스당 캐시로 충분

**대안 검토:**

| 캐시 | 장점 | 단점 | 선택 이유 |
|---|---|---|---|
| **Redis** | 분산, 영속성 | 외부 서비스, Railway 비용, 관리 필요 | 과도 |
| **Memcached** | 빠름 | 설정 복잡 | 과도 |
| **lru_cache** | 내장, 단순 | 단일 프로세스 | **선택** |

---

## 4. 프론트엔드

### 선택: 정적 HTML + 바닐라 JavaScript

| 항목 | 내용 |
|---|---|
| **HTML** | 정적 마크업 |
| **CSS** | 인라인 style + `<style>` 블록 |
| **JS** | 바닐라 (프레임워크 없음) |
| **빌드** | 없음 (그대로 배포) |

**선택 이유:**
- 단순성: 의존성 0, 빌드 프로세스 없음
- 배포 속도: HTML 파일만 서빙
- 개발 속도: 즉시 새로고침으로 확인
- 성능: 브라우저 기본 캐싱 활용

**대안 검토:**

| 스택 | 장점 | 단점 | 선택 이유 |
|---|---|---|---|
| **React** | 컴포넌트, 상태 관리 | 빌드 필요, 번들 크기, 학습곡선 | 과도 |
| **Vue.js** | 가볍고 빠름 | 여전히 빌드 필요 | 단순성 우선 |
| **Vanilla JS** | 의존성 0, 빠름 | 코드량 증가 | **선택** |

**HTML 구조:**
```
index.html (단일 페이지)
├── §0 헤더
├── §1 학교 분포 (Leaflet)
├── §2 특보 모니터링
├── §3 보고서 초안
├── §4 보고서 이력 (신규)
└── §5 통계 대시보드 (신규)
```

---

## 5. 지도 라이브러리

### 선택: Leaflet 1.9.4 + Leaflet.markercluster 1.5.3

| 항목 | 내용 |
|---|---|
| **라이브러리** | Leaflet (CDN) |
| **클러스터링** | Leaflet.markercluster |
| **타일** | VWorld (운영) / OpenStreetMap (폴백) |

**선택 이유:**
- 가볍고 빠름 (12K 마커 처리 최적화)
- 마커 클러스터링으로 줌 레벨별 동적 표시
- 반응형 웹 지원
- 라이선스 자유로움

**대안 검토:**

| 라이브러리 | 장점 | 단점 | 선택 이유 |
|---|---|---|---|
| **Google Maps** | 강력, 부자연스럽지 않음 | 키 관리, API 비용 | 비용 |
| **Mapbox** | 아름다운 UX | 유료 | 비용 |
| **Leaflet** | 경량, 확장 가능 | 커스텀 필요 | **선택** |

**타일 선택:**

| 타일 | 장점 | 단점 | 사용처 |
|---|---|---|---|
| **VWorld** | 국토부 공식, 한글 지명 | 일 한도(5만/key), 키 관리 | 운영 모드 |
| **OpenStreetMap** | 무제한, 안정적 | 영어, 정확도 낮음 | 폴백 |

**마이그레이션 전략:**
```javascript
// 환경변수로 타일 선택
const MAP_PROVIDER = process.env.MAP_PROVIDER || 'vworld';
const tileUrl = MAP_PROVIDER === 'vworld' 
  ? 'https://api.vworld.kr/...' 
  : 'https://tile.openstreetmap.org/...';
```

---

## 6. 차트 라이브러리 (신규)

### 선택: Chart.js 4.x (CDN)

| 항목 | 내용 |
|---|---|
| **라이브러리** | Chart.js 4.x |
| **배포** | CDN (npm 없음) |
| **차트 유형** | Line, Bar, Doughnut, (Box plot custom) |

**선택 이유:**
- 가볍고 빠름 (바닐라 JS와 호환)
- 반응형 레이아웃 자동 지원
- 호버 인터랙션 내장
- 다크 모드 커스텀 쉬움

**대안 검토:**

| 라이브러리 | 장점 | 단점 | 선택 이유 |
|---|---|---|---|
| **D3.js** | 강력한 커스터마이징 | 가파른 학습곡선, 무거움 | 복잡도 과다 |
| **Recharts** | React 통합 | 빌드 필요 | 프레임워크 없음 |
| **Chart.js** | 간단, 가벼움, CDN | 제한된 커스터마이징 | **선택** |

---

## 7. AI / LLM 통합

### 선택: Anthropic Claude (3중 어댑터)

| 항목 | 내용 |
|---|---|
| **SDK** | `anthropic` Python 패키지 (pip) |
| **CLI** | `claude` 명령어 (별도 설치) |
| **Fallback** | Template 기반 초안 생성 |

**3중 어댑터 구조:**

```
1단계: SDK 모드
├─ anthropic.Anthropic() 라이브러리 호출
├─ timeout: 60초
└─ 성공 시 반환

2단계: CLI 모드 (SDK 실패 시)
├─ subprocess로 "claude -p" 호출
├─ timeout: 60초
└─ 성공 시 반환

3단계: Template Fallback (CLI도 실패 시)
├─ 템플릿 기반 초안 자동 생성
└─ 항상 성공 (다운타임 0)
```

**선택 이유:**
- Claude 3.5 Sonnet: 성능과 비용의 균형
- SDK + CLI 이중화: 신뢰성 향상
- Template fallback: 다운타임 완전 제거
- API 키 관리: Railway 환경변수로 관리

**비용 및 토큰:**
- 모델: claude-3-5-sonnet-20241022
- 예상: 보고서당 ~1,500 tokens (입력 200, 출력 300)
- 대회 시연용 한도: 일일 10만 tokens 목표 (약 67건)
- 과초 시 template fallback으로 자동 커버

**대안 검토:**

| 모델 | 장점 | 단점 | 선택 이유 |
|---|---|---|---|
| **GPT-4** | 성능 최고 | API 비용 높음, 의존성 | 비용 |
| **Llama** | 오픈소스, 저비용 | 호스팅 필요, 성능 낮음 | 인프라 |
| **Claude 3.5** | 우수한 성능, 합리적 비용 | | **선택** |

---

## 8. 배포 인프라

### 선택: Railway (Hobby Plan)

| 항목 | 내용 |
|---|---|
| **플랫폼** | Railway.app |
| **런타임** | Python 3.12.7 |
| **설정파일** | Procfile, runtime.txt |
| **도메인** | `https://safety-nation-production.up.railway.app` |

**선택 이유:**
- GitHub 연동으로 자동 배포
- 환경변수 관리 간편
- Python 런타임 자동 감지
- 단일 개발자에게 무료/저비용 플랜 충분

**Procfile 예시:**
```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

**runtime.txt:**
```
python-3.12.7
```

**대안 검토:**

| 플랫폼 | 장점 | 단점 | 선택 이유 |
|---|---|---|---|
| **Heroku** | 검증됨, 간단 | 무료 플랜 폐지, 비용 증가 | 비용 |
| **Vercel** | JS 최적화 | Python 지원 제한 | 언어 미스매치 |
| **Railway** | Git 연동, 저비용, 편함 | 상대적으로 새로움 | **선택** |

---

## 9. 기타 도구 및 라이브러리

### 요청 HTTP 클라이언트

| 항목 | 선택 |
|---|---|
| 백엔드 (Python) | `requests` 라이브러리 |
| 프론트엔드 (JS) | `fetch` API (내장) |

**선택 이유:**
- `requests`: 표준적, 안정적
- `fetch`: 의존성 0, 최신 브라우저 지원

### 로깅

| 항목 | 선택 |
|---|---|
| 라이브러리 | Python 표준 `logging` |
| 출력 | `logs/benchmark.jsonl` (NDJSON) |

**선택 이유:**
- 표준 라이브러리, 의존성 0
- NDJSON: 한 줄씩 파싱 가능 (대용량 로그에 유리)

### 테스트

| 항목 | 선택 |
|---|---|
| 프레임워크 | pytest |
| 위치 | `tests/test_*.py` |

**선택 이유:**
- 단순하고 강력한 문법
- 픽스처(fixture) 지원 편함
- 플러그인 생태계 풍부

---

## 10. 환경변수 명명 규칙

### 환경변수 목록

| 변수명 | 값 | 용도 | 기본값 |
|---|---|---|---|
| `FLASK_ENV` | `production` \| `development` | Flask 환경 | `production` |
| `SECRET_KEY` | 32B 랜덤 문자열 | Flask 세션 서명 | 필수 (Railway 설정) |
| `DEBUG` | `True` \| `False` | Flask 디버그 모드 | `False` |
| `DEMO_MODE` | `true` \| `false` | 데모/운영 모드 | `true` |
| `ANTHROPIC_API_KEY` | API 키 | Claude SDK 호출 | 선택사항 |
| `MAP_PROVIDER` | `vworld` \| `osm` | 지도 타일 선택 | `vworld` |
| `VWORLD_API_KEY` | API 키 | VWorld 타일 API | 필수 (운영) |
| `LOG_LEVEL` | `DEBUG` \| `INFO` \| `WARNING` | 로깅 레벨 | `INFO` |
| `BENCHMARK_LOG_PATH` | 파일 경로 | 벤치마크 로그 위치 | `logs/benchmark.jsonl` |
| `REPORTS_DB_PATH` | 파일 경로 | SQLite DB 위치 | `data/reports.db` |

### Railway 환경변수 설정

```bash
# Railway Dashboard 또는 CLI로 설정
railway variable set SECRET_KEY "$(openssl rand -hex 16)"
railway variable set ANTHROPIC_API_KEY "sk-ant-..."
railway variable set VWORLD_API_KEY "..."
railway variable set DEMO_MODE "false"
```

---

## 11. 보안 고려사항

### HTTPS & CSP

| 항목 | 구성 |
|---|---|
| **HTTPS** | Railway 자동 (*.up.railway.app) |
| **HSTS** | 활성화 (Talisman 사용 검토) |
| **CSP** | Content-Security-Policy 헤더 설정 |

### 비밀값 관리

| 항목 | 관리 |
|---|---|
| **API 키** | 환경변수 (Railway 대시보드) |
| **DB 비밀번호** | SQLite (파일 기반, 권한 제어) |
| **SECRET_KEY** | 32B 난수 (배포 시 생성) |

### 식별정보 검증

| 항목 | 도구 |
|---|---|
| **스크립트** | `scripts/check_identifiers.py` |
| **대상** | 데모 fixture, 샘플 데이터 |
| **빌드 훅** | CI/CD에서 실행 (선택) |

---

## 12. 성능 목표 및 최적화

### 성능 목표

| 엔드포인트 | 목표 | 측정 기준 |
|---|---|---|
| `/api/schools/map?region=...` | ≤ 100ms | 응답 시간 |
| 보고서 생성 (AI) | P95 ≤ 30초 | benchmark.jsonl |
| 12K 마커 첫 로드 | ≤ 2초 | Railway 사이트 스피드 |
| 통계 대시보드 | ≤ 2초 | 차트 렌더링 |

### 최적화 전략

**백엔드:**
- lru_cache로 학교 데이터 인메모리 캐싱
- 요청별 JSON 최소화 (필요 필드만)

**프론트엔드:**
- Leaflet markercluster로 초기 렌더링 최적화
- 이미지 압축 (icon PNG)
- defer 속성으로 JS 로드 지연

**배포:**
- gunicorn 워커 수 4개 (Railway Hobby 기준)
- gzip 압축 활성화

---

## 13. 개발 환경 세팅

### 로컬 개발 (Mac/Linux/Windows)

```bash
# 1. Python 3.10+ 설치
python --version  # 3.10 이상

# 2. 가상환경
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 3. 의존성
pip install -r requirements.txt

# 4. 환경변수 (.env 또는 shell)
export FLASK_ENV=development
export DEMO_MODE=true

# 5. 실행
python app.py  # 또는 flask run
# 접속: http://localhost:5000
```

### requirements.txt

```
Flask==3.0.0
gunicorn==21.2.0
requests==2.31.0
anthropic==0.7.0  # 선택사항
Talisman==1.1.0  # 선택사항 (보안)
```

---

## 14. 향후 확장 시나리오

### Scale Up 가능성

**현재 → 향후:**

| 항목 | 현재 | 향후 | 마이그레이션 비용 |
|---|---|---|---|
| 백엔드 | Flask | FastAPI | 높음 (구조 변경) |
| DB | SQLite | PostgreSQL | 낮음 (SQL 호환) |
| 캐시 | lru_cache | Redis | 중간 (추상화 필요) |
| 인증 | 없음 | JWT/OAuth | 높음 (로직 추가) |

**마이그레이션 전략:**
- 현재: 단순하고 빠른 시연 우선
- 향후: 필요할 때 (사용자 증가 시) 개선
- 코드 구조: 모듈화로 교체 최소화

---

## 15. 라이선스 및 저작권

| 항목 | 라이선스 | 비고 |
|---|---|---|
| Flask | BSD-3-Clause | 상업 사용 가능 |
| Leaflet | BSD 2-Clause | 무료 |
| Chart.js | MIT | 무료 |
| VWorld 타일 | CC-BY-4.0 | 저작자 표시 필수 |
| 학교알리미 데이터 | CC-BY-4.0 | 저작자 표시 필수 |

---

## 16. 기술 스택 검증 체크리스트

- [x] 백엔드 프레임워크 선택 및 이유 명시
- [x] 데이터베이스 선택 및 마이그레이션 전략
- [x] 프론트엔드 스택 (빌드 없음, 바닐라 JS)
- [x] 지도 라이브러리 + 타일 선택
- [x] AI/LLM 3중 어댑터 구조
- [x] 배포 인프라 (Railway)
- [x] 환경변수 명명 규칙
- [x] 성능 목표 및 최적화 전략
- [x] 개발 환경 세팅
- [x] 향후 확장 시나리오 및 마이그레이션 경로

---

**문서 버전**: v1.0  
**생성일**: 2026-05-10  
**기술 스택 확정**: 최종  
**마지막 수정**: TBD  
