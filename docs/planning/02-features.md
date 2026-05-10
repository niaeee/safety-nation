# 기능 명세서 (Feature Specifications)

safety-nation의 5대 기능 상세 명세

---

## F1. 학교 정보 조회·시각화

### 목적

사용자가 지도 상에서 전국 12,011개 학교의 분포를 한눈에 파악하고, 시도·학교급 필터로 관심 지역의 학교를 빠르게 찾는다.

### 입력 및 출력

| 항목 | 내용 |
|---|---|
| **입력** | 시도명, 학교급(초/중/고), 지도 영역, 학교명 검색어 |
| **출력** | Leaflet 지도 마커, 팝업 (학교명/시도/급/아이디) |
| **API** | `GET /api/schools/map?region=&level=&bbox=` |

### 인수기준 (Acceptance Criteria)

- **AC-1.1**: 17개 시도 다중선택 가능 (동시 선택 가능)
- **AC-1.2**: 3개 학교급(초/중/고) 독립적으로 체크박스 선택
- **AC-1.3**: 마커 클릭 → 팝업 (학교명, 시도, 학교급, ID 표시)
- **AC-1.4**: 12,011개 마커 첫 로드 ≤ 2초 (Railway 환경)
- **AC-1.5**: 시도 변경 시 지도 카메라가 부드럽게 전환 (D-lite 애니메이션)
- **AC-1.6**: 마커 클러스터링으로 줌 레벨에 따라 숫자 표시
- **AC-1.7**: 필터 변경 후 마커 즉시 업데이트 (≤ 500ms)

### 의존성

없음 (초기 로드 단계)

### 우선순위

**P0** (필수) — 시스템 진입점

### 구현 가이드

```javascript
// 예시: 시도 필터 변경 시 마커 업데이트
function updateMarkers(region, levels) {
  const filters = {
    region: region,  // 예: "서울특별시"
    level: levels    // 예: ["초등학교", "중학교"]
  };
  
  fetch(`/api/schools/map?region=${filters.region}&level=${filters.level.join(',')}`)
    .then(r => r.json())
    .then(data => {
      // 마커 레이어 초기화
      clearMarkers();
      // 새 마커 추가
      data.schools.forEach(school => {
        addMarker(school.lat, school.lng, school.name);
      });
      // 카메라 이동
      if (region) {
        mapCamera.flyTo(getRegionBounds(region), { duration: 1 });
      }
    });
}
```

---

## F2. 특보 모니터링·매칭

### 목적

기상특보(호우주의보, 강풍주의보 등)를 실시간으로 모니터링하고, 영향권에 속한 학교를 자동으로 식별한다.

### 입력 및 출력

| 항목 | 내용 |
|---|---|
| **입력** | 특보 정보 (발령 시각, 영향 지역, 특보 유형, 강도) |
| **출력** | 활성 특보 목록, 매칭된 학교 목록, 위험도 점수 |
| **API** | `GET /api/alerts/active`, `POST /api/alerts/match` |

### 인수기준 (Acceptance Criteria)

- **AC-2.1**: 활성 특보를 카드 형식으로 표시 (발령 시각, 유형, 영향 시군구)
- **AC-2.2**: 각 카드에 "영향 학교 수" 미리 표시
- **AC-2.3**: 특보 카드 클릭 → 매칭 API 호출, 영향학교 목록 반환
- **AC-2.4**: 17개 시도 region명 정확히 일치 (예: "서울특별시", "부산광역시" 등)
- **AC-2.5**: 매칭 결과는 100% 재현 가능 (결정론적 알고리즘)
- **AC-2.6**: 위험도 점수 계산: 초등학교 1.0, 중학교 0.8, 고등학교 0.6 가중치
- **AC-2.7**: 매칭 완료 후 F1 지도의 해당 학교 마커 붉은 테두리로 강조
- **AC-2.8**: 비활성 특보는 회색으로 표시, 클릭 불가

### 의존성

F1 (지도 준비, 학교 데이터 필요)

### 우선순위

**P0** (필수) — 핵심 기능

### 구현 가이드

```python
# 백엔드: region 기반 매칭 로직
def match_schools(alert_region, schools_data):
    """
    alert_region: "서울특별시"
    schools_data: [{id, name, region, level}, ...]
    return: 매칭된 학교 목록 + 위험도 점수
    """
    matched = []
    
    for school in schools_data:
        if school['region'] == alert_region:
            # 학교급별 가중치
            weight = {
                '초등학교': 1.0,
                '중학교': 0.8,
                '고등학교': 0.6
            }.get(school['level'], 0)
            
            matched.append({
                'id': school['id'],
                'name': school['name'],
                'level': school['level'],
                'risk_score': weight
            })
    
    # 위험도 점수 내림차순 정렬
    matched.sort(key=lambda x: x['risk_score'], reverse=True)
    return matched
```

---

## F3. AI 보고서 초안 자동 생성

### 목적

특보 메타데이터·영향학교·표준 매뉴얼을 입력으로 Anthropic Claude를 호출하여, 학교 안전 담당자가 즉시 검토·결재할 수 있는 보고서 초안을 자동 생성한다.

### 입력 및 출력

| 항목 | 내용 |
|---|---|
| **입력** | 특보 ID, 영향학교 목록 (학교명·시도·급·위험도), 표준 매뉴얼 문구 |
| **출력** | 보고서 초안 (마크다운 형식), 생성 시간, 출처 (cli/sdk/template) |
| **API** | `POST /api/reports/draft` |

### 인수기준 (Acceptance Criteria)

- **AC-3.1**: 보고서 생성 P95 처리시간 ≤ 30초
- **AC-3.2**: AI 모드 실패 시 TemplateDrafter fallback으로 자동 생성 (다운타임 0)
- **AC-3.3**: 모든 출력에 "AI 보조판단, 담당자 검토 필수" disclaimer 고정 표시
- **AC-3.4**: `draft.source` 필드에 생성 출처 명시: "cli", "sdk", "template" 중 하나
- **AC-3.5**: 보고서에 매칭된 학교 테이블 포함 (학교명, 시도, 학교급, 위험도)
- **AC-3.6**: 특보 유형별 표준 문구 포함 (예: "호우주의보 발령 시 …")
- **AC-3.7**: 처리 시간 로깅 (benchmark.jsonl에 기록)

### 의존성

F2 (영향학교 매칭 필요)

### 우선순위

**P0** (필수) — 핵심 기능

### 구현 가이드

```python
# 백엔드: 3중 어댑터 구조
class ReportDrafter:
    def draft(self, alert, matched_schools, manual_text):
        """
        3단계:
        1. SDK 모드 시도 (Claude API 호출)
        2. 실패 시 CLI 모드 시도 (subprocess로 claude -p 호출)
        3. 둘 다 실패 시 Template fallback (템플릿 기반 초안)
        """
        
        # 1단계: SDK 모드
        try:
            prompt = self._build_prompt(alert, matched_schools, manual_text)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return {
                'text': response.content[0].text,
                'source': 'sdk',
                'elapsed_sec': response.usage.input_tokens / 1000  # 대략
            }
        except Exception as e:
            logger.warning(f"SDK 모드 실패: {e}")
            
            # 2단계: CLI 모드
            try:
                result = subprocess.run(
                    ['claude', '-p', self._build_prompt(...)],
                    timeout=60,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return {
                        'text': result.stdout,
                        'source': 'cli',
                        'elapsed_sec': 60
                    }
            except Exception as e:
                logger.warning(f"CLI 모드 실패: {e}")
            
            # 3단계: Template fallback
            return {
                'text': self._template_fallback(alert, matched_schools),
                'source': 'template',
                'elapsed_sec': 0.1
            }
    
    def _build_prompt(self, alert, matched_schools, manual_text):
        """Claude 프롬프트 작성"""
        return f"""
당신은 교육부 안전 담당 공무원입니다.
다음 정보를 바탕으로 학교 안전 보고서 초안을 작성하세요.

[특보 정보]
- 유형: {alert['type']}
- 발령 시각: {alert['issued_at']}
- 영향 지역: {alert['region']}
- 강도: {alert['intensity']}

[영향 학교 목록]
{self._format_schools_table(matched_schools)}

[표준 매뉴얼]
{manual_text}

[요구사항]
1. 특보 유형별 표준 문구 포함
2. 영향 학교 수와 교급 분포 언급
3. 권장 조치사항 제시
4. 존댓말 사용

보고서는 마크다운 형식으로 작성하세요.
"""
    
    def _template_fallback(self, alert, matched_schools):
        """Template 기반 보고서 자동 생성"""
        template = f"""
# {alert['issued_at']} {alert['type']} 보고서

## 특보 정보
- **유형**: {alert['type']}
- **강도**: {alert['intensity']}
- **영향 지역**: {alert['region']}

## 영향 학교
총 {len(matched_schools)}개 학교가 영향권에 있습니다.

| 학교명 | 시도 | 학교급 | 위험도 |
|---|---|---|---|
{self._format_schools_rows(matched_schools)}

## 권장 조치
- 학교 안전 점검 실시
- 야외활동 중단 고려
- 학부모·교직원 안전 공지

---
*이 보고서는 AI 보조판단으로 생성되었습니다. 담당자의 검토 및 승인이 필수입니다.*
"""
        return template
```

---

## F4. 보고서 저장·검색·이전 사례 참조 (신규)

### 목적

생성된 보고서를 SQLite에 저장하여, 나중에 검색·조회할 수 있고, 동일 특보 유형의 이전 사례를 자동으로 추천받는다. P1 시도 담당자가 의사결정 근거를 수집할 수 있다.

### 입력 및 출력

| 항목 | 내용 |
|---|---|
| **입력** | 저장할 보고서 (텍스트, 메타데이터), 검색 조건 (특보 유형, 지역, 날짜) |
| **출력** | 저장된 보고서 목록, 유사 사례 순위 |
| **API** | `POST /api/reports/save`, `GET /api/reports/list`, `GET /api/reports/{id}` |

### 인수기준 (Acceptance Criteria)

- **AC-4.1**: SQLite 테이블 생성 및 관리 (자동)
  - 스키마: `reports (id, ts, alert_type, alert_region, schools_affected, draft_text, source)`
- **AC-4.2**: "저장" 버튼 클릭 → 현재 보고서를 DB에 insert
- **AC-4.3**: 검색 박스에서 특보 유형·지역·날짜 범위 필터링 가능
- **AC-4.4**: 저장된 보고서 테이블에 다음 정보 표시:
  - 생성 시각, 특보 유형, 영향 지역, 영향학교 수, 저장 상태
- **AC-4.5**: 테이블 행 클릭 → §3에 해당 보고서 재표시
- **AC-4.6**: 특보 유형 조회 시 자동으로 이전 3건 사례 추천 (Recent 상단)
- **AC-4.7**: 보고서 저장/로드 시간 ≤ 1초
- **AC-4.8**: DB 파일은 `data/reports.db` 위치에 저장, 자동 백업 고려

### 의존성

F3 (보고서 생성)

### 우선순위

**P1** (고우선) — 운영 편의성 증대

### 구현 가이드

```python
# 백엔드: SQLite 관리
import sqlite3
from pathlib import Path

class ReportDB:
    def __init__(self, db_path='data/reports.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_schema()
    
    def _init_schema(self):
        """테이블 자동 생성"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_type TEXT NOT NULL,
                    alert_region TEXT NOT NULL,
                    schools_affected INTEGER NOT NULL,
                    draft_text TEXT NOT NULL,
                    source TEXT,  -- cli/sdk/template
                    draft_time_sec REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alert_type_ts 
                ON reports(alert_type, ts DESC)
            """)
            conn.commit()
    
    def save(self, alert_id, alert_type, alert_region, 
             schools_affected, draft_text, source, draft_time_sec):
        """보고서 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO reports 
                (id, alert_type, alert_region, schools_affected, 
                 draft_text, source, draft_time_sec)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (alert_id, alert_type, alert_region, schools_affected,
                  draft_text, source, draft_time_sec))
            conn.commit()
        return alert_id
    
    def list(self, query=None, alert_type=None, date_from=None, date_to=None):
        """보고서 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            sql = "SELECT * FROM reports WHERE 1=1"
            params = []
            
            if alert_type:
                sql += " AND alert_type = ?"
                params.append(alert_type)
            
            if date_from:
                sql += " AND ts >= ?"
                params.append(date_from)
            
            if date_to:
                sql += " AND ts <= ?"
                params.append(date_to)
            
            sql += " ORDER BY ts DESC"
            
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_similar(self, alert_type, limit=3):
        """유사 사례 추천"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM reports 
                WHERE alert_type = ? 
                ORDER BY ts DESC 
                LIMIT ?
            """, (alert_type, limit))
            return [dict(row) for row in cursor.fetchall()]
```

---

## F5. 통계 대시보드 (신규)

### 목적

P3 교육행정 정책 수립자가 광역 수준의 특보 처리 통계를 조회하고, 시도별·시간대별 트렌드를 분석하여 정책 입안에 근거를 제공한다.

### 입력 및 출력

| 항목 | 내용 |
|---|---|
| **입력** | 기간 선택 (최근 7일/30일/전체) |
| **출력** | 4종 Chart.js 차트 |
| **API** | `GET /api/stats/summary?period=7d\|30d\|all` |

### 인수기준 (Acceptance Criteria)

- **AC-5.1**: 기간 선택 드롭다운 (최근 7일 / 30일 / 전체)
- **AC-5.2**: 차트 1 — 기간별 처리량
  - X축: 날짜 (일/주/월)
  - Y축: 보고서 생성 건수
  - 유형: 라인 차트 또는 바 차트
- **AC-5.3**: 차트 2 — 시도별 영향학교 히트맵
  - 17개 시도를 행으로, 영향학교 수를 색상으로 표현
  - 유형: 히트맵 또는 막대 차트
- **AC-5.4**: 차트 3 — AI 출처 분포
  - cli / sdk / template 비율
  - 유형: 도넛 차트
  - 범례에 건수 표시
- **AC-5.5**: 차트 4 — 처리시간 분포
  - P50, P95, 최대값 표시
  - 유형: 박스플롯 또는 바 차트
- **AC-5.6**: 마우스 호버 시 상세값 표시
- **AC-5.7**: 시도별 드릴다운 기능 (선택사항)
- **AC-5.8**: 차트 로딩 시간 ≤ 2초
- **AC-5.9**: 데이터 부족 시 "통계 데이터가 충분하지 않습니다" 메시지

### 의존성

F4 (저장된 데이터 필요)

### 우선순위

**P1** (고우선) — 정책 수립 근거 제공

### 구현 가이드

```python
# 백엔드: 통계 계산
def get_stats_summary(period='7d'):
    """통계 요약 API"""
    db = ReportDB()
    
    # 기간 계산
    if period == '7d':
        date_from = datetime.now() - timedelta(days=7)
    elif period == '30d':
        date_from = datetime.now() - timedelta(days=30)
    else:
        date_from = None
    
    # 데이터 로드
    reports = db.list(date_from=date_from)
    
    if not reports:
        return {
            'daily': [],
            'by_region': [],
            'by_source': {'cli': 0, 'sdk': 0, 'template': 0},
            'processing_time': {'p50': 0, 'p95': 0, 'max': 0}
        }
    
    # 1. 기간별 처리량
    daily_counts = defaultdict(int)
    for report in reports:
        date = report['ts'].split('T')[0]
        daily_counts[date] += 1
    
    daily = [
        {'date': d, 'count': c}
        for d, c in sorted(daily_counts.items())
    ]
    
    # 2. 시도별 영향학교
    region_schools = defaultdict(int)
    for report in reports:
        region = report['alert_region']
        region_schools[region] += report['schools_affected']
    
    by_region = [
        {'region': r, 'schools': s}
        for r, s in sorted(region_schools.items())
    ]
    
    # 3. 출처 분포
    by_source = {'cli': 0, 'sdk': 0, 'template': 0}
    for report in reports:
        source = report['source'] or 'template'
        by_source[source] += 1
    
    # 4. 처리시간 분포
    times = [r['draft_time_sec'] for r in reports if r['draft_time_sec']]
    times.sort()
    
    processing_time = {
        'p50': times[len(times)//2] if times else 0,
        'p95': times[int(len(times)*0.95)] if times else 0,
        'max': max(times) if times else 0
    }
    
    return {
        'daily': daily,
        'by_region': by_region,
        'by_source': by_source,
        'processing_time': processing_time
    }
```

```javascript
// 프론트엔드: Chart.js 렌더링
async function renderDashboard() {
  const period = document.getElementById('period-select').value; // '7d'
  const response = await fetch(`/api/stats/summary?period=${period}`);
  const data = await response.json();
  
  // 차트 1: 기간별 처리량
  const ctx1 = document.getElementById('chart-daily').getContext('2d');
  new Chart(ctx1, {
    type: 'line',
    data: {
      labels: data.daily.map(d => d.date),
      datasets: [{
        label: '보고서 생성 건수',
        data: data.daily.map(d => d.count),
        borderColor: '#3b82f6',
        fill: false
      }]
    }
  });
  
  // 차트 2: 시도별 영향학교
  const ctx2 = document.getElementById('chart-region').getContext('2d');
  new Chart(ctx2, {
    type: 'bar',
    data: {
      labels: data.by_region.map(r => r.region),
      datasets: [{
        label: '영향학교 수',
        data: data.by_region.map(r => r.schools),
        backgroundColor: '#8b5cf6'
      }]
    }
  });
  
  // 차트 3: 출처 분포
  const ctx3 = document.getElementById('chart-source').getContext('2d');
  new Chart(ctx3, {
    type: 'doughnut',
    data: {
      labels: ['CLI', 'SDK', 'Template'],
      datasets: [{
        data: [
          data.by_source.cli,
          data.by_source.sdk,
          data.by_source.template
        ],
        backgroundColor: ['#10b981', '#f59e0b', '#ef4444']
      }]
    }
  });
  
  // 차트 4: 처리시간 분포
  const ctx4 = document.getElementById('chart-time').getContext('2d');
  new Chart(ctx4, {
    type: 'bar',
    data: {
      labels: ['P50', 'P95', '최대'],
      datasets: [{
        label: '처리시간 (초)',
        data: [
          data.processing_time.p50,
          data.processing_time.p95,
          data.processing_time.max
        ],
        backgroundColor: '#06b6d4'
      }]
    }
  });
}
```

---

## 기능 우선순위 및 의존성 그래프

```
F1 (학교 정보)     [필수, 독립]
  ↓
F2 (특보 매칭)     [필수, F1 의존]
  ↓
F3 (AI 보고서)     [필수, F2 의존]
  ↓
F4 (저장·검색)     [고우선, F3 의존]
  ↓
F5 (통계)          [고우선, F4 의존]
```

---

## 기능 구현 체크리스트

### F1 체크리스트
- [ ] Leaflet 맵 렌더링
- [ ] 시도 다중선택 필터
- [ ] 학교급 체크박스 필터
- [ ] 마커 클러스터링 (12K)
- [ ] 팝업 UI
- [ ] D-lite 카메라 애니메이션
- [ ] 응답 시간 측정 (≤ 2초)

### F2 체크리스트
- [ ] 특보 카드 UI
- [ ] region 기반 매칭 알고리즘
- [ ] 위험도 점수 계산
- [ ] 17개 시도 region명 검증
- [ ] 매칭 결과 테이블
- [ ] 마커 강조 (붉은 테두리)
- [ ] 매칭 로깅 (benchmark.jsonl)

### F3 체크리스트
- [ ] Claude SDK 통합
- [ ] CLI 모드 fallback
- [ ] Template fallback
- [ ] Disclaimer 고정 표시
- [ ] source 필드 기록
- [ ] 처리 시간 측정 (P95 ≤ 30초)
- [ ] 보고서 테이블 렌더링

### F4 체크리스트
- [ ] SQLite 스키마 설계
- [ ] 저장 API 구현
- [ ] 검색 API 구현 (다중 필터)
- [ ] 유사 사례 추천
- [ ] 테이블 UI
- [ ] 행 클릭 → §3 재표시
- [ ] DB 자동 백업

### F5 체크리스트
- [ ] 기간 선택 드롭다운
- [ ] 4종 차트 렌더링 (Chart.js)
- [ ] 호버 인터랙션
- [ ] 색상 스키마 (다크 모드)
- [ ] 로딩 상태 표시
- [ ] 데이터 부족 메시지
- [ ] 성능 측정 (≤ 2초 로딩)

---

## 부록 A: v1.2 신규 기능 (Eros Cycle 1+2 결과)

### F6. 자연어 Q&A (RAG)

**목적**: 자연어로 시스템 데이터에 질의 ("울산 호우 취약 학교는?")

**입력/출력**: 사용자 텍스트 → Claude SDK 응답 + 인용 출처

**인수기준**:
- AC-6.1: 시스템 프롬프트에 학교 목록·매뉴얼·활성 특보 컨텍스트 주입 (Claude 200K)
- AC-6.2: 응답 P95 ≤ 10초 *(가설)*
- AC-6.3: 시연 안전 — 사전 큐레이션 질문 5~7개 fallback 유지
- AC-6.4: §6 채팅창 UI

**우선순위**: P1 (D6 작업)

---

### F7. UI 알림 카드 (push 시뮬레이션)

**목적**: 메인 상단에 활성 특보 즉시 표시 — Eros Cycle 2 push 결핍 대응

**인수기준**:
- AC-7.1: 페이지 로드 시 즉시 fetch + 표시 (≤ 200ms)
- AC-7.2: 클릭 → §2 특보 모니터링으로 스크롤
- AC-7.3: 0건이면 배너 숨김
- AC-7.4: 다크모드 + 색맹 대응

**우선순위**: P0 (D4 작업, 가장 싸고 임팩트 큼)

---

### F2 강화: 위험도 풀 산정 (RiskEngine plug-in)

**Phase A 신호** (D-7 안 구현):
- 학교급 가중치 (초/중/고)
- 설립일자 (노후 위험 ↑)
- 특보 강도 (주의보/경보)

**Phase B 신호** (외부 데이터 발견 시 또는 v2):
- 지형, 인접 학교 패턴, 시간대

**인터페이스 (E1 plug-in)**:
```python
class RiskEngine(Protocol):
    def score(self, school: dict, alert: dict) -> dict:
        """위험도 0~100 + 산정 근거 반환"""
```

**인수기준**:
- AC-2.1 강화: Phase A 3신호 반영, 0~100 정규화
- AC-2.2 신규: 산정 근거(신호별 기여도) 응답 포함
- AC-2.3 신규: plug-in 교체로 Phase B 도입 가능

---

### 학부모 검색 박스 (메인 §1 상단)

P4 페르소나 진입 동선. 학교명 입력 → 위험 아이콘 표시.

---

**문서 버전**: v1.2 (Eros Cycle 1+2 반영)
**생성일**: 2026-05-10
**v1.2 추가일**: 2026-05-10

---

## 부록 B: v1.3 신규 기능 (근본 사이트 niaeee/safety 이식)

### 데이터 범위 전략
- **울산 246개교**: 학사일정·기본정보·대피소·CCTV 풀 데이터 (이식)
- **전국 12,011개교**: 위치만 (기존)
- **v2**: 전국 풍부 확대

---

### F8. 안전문자/특보 → 반경 학교 검색

**목적**: 시청 안전문자(예: "울산 남구 화재") → 좌표 → 반경 N km 학교 자동 검색

**입력**: 안전문자 텍스트 또는 좌표(lat,lng) + 반경(km, 사용자 설정)

**출력**: 반경 내 학교 목록 + 각 학교 위험도/학사일정/기본정보 동시 표시

**인수기준**:
- AC-8.1: `services/geocoder.py` 이식 (주소→좌표 변환, 카카오/VWorld API)
- AC-8.2: 반경 km 슬라이더 (1~30km, 기본 5km)
- AC-8.3: 기존 `/api/schools/near` 활용
- AC-8.4: 안전문자 텍스트 파싱 (지명 추출 → 좌표) — Claude 보조

**우선순위**: P0 (근본 사이트 핵심 기능)

---

### F9. 학사일정 (방학·개학 여부)

**목적**: 영향학교가 현재 방학 중인지 개학 중인지 표시 → AI 보고서 영향도 산정에 반영

**입력**: 학교 ID + 현재 날짜

**출력**: `{status: "방학중|개학중|시험기간", until: "YYYY-MM-DD"}`

**인수기준**:
- AC-9.1: `data/school_schedules.json` 이식 (울산 246개교)
- AC-9.2: `services/school_data.py`에 `get_schedule(school_id, date)` 추가
- AC-9.3: AI 보고서에 "현재 방학 중이라 직접 영향 ↓" 같은 컨텍스트 명시
- AC-9.4: 위험도 산정에 가중치 (방학 중이면 위험도 −20%)

**우선순위**: P0

---

### F10. 학교 기본정보 (학생수·교직원수·규모)

**목적**: 학교 마커 클릭 시 학생수·교직원수·건물수 등 상세정보 표시

**입력**: 학교 ID

**출력**: `{students: 850, teachers: 60, buildings: 5, area_m2: 12000, …}`

**인수기준**:
- AC-10.1: `data/학교기본정보(*).json` 5종(초·중·고·각·특) 이식
- AC-10.2: `school_data.py`에 `get_basic_info(school_id)` 추가
- AC-10.3: 마커 팝업에 "학생수 850명 (큰 학교)" 표시
- AC-10.4: 위험도 산정에 가중치 (학생수 ↑ → 위험도 ↑)

**우선순위**: P0

---

### F11. 인근 대피소 마커·목록

**목적**: 학교 주변 대피소를 지도에 표시 + 영향학교 보고서에 첨부

**입력**: 학교 좌표 + 반경 km

**출력**: 대피소 목록 [{name, lat, lng, capacity, type}]

**인수기준**:
- AC-11.1: `services/shelters.py` + `blueprints/shelters_bp.py` 이식
- AC-11.2: `data/ulsan_shelters_fallback.json` 데이터 이식
- AC-11.3: 학교 마커 클릭 시 인근 대피소 5개 자동 표시
- AC-11.4: AI 보고서 컨텍스트로 "인근 대피소 N곳" 인용

**우선순위**: P1

---

### F12. 인근 CCTV 마커

**목적**: 학교 주변 CCTV 위치 지도 표시 → 시각적 모니터링 가능성 노출

**인수기준**:
- AC-12.1: `services/cctv.py` 이식
- AC-12.2: 마커 색상·아이콘 차별화 (대피소·학교와 구분)
- AC-12.3: 클릭 시 CCTV ID·관할 정보 팝업

**우선순위**: P1

---

### F13. 보고서/지도 공유 링크

**목적**: 보고서·지도 상태를 URL로 공유 → 팀장·학부모에게 카톡/SMS 전송

**인수기준**:
- AC-13.1: `services/share_store.py` 이식 (Redis 또는 SQLite)
- AC-13.2: `share.html` 이식 (공유 받는 화면)
- AC-13.3: 보고서 우상단에 "공유 링크 복사" 버튼
- AC-13.4: 링크는 7일 유효

**우선순위**: **Stretch** *(코덱스 검토 반영, 2026-05-10)*
**사유**: Redis/파일 영속성·공유 URL 보안 검토가 D-7 핵심 시연 범위를 잠식함. P0 완료 후에 추가 검토.

---

### F14. 프리셋 시나리오 (모의 안전문자)

**목적**: 시연 시 KMA 대신 미리 등록된 시나리오로 "호우주의보 강원" 같은 상황 재현

**인수기준**:
- AC-14.1: `data/presets.json` 이식
- AC-14.2: 메인 §2 상단에 "프리셋 선택" 드롭다운
- AC-14.3: 시연 안정성 100% (KMA API 장애에도 시연 가능)

**우선순위**: P2 (시연 안전 강화)

---

### F15. 재난담당팀장 보고 라인

**목적**: AI 보고서 생성 후 자동으로 재난담당팀장에게 전달 (현재는 모킹, v2 실 연동)

**인수기준**:
- AC-15.1: 시도별 재난담당팀장 모킹 데이터 (`data/report_lines.json` 신규)
- AC-15.2: 보고서 화면에 "팀장 [이름]에게 전송" 버튼 (실 전송 X, 시뮬레이션)
- AC-15.3: F13 공유 링크 활용 → 모킹 메시지에 URL 첨부
- AC-15.4: v2에 카카오톡 알림톡·이메일 실 연동 명시

**우선순위**: P2

---

**문서 버전**: v1.3 (근본 사이트 이식 8개 기능 추가)
**v1.3 추가일**: 2026-05-10
