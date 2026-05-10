# 코딩 컨벤션 및 개발 표준

safety-nation 프로젝트의 일관된 개발 규칙

---

## 1. Python 코드 스타일

### 1.1 기본 규칙

| 항목 | 규칙 |
|---|---|
| **들여쓰기** | 4 스페이스 (탭 금지) |
| **라인 길이** | 최대 100자 |
| **인코딩** | UTF-8 |
| **라인 끝** | LF (`\n`) |

### 1.2 모듈 상단 구조

```python
# -*- coding: utf-8 -*-
"""app.py: Flask 메인 애플리케이션 진입점"""

from __future__ import annotations

import logging
from pathlib import Path

import flask

logger = logging.getLogger(__name__)
```

### 1.3 타입 힌트 (권장: Python 3.10+)

```python
def match_schools(
    alert_region: str,
    schools: list[dict[str, str]],
    weights: dict[str, float] | None = None
) -> list[dict[str, str | float]]:
    """특보 지역으로 학교를 매칭한다."""
    pass
```

**규칙:**
- `Optional[X]` 대신 `X | None` 사용
- 함수 리턴 타입 항상 명시

### 1.4 함수/클래스 Docstring (한국어, 짧게)

```python
def get_schools_near(lat: float, lng: float, km: float = 5) -> list[dict]:
    """반경 내 학교 목록을 반환한다."""
    pass

class ReportDB:
    """보고서 SQLite 관리 클래스."""
    pass
```

### 1.5 경로 처리 (pathlib 권장)

```python
from pathlib import Path

# Good
db_path = Path("data/reports.db")
db_path.parent.mkdir(exist_ok=True)

# Bad (금지)
import os
db_path = os.path.join("data", "reports.db")
```

### 1.6 데이터클래스

```python
from dataclasses import dataclass

@dataclass
class Report:
    """보고서 데이터."""
    id: str
    ts: str
    alert_type: str
    draft_text: str
```

### 1.7 상수 정의

```python
DEFAULT_MAP_ZOOM = 7
RISK_WEIGHTS = {"초등학교": 1.0, "중학교": 0.8}
AI_TIMEOUT_SEC = 60
```

**규칙:** 모두 대문자 (UPPER_SNAKE_CASE)

### 1.8 금지 사항

| 항목 | 금지 | 대안 |
|---|---|---|
| **print 디버그** | `print("x:", x)` 잔존 | 로깅 사용 |
| **비밀값** | `API_KEY = "sk-..."` 하드코딩 | 환경변수 |
| **와일드카드** | `from module import *` | `from module import Func` |
| **except 침묵** | `except: pass` | `except Error as e: logger.error(...)` |

---

## 2. JavaScript 코드 스타일

### 2.1 기본 규칙

| 항목 | 규칙 |
|---|---|
| **들여쓰기** | 2 스페이스 |
| **변수 선언** | `const`/`let`만 (var 금지) |
| **따옴표** | 싱글 `'` 권장 |
| **비교** | `===` / `!==` (== 금지) |

### 2.2 변수 선언

```javascript
// Good
const schools = [];  // 재할당 없음
let count = 0;       // 재할당 필요

// Bad
var schools = [];    // var 금지!
```

### 2.3 화살표 함수

```javascript
// Good
const filterSchools = (schools, region) => {
  return schools.filter(s => s.region === region);
};

// Bad
function filterSchools(schools, region) {
  return schools.filter(function(s) {
    return s.region === region;
  });
}
```

### 2.4 비동기 (async/await 권장)

```javascript
// Good
async function fetchSchools() {
  try {
    const response = await fetch('/api/schools/map');
    const data = await response.json();
    return data.schools;
  } catch (error) {
    console.error('Failed:', error);
    return [];
  }
}

// Bad (then 연쇄)
fetch('/api/schools/map')
  .then(r => r.json())
  .then(data => { /* ... */ })
  .catch(err => { /* ... */ });
```

### 2.5 AbortController (타임아웃)

```javascript
const fetchWithTimeout = async (url, timeout = 30000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, { signal: controller.signal });
    return response.json();
  } finally {
    clearTimeout(timeoutId);
  }
};
```

### 2.6 배열/객체 처리

```javascript
// Good
const doubled = numbers.map(n => n * 2);
const filtered = schools.filter(s => s.level === '초등');
const found = schools.find(s => s.id === 'S001');

// 스프레드 연산자
const all = [...group1, ...group2];
const updated = { ...school, risk_score: 1.0 };
```

### 2.7 주석 (한국어)

```javascript
// 한국어 주석
const cluster = L.markerClusterGroup({
  maxClusterRadius: 80
});

/* 여러 줄 주석
 * 특보 발령 시 영향학교를
 * 빠르게 식별하는 로직 */
```

### 2.8 금지 사항

| 항목 | 금지 |
|---|---|
| **var** | `var x = 1;` |
| **console.log** | 배포 코드에 잔존 |
| **==** | `x == 5` (=== 사용) |
| **비타입 강제** | `!0 + 1` (명시적 형변환) |

---

## 3. HTML / CSS

### 3.1 HTML 구조

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>safety-nation</title>
</head>
<body>
  <!-- 콘텐츠 -->
</body>
</html>
```

### 3.2 들여쓰기 (2 스페이스)

```html
<div class="container">
  <section id="map-section">
    <h2>학교 분포 맵</h2>
  </section>
</div>
```

### 3.3 속성 순서

```html
<!-- id → class → style → 기타 -->
<div id="header" class="sticky-header" style="background: #0b1020;">
  <!-- ... -->
</div>
```

### 3.4 CSS: 다크 모드 기본

```css
body {
  background-color: #0b1020;
  color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
}

/* prefers-reduced-motion 감지 */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

**규칙:**
- 배경: #0b1020
- 텍스트: #fff
- Tailwind 미사용 (인라인 style 또는 `<style>`)
- prefers-reduced-motion 항상 지원

---

## 4. 파일명 및 폴더 구조

### 4.1 명명 규칙

| 유형 | 규칙 | 예시 |
|---|---|---|
| **Python 파일** | snake_case | `build_school_data.py` |
| **Python 함수** | snake_case | `def match_schools()` |
| **Python 클래스** | PascalCase | `class ReportDB` |
| **JS 파일** | kebab-case | `alert-handler.js` |
| **JS 함수** | camelCase | `filterSchools()` |
| **마크다운** | kebab-case | `01-prd.md`, `06-screens.md` |
| **환경변수** | UPPER_SNAKE | `ANTHROPIC_API_KEY` |
| **HTML ID** | kebab-case | `id="alerts-container"` |
| **CSS 클래스** | kebab-case | `class="btn-primary"` |

### 4.2 폴더 구조

```
safety-nation/
├── app.py                # Flask 메인
├── requirements.txt      # Python 의존성
├── Procfile             # Railway 배포
├── runtime.txt          # Python 3.12.7
├── app/
│   ├── routes.py        # 라우트
│   ├── services/        # 비즈니스 로직
│   └── utils/           # 유틸리티
├── static/
│   ├── index.html       # 단일 페이지
│   ├── style.css        # (선택) CSS
│   └── script.js        # (선택) JS
├── data/
│   ├── schools.json
│   ├── reports.db       # SQLite
│   └── processed/
├── logs/
│   ├── benchmark.jsonl
│   └── app.log
├── scripts/
│   ├── build_school_data.py
│   └── check_identifiers.py
├── tests/
│   ├── conftest.py
│   ├── test_schools.py
│   └── test_*.py
└── docs/planning/
    ├── 01-prd.md
    ├── 02-features.md
    ├── 03-personas.md
    ├── 04-user-stories.md
    ├── 05-tech-stack.md
    ├── 06-screens.md
    └── 07-coding-convention.md
```

---

## 5. 환경변수 명명

| 변수명 | 유형 | 기본값 | 필수 |
|---|---|---|---|
| `FLASK_ENV` | `production` \| `development` | `production` | ✅ |
| `SECRET_KEY` | 32B 문자열 | (없음) | ✅ (운영) |
| `DEMO_MODE` | `true` \| `false` | `true` | - |
| `ANTHROPIC_API_KEY` | 토큰 | (없음) | - (SDK 모드) |
| `MAP_PROVIDER` | `vworld` \| `osm` | `vworld` | - |
| `LOG_LEVEL` | DEBUG \| INFO \| WARNING | `INFO` | - |

**규칙:** 모두 대문자 (UPPER_SNAKE_CASE), 단어는 언더스코어

---

## 6. Git 커밋 메시지

### 6.1 형식

```
feat(scope): 한국어 요약

상세 설명 (필요시)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### 6.2 타입 정의

| 타입 | 설명 | 예시 |
|---|---|---|
| `feat` | 새 기능 | `feat(api): 특보 매칭 엔드포인트` |
| `fix` | 버그 수정 | `fix(db): SQLite 타임아웃` |
| `refactor` | 리팩토링 | `refactor(services): 모듈 분리` |
| `test` | 테스트 추가 | `test(matching): region 매칭 단위 테스트` |
| `docs` | 문서 수정 | `docs: 환경변수 명시` |
| `chore` | 빌드/배포 | `chore: requirements.txt 업데이트` |

### 6.3 Scope (예시)

`api`, `db`, `service`, `front`, `map`, `ai`, `test`, `docs`

### 6.4 예시

```bash
git commit -m "feat(api): 특보 매칭 엔드포인트 구현

- region 기반 학교 자동 식별
- 위험도 점수 계산

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## 7. 테스트 (pytest)

### 7.1 파일 위치

```
tests/
├── conftest.py           # 공용 설정
├── test_schools.py       # F1
├── test_alerts.py        # F2
├── test_reports.py       # F3/F4
└── test_stats.py         # F5
```

### 7.2 테스트 작성

```python
def test_match_schools_seoul(sample_schools):
    """서울 특보로 학교를 매칭하는 경우"""
    # Arrange
    alert_region = "서울특별시"
    
    # Act
    matched = match_schools(alert_region, sample_schools)
    
    # Assert
    assert len(matched) == 3
    assert all(s["region"] == alert_region for s in matched)
```

### 7.3 실행

```bash
pytest                           # 모든 테스트
pytest tests/test_schools.py     # 특정 파일
pytest -v                        # Verbose
pytest --cov=app                 # 커버리지
```

---

## 8. 금지 항목 및 안티패턴

### 8.1 Python 금지

| 금지 | 대안 |
|---|---|
| `from module import *` | `from module import ClassA, func_b` |
| `print("debug")` 잔존 | 로깅 사용 |
| `API_KEY = "sk-..."` 하드코딩 | 환경변수 |
| `def func(lst=[]):` | `def func(lst=None):` |

### 8.2 JavaScript 금지

| 금지 | 대안 |
|---|---|
| `var x = 1;` | `const x = 1;` |
| `.then().then().then()` | `async/await` |
| `x == 5` | `x === 5` |
| `console.log` 배포 코드 | 제거 또는 로거 |

### 8.3 데이터 금지

| 금지 | 이유 |
|---|---|
| 데모에 실명 | 식별정보 검증 필수 |
| 실주소 | 비식별 원칙 |
| 실 전화번호 | 개인정보보호 |

---

## 9. 코드 리뷰 체크리스트

PR 전 확인:

- [ ] 스타일 규칙 준수 (들여쓰기, 명명 등)
- [ ] 타입 힌트 추가 (Python)
- [ ] Docstring 작성 (한국어)
- [ ] 테스트 작성 및 통과
- [ ] 환경변수 설정 (.env.example 업데이트)
- [ ] 마크다운 문서 업데이트
- [ ] 식별정보 검증 (check_identifiers.py)

---

## 10. 개발 워크플로우

1. **기획**: 01-prd.md ~ 06-screens.md 검토
2. **테스트 작성** (TDD): test_*.py 작성
3. **구현**: 기능 코드 작성
4. **검증**: pytest 통과
5. **커밋**: 메시지 형식 준수
6. **배포**: Railway 자동 배포

---

**문서 버전**: v1.0  
**생성일**: 2026-05-10  

**이 컨벤션은 프로젝트 진행 중 지속적으로 개선됩니다.**
