# 2일차 프로젝트 정본 사양

> 1일차의 `docs/day1-workflow-spec.md`와 같은 역할을 한다. 2일차 네 프로젝트의 값에 대한
> 유일한 출처는 이 문서와 `public/downloads/day2-p1.json` ~ `day2-p4.json`이다.

원본 워크플로우 네 개를 읽고 확정한 사항이다.

| 프로젝트 | 원본 워크플로우 이름 |
|---|---|
| P1 공문서 요약 서비스 | `공문서 요약 서비스` |
| P2 매일 아침 민원 브리핑 봇 | `[2일차] 프로젝트2 · 매일 아침 민원 브리핑 봇` |
| P3 AI 민원 자동 분류·답변 초안 | `[2일차] 프로젝트3 · AI 민원 자동 분류·답변 초안` |
| P4 날씨 알리미 | `날씨 알리미 (기상청 단기예보 → 텔레그램)` |

원본 인스턴스 주소·프로젝트 id·자격증명 id는 이 저장소에 적지 않는다.

---

## ⚠ 원본 워크플로우에 대한 경고 (강사 확인 필요)

**원본 `날씨 알리미` 워크플로우의 HTTP Request 노드에 공공데이터포털 인증키가 평문으로
박혀 있다.** 쿼리 파라미터 `serviceKey`의 값이다. 이 저장소에는 옮기지 않았고
`여기에_본인_서비스키` 자리표시자로 바꿨지만, **원본은 그대로 남아 있다.**

수업에서 이 워크플로우 화면을 캡처하거나 화면 공유하면 키가 그대로 노출된다. 캡처 전에
값을 지우거나 가려야 하고, 이미 노출된 적이 있다면 공공데이터포털에서 키를 재발급하는 편이
안전하다. 텔레그램 chat id(원본 P1·P4에 리터럴로 들어 있음)도 마찬가지다.

---

## 핵심 설계 결정

### 결정 A: P1의 AI는 OpenAI가 아니라 Gemini로 바꾼다

원본 `공문서 요약 서비스`는 **AI Agent 노드 + OpenAI `gpt-4.1-mini`** 조합이다. 이 강좌는
준비물로 무료 Gemini API 키만 요구했으므로 그대로 쓸 수 없다.

1일차 06강에서 배운 **`Basic LLM Chain` + `Google Gemini Chat Model`** 조합을 그대로
재사용한다. 결과를 꺼내는 표현식도 06강과 같은 `{{ $json.text }}`다. 원본의
`{{ $node["AI Agent"].json["output"] }}` 표기는 쓰지 않는다.

### 결정 B: 폼의 파일 필드 이름은 `PDF` 하나로 짓는다

n8n 폼 트리거는 파일 필드의 **라벨을 그대로 바이너리 필드 이름으로 쓰되, 영문·숫자가 아닌
글자를 전부 `_`로 바꾼다.** 원본은 라벨이 `공문서 PDF 업로드`여서 바이너리 이름이
`____PDF____`(밑줄 네 개 + PDF + 밑줄 네 개)가 되어 있다. 수강생이 이 이름을 스스로
알아낼 방법이 없다.

라벨을 `PDF`로 지으면 바이너리 이름도 `PDF`가 되어 본문에 그대로 적어줄 수 있다.
`multipleFiles`는 `false`로 명시한다(기본값이 `true`라 여러 파일을 받게 되어 있다).

다만 이 이름 규칙은 n8n 버전에 따라 달라질 수 있는 종류의 것이므로, P1의 `안 될 때`에
**노드 왼쪽 INPUT 패널에서 실제 바이너리 이름을 확인해 그대로 복사하는 방법**을 넣는다.

### 결정 C: P2에 원본에 없는 `한 건으로 합치기`(Aggregate) 노드를 넣는다

**원본은 "여러 건 요약"을 하지 못한다.** 구글 시트 읽기는 행마다 항목을 하나씩 내보내므로,
민원이 20건 쌓여 있으면 AI 노드가 20번 돌고 브리핑 메일이 20통 발송된다. 프롬프트의
`{{ JSON.stringify($json) }}`도 그 한 행만 담는다.

`Aggregate` 노드(`aggregateAllItemData`, 결과 필드 `data`)로 전체 행을 한 항목에 모은 뒤
`{{ JSON.stringify($json.data) }}`로 넘긴다. 2일차 P2의 새 개념이 "여러 건 요약"이므로
이 노드가 곧 그 개념이다.

### 결정 D: P3에서 `$('노드 이름')` 문법을 도입한다

`AI 분류·답변` 노드를 지나면 `$json`은 `{ text: ... }`가 되어 민원 원문이 사라진다.
1일차 결정 1에서 다룬 바로 그 현상이다. 원본은 시트 매핑이 아예 비어 있어서 이 문제가
겉으로 드러나지 않았다.

시트에 민원 원문을 남기려면 폼 노드를 직접 지목해야 한다:

```
{{ $('민원 내용 입력').item.json.민원내용 }}
```

1일차에서 "이어 붙이면 값이 사라진다"고 배운 현상의 **해결책**이므로 여기서 가르치기 좋다.
P3의 새 개념은 이 문법 하나다.

### 결정 E: 텔레그램 메시지에 서식(`parse_mode`)을 쓰지 않는다

원본 P1·P4는 `parse_mode: Markdown`에 `*굵게*` 표기를 쓴다. 텔레그램의 구형 Markdown은
`*` · `_` · `[` 의 짝이 맞지 않으면 **메시지 발송 자체가 400 오류로 실패한다.** AI가 쓴
문장이나 공문서 제목에 이런 글자가 섞이는 일은 흔하다. 초보자는 "AI는 잘 돌았는데
텔레그램만 빨간색"인 상황의 원인을 찾을 수 없다.

서식을 쓰지 않으면 이 실패가 원천적으로 사라진다. `additionalFields`에는
`appendAttribution: false`만 켠다(메시지 끝에 붙는 n8n 홍보 문구 제거).

### 결정 F: P4의 지역·격자 설정은 `발표시각 계산` 한 곳에 모은다

원본은 격자 좌표(`nx`/`ny`)를 첫 Code 노드에, 지역 이름 문자열
(`인천 남동구 구월2동`)을 두 번째 Code 노드 안에 흩어놓았다. 수강생이 자기 동네로 바꾸려면
두 곳을 고쳐야 하고, 한쪽만 고치면 **엉뚱한 지역 이름이 붙은 옆동네 날씨**가 온다.

`REGION` · `NX` · `NY` 세 값을 첫 Code 노드 맨 위 한 블록에 모으고, 두 번째 Code 노드는
`$('발표시각 계산').first().json.region`으로 지역 이름을 가져온다.

### 결정 G: P4의 스케줄은 하루 한 번으로 단순화한다

원본은 cron `0 7 * * *`에 12시·18시·23시 규칙과 빈 규칙 `{}`까지 다섯 개가 겹쳐 있다.
강의에서는 `Trigger at Hour = 7` 하나만 쓴다.

### 결정 H: 원본의 발표시각 계산 버그를 고친다

원본 코드는 자정 직후(KST 00:00~00:09)에 **오늘 날짜 + 23시 발표분**을 요청한다. 아직
발표되지 않은 회차라 API가 빈 응답을 준다. 현재 시각에서 10분을 뺄 때 날짜를 함께
넘기지 않아서 생기는 문제다. 정본 코드는 10분을 빼면서 날짜도 같이 전날로 넘긴다.

### 결정 I: 시트는 1일차에서 만든 것을 그대로 쓴다

- **P2**: 1일차 03강부터 민원이 쌓인 그 시트의 `시트1` 탭을 **읽는다.** 머리글 6개
  (`이름`·`연락처`·`이메일`·`종류`·`상세설명`·`등록일`)가 그대로 쓰인다.
- **P3**: 같은 스프레드시트에 `분류결과` 탭을 새로 만들고 머리글 3개
  (`민원내용`·`AI분류결과`·`접수일시`)를 넣는다. 새 스프레드시트를 만들지 않는다.

---

## 프로젝트별 정본 사양

### P1 — 공문서 요약 서비스

| 노드 | type | typeVersion | position |
|---|---|---|---|
| 공문서 업로드 폼 | `n8n-nodes-base.formTrigger` | 2.5 | `[0, 0]` |
| PDF 텍스트 추출 | `n8n-nodes-base.extractFromFile` | 1.1 | `[220, 0]` |
| AI 요약 | `@n8n/n8n-nodes-langchain.chainLlm` | 1.9 | `[440, 0]` |
| Google Gemini Chat Model | `@n8n/n8n-nodes-langchain.lmChatGoogleGemini` | 1 | `[380, 180]` |
| 텔레그램 발송 | `n8n-nodes-base.telegram` | 1.2 | `[660, 0]` |

- 폼: `formTitle` `공문서 요약 서비스`, `formDescription`
  `PDF 공문서를 올리면 AI가 핵심만 요약해 텔레그램으로 보내드립니다.`
  필드 1개 — 라벨 `PDF`, 타입 `file`, `acceptFileTypes` `.pdf`, `multipleFiles` `false`, 필수
- 텍스트 추출: `operation` `pdf`, `binaryPropertyName` `PDF`
- AI 요약 프롬프트(`promptType` `define`):
```
=다음 공문서를 5줄 이내로 핵심만 요약하세요.

- 목적
- 주요 내용
- 지원 사항
- 대상
- 일정

각 항목을 한 줄로 정리하세요.
불필요한 설명은 하지 마세요.

[문서 내용]
{{ $json.text }}
```
- 텔레그램: `chatId` 자리표시자, `text` `=📄 공문서 요약\n\n{{ $json.text }}`

연결: 폼 → 추출 → AI 요약 → 텔레그램, Gemini →(`ai_languageModel`) AI 요약

### P2 — 매일 아침 민원 브리핑 봇

| 노드 | type | typeVersion | position |
|---|---|---|---|
| 매일 아침 9시 | `n8n-nodes-base.scheduleTrigger` | 1.3 | `[0, 0]` |
| 민원 현황 읽기 | `n8n-nodes-base.googleSheets` | 4.7 | `[220, 0]` |
| 한 건으로 합치기 | `n8n-nodes-base.aggregate` | 1 | `[440, 0]` |
| AI 브리핑 작성 | `@n8n/n8n-nodes-langchain.chainLlm` | 1.9 | `[660, 0]` |
| Google Gemini Chat Model | `@n8n/n8n-nodes-langchain.lmChatGoogleGemini` | 1 | `[600, 180]` |
| 브리핑 메일 | `n8n-nodes-base.gmail` | 2.2 | `[880, -100]` |
| 텔레그램 알림 | `n8n-nodes-base.telegram` | 1.2 | `[880, 120]` |

- 스케줄: `rule.interval` `[{ "triggerAtHour": 9 }]`
- 시트 읽기: `documentId` 자리표시자, `sheetName` `시트1` (읽기가 기본 동작이라 `operation`을 적지 않는다)
- 합치기: `aggregate` `aggregateAllItemData`, `destinationFieldName` `data`
- AI 브리핑 프롬프트 끝: `[민원 목록]\n{{ JSON.stringify($json.data) }}`
- 메일: `sendTo` 자리표시자, `subject` `=[일일 민원 브리핑] {{ $now.toFormat('yyyy-MM-dd') }}`,
  `emailType` `text`, `message` `={{ $json.text }}`
- 텔레그램: `text` `=📋 일일 민원 브리핑\n\n{{ $json.text }}`

연결: 9시 → 읽기 → 합치기 → AI → (메일, 텔레그램), Gemini →(`ai_languageModel`) AI

### P3 — AI 민원 자동 분류·답변 초안

| 노드 | type | typeVersion | position |
|---|---|---|---|
| 민원 내용 입력 | `n8n-nodes-base.formTrigger` | 2.5 | `[0, 0]` |
| AI 분류·답변 | `@n8n/n8n-nodes-langchain.chainLlm` | 1.9 | `[220, 0]` |
| Google Gemini Chat Model | `@n8n/n8n-nodes-langchain.lmChatGoogleGemini` | 1 | `[160, 180]` |
| 분류 결과 기록 | `n8n-nodes-base.googleSheets` | 4.7 | `[440, 0]` |

- 폼: `formTitle` `민원 내용 입력`, `formDescription` `분류할 민원 내용을 입력하세요.`
  필드 1개 — 라벨 `민원내용`, 타입 `textarea`, 필수
- 시트 기록: `operation` `append`, `sheetName` `분류결과`, 매핑 3개
  - `민원내용` = `={{ $('민원 내용 입력').item.json.민원내용 }}`
  - `AI분류결과` = `={{ $json.text }}`
  - `접수일시` = `={{ $now.toFormat('yyyy-MM-dd HH:mm') }}`

연결: 폼 → AI → 시트, Gemini →(`ai_languageModel`) AI

### P4 — 날씨 알리미

| 노드 | type | typeVersion | position |
|---|---|---|---|
| 매일 아침 7시 | `n8n-nodes-base.scheduleTrigger` | 1.3 | `[0, 0]` |
| 발표시각 계산 | `n8n-nodes-base.code` | 2 | `[220, 0]` |
| 기상청 API 호출 | `n8n-nodes-base.httpRequest` | 4.2 | `[440, 0]` |
| 메시지 가공 | `n8n-nodes-base.code` | 2 | `[660, 0]` |
| 텔레그램 발송 | `n8n-nodes-base.telegram` | 1.2 | `[880, 0]` |

- HTTP: `url`
  `https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst`,
  `sendQuery` `true`, 쿼리 8개 — `serviceKey`(자리표시자) · `pageNo` `1` ·
  `numOfRows` `300` · `dataType` `JSON` · `base_date` · `base_time` · `nx` · `ny`
  (뒤 네 개는 `={{ $json.… }}` 표현식)
- 텔레그램: `text` `={{ $json.message }}`

연결: 7시 → 발표시각 계산 → API 호출 → 메시지 가공 → 텔레그램 (일직선)

---

## 자리표시자 (JSON에 실제로 들어간 값)

| 자리 | 자리표시자 | 들어 있는 파일 |
|---|---|---|
| 텔레그램 `chatId` | `여기에_본인_chat_id` | p1, p2, p4 |
| 구글 시트 `documentId` | `여기에_본인_시트_ID` | p2, p3 |
| Gmail `sendTo` | `본인이메일@example.com` | p2 |
| 공공데이터포털 `serviceKey` | `여기에_본인_서비스키` | p4 |

1일차와 같은 표기를 쓴다(`본인이메일@example.com`, `여기에_본인_시트_ID`). 텔레그램과
서비스키는 2일차에 처음 나오므로 같은 어법으로 새로 정했다.

---

## 노드 배치 규칙

1일차와 같다 — **어떤 두 노드도 x·y가 동시에 120 미만으로 가까워서는 안 된다.**

2일차는 전부 일직선이므로 x를 `220` 간격으로 늘어놓는다. 보조 노드(Gemini)는 부모보다
x를 60 줄이고 y를 180 내린다. P2만 끝에서 두 갈래로 갈라지며 y를 `-100` / `120`으로 벌린다.

---

## 노드 이름 목록 (전 자료 공통)

P1: `공문서 업로드 폼`, `PDF 텍스트 추출`, `AI 요약`, `Google Gemini Chat Model`, `텔레그램 발송`
P2: `매일 아침 9시`, `민원 현황 읽기`, `한 건으로 합치기`, `AI 브리핑 작성`,
`Google Gemini Chat Model`, `브리핑 메일`, `텔레그램 알림`
P3: `민원 내용 입력`, `AI 분류·답변`, `Google Gemini Chat Model`, `분류 결과 기록`
P4: `매일 아침 7시`, `발표시각 계산`, `기상청 API 호출`, `메시지 가공`, `텔레그램 발송`

이 이름들은 본문·다이어그램·JSON 세 곳에서 철자까지 완전히 같아야 한다. 특히 P3의
`$('민원 내용 입력')`과 P4의 `$('발표시각 계산')`은 이름이 한 글자만 달라도 실행이 실패한다.
