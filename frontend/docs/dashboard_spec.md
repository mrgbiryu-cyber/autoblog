# Dashboard Specification

## Folder / file overview

- `frontend/src/app/(user)/dashboard/page.tsx`  
  - 새로운 “AI Marketing Automation Engine” 대시보드 UI를 구성하며, 크레딧 상태, 플랫폼 카드, 지식 기반 입력, 스케줄링 설정, 키워드 트래킹 테이블, 실행 로그, HTML 미리보기 모달을 모두 포함합니다.
  - 상태 관리엔 `useState`/`useEffect`를 활용해 API 응답을 로드하고, 사용자 상호작용 이벤트(일정 저장, 미리보기, 복사 등)를 처리합니다.
  - Tailwind 기반 디자인으로 크레딧 영역, 플랫폼 통합, Free Trial 버튼, HTML 미리보기 복사 기능 등을 시각화합니다.

- `frontend/src/lib/api.ts`
  - `API_BASE_URL`을 기준으로 백엔드 엔드포인트들을 캡슐화한 헬퍼 함수 모음입니다.
  - `fetchCreditStatus`, `fetchScheduleConfig`, `saveScheduleConfig`, `fetchKeywordTracking`, `generatePreviewHtml` 함수가 UI와 연동됩니다.
  - 실패 시 구조화된 기본값을 반환하여 UI가 무중단으로 작동하도록 합니다.

- `frontend/docs/dashboard_spec.md`
  - 본 파일 스스로가 API 사양과 구조 설명을 보관하는 역할을 하며, 향후 “부자(AI 어시스턴트)”가 흐름을 검토할 때 참조용으로 사용됩니다.

## API contract for dashboard

### 1. Credit Status
- **Endpoint**: `GET /api/v1/credits/status`
- **Purpose**: 상단 Credit 배너에 표시할 보유 크레딧과 다음 차감 예정액을 가져옵니다.
- **Headers**: `Content-Type: application/json`, optional `Authorization: Bearer <token>`
- **Response**:
  ```json
  {
    "current_credit": 42,
    "upcoming_deduction": 6,
    "currency": "KRW"
  }
  ```

### 2. Schedule configuration
- **Endpoint**: `GET /api/v1/schedule`
- **Purpose**: 플랫폼별 자동 발행 스케줄(주기, 게시물 수, 발행 요일/시간)을 초기값으로 로드합니다.
- **Response**:
  ```json
  {
    "frequency": "daily", // hourly | daily | weekly
    "posts_per_day": 2,
    "days": ["Mon","Wed","Fri"],
    "target_times": ["09:00","19:00"]
  }
  ```
- **Endpoint (save)**: `POST /api/v1/schedule`
- **Purpose**: 사용자가 입력한 스케줄을 저장합니다.
- **Request Body**: 동일한 구조의 JSON (`SchedulePayload`). 서버는 상태를 저장하고, 응답은 200 OK로 처리되면 UI가 알림 메시지를 띄웁니다.

### 3. Keyword tracker
- **Endpoint**: `GET /api/v1/posts/keywords`
- **Purpose**: 등록된 포스팅과 해당 키워드의 플랫폼별 노출 순위(랭킹, 변동, 업데이트 시간)를 가져옵니다.
- **Response**:
  ```json
  [
    {
      "keyword": "AI 마케팅 자동화",
      "platform": "Naver",
      "rank": 3,
      "change": 1,
      "updated_at": "2시간 전"
    },
    ...
  ]
  ```

### 4. Preview generation
- **Endpoint**: `POST /api/v1/posts/preview`
- **Purpose**: 사용자 입력(주제 + 페르소나 + 프롬프트)과 이미지, 글자수 조건을 전달하여 Gemini가 생성한 HTML과 요약, 예상 크레딧을 반환합니다.
- **Request Body**:
  ```json
  {
    "topic": "AI Marketing Automation",
    "persona": "Data-Driven Strategist",
    "image_count": 3,
    "word_count_range": [800, 1200],
    "custom_prompt": "SEO 중심으로 프롬프트 작성",
    "free_trial": true
  }
  ```
- **Response**:
  ```json
  {
    "html": "<h1>...</h1><p>...</p>",
    "summary": "SEO적으로 최적화된 서문",
    "credits_required": 8
  }
  ```

### 5. Blog analysis
- **Endpoint**: `POST /api/v1/blogs/analyze`
- **Purpose**: 사용자가 등록한 블로그(기본적으로 첫 번째 블로그)를 `gemini-2.5-flash`에 분석 요청하여 이상적인 카테고리 및 작성 지시 프롬프트를 받아옵니다.
- **Request Body**:
  ```json
  {
    "blog_id": 123
  }
  ```
- **Response**:
  ```json
  {
    "category": "AI Automation",
    "prompt": "Please craft an SEO intro..."
  }
  ```
- **Usage**: 결과를 대시보드에서 `topic`과 프롬프트에 자동 반영하고, 필요한 경우 사용자가 직접 수정하여 `Preview generation` API에 넘깁니다.

## Frontend integration notes

- UI는 `frontend/src/app/(user)/dashboard/page.tsx`에서 위 API들을 `frontend/src/lib/api.ts`로 추상화하여 호출합니다.
- Failover 케이스를 고려해, API 오류 시에도 기본 데이터(크레딧 42, 키워드 샘플, HTML 템플릿 등)를 보여줍니다.
- 미리보기/복사/프리뷰 모달, 스케줄 세이브 버튼, Free Trial 버튼은 모두 해당 API 함수의 성공/실패 여부에 따라 상태 메시지를 업데이트합니다.

## Next steps for review

1. 백엔드에서 위 API가 실제 구현되었는지 점검한 후, schema에 맞춰 응답을 조정합니다.
2. 추가로 Credential을 저장하는 `AuthService`와 `CreditLog` 모델이 연동되어 있는지 검토합니다.
3. 프론트엔드 테스트(예: `next test` 또는 유닛 테스트)에서 `api.ts` 함수를 mocking하여 결과를 시뮬레이트합니다.

