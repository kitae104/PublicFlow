# 1일차 강의 본문 8강 구현 계획 (2단계)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 1일차 8강의 본문(`#steps`·`#verify`·`#trouble`)을 실제로 동작하는 값으로 채우고, 각 강의 종료 시점의 누적 워크플로우 JSON 8개를 만들어 다운로드 가능하게 한다.

**Architecture:** 하나의 워크플로우가 매 강의 노드 하나씩 자란다. 단 **일직선이 아니라 `샘플 민원`에서 갈라지는 부챗살(fan-out)** 구조다. 이유는 아래 "핵심 설계 결정"에 있다. 각 강의 종료 시점을 그대로 export한 JSON을 `public/downloads/`에 두어, 수강생이 막히면 그 지점부터 이어서 진행할 수 있게 한다.

**Tech Stack:** 정적 HTML(1단계에서 확정된 템플릿), n8n 워크플로우 JSON, 검증은 `tools/check_site.py`와 n8n MCP의 `validate_workflow`.

---

## Global Constraints

- **작업 루트:** `D:\Github\n8n_WS\PublicFlow`
- **Python 실행은 반드시 `python`** — 이 머신의 `python3`은 Windows 스토어 스텁이라 코드를 실행하지 않고 문자열 `Python`만 출력한 뒤 exit 0을 반환한다. 검사가 통과한 것처럼 보이면서 실제로는 아무것도 검사하지 않는다.
- **배포 금지:** 이 계획의 어떤 단계도 Vercel 배포나 **n8n 인스턴스에 워크플로우 생성/수정**을 수행하지 않는다. JSON은 로컬 파일로만 만들고, 검증은 `validate_workflow`(로컬 JSON 검사, 인스턴스에 쓰지 않음)로 한다.
- **빌드 도구·외부 리소스 금지:** `public/`의 파일이 곧 배포물. CDN·웹폰트·외부 이미지·`<script>` 모두 금지.
- **Gemini 모델 문자열은 정확히 `models/gemini-2.5-flash`**, 대체는 `models/gemini-2.5-flash-lite`.
- **언어:** 사용자 노출 텍스트는 한국어. 파일명·식별자는 영문 소문자 케밥케이스.
- **강의 페이지 필수 섹션 id 7개** 유지: `goal`, `flow`, `why`, `steps`, `verify`, `trouble`, `download`.
- **1단계에서 확정된 클래스만 사용.** 새 CSS 컴포넌트를 만들지 않는다. 사용 가능: `.wrap` `.page-head` `.crumb` `.pager` `.sec` `.sec-title` `ol.steps>li` `.step-title` `.hint` `figure.capture` `.capture-cap` `.capture-guide` `.note` `.note.warn` `.note.tip` `code.val` `.flow` `.flow-node` `.is-new` `.is-dim` `.flow-arrow` `.flow-legend` `.flow-split`
- **`figure.capture`의 속성 순서 고정:** `<figure class="capture" id="fig-...">`. `tools/apply_captures.py`가 이 순서를 문자열로 찾는다.
- **캡처 자리표시자를 직접 채우지 않는다.** 새 그림이 필요하면 `figure.capture` 자리표시자를 추가하고 id를 `fig-d1-NN-N` 형식으로 페이지 내 연번으로 붙인다.
- **강사 개인정보 금지:** 아래 값들은 원본에 박혀 있으나 **강의 자료에 그대로 쓰면 안 된다.** 반드시 "본인 것으로 바꾸세요"로 처리한다.
  - 이메일 `aqua0405@gmail.com`
  - 구글 시트 문서 ID `1nMbi2VfMxQ2Bud1M7WjyZjyz6XASN2QyX0Mecc3TjXM` 및 그 URL
  - 캘린더 ID `aqua0405@gmail.com`
  - 이름 `김기태`는 예시 데이터이므로 **그대로 써도 된다**(가상의 민원인 역할).

---

## 핵심 설계 결정 — 구현 전 반드시 읽을 것

원본 워크플로우 8개를 읽고 확정한 사항이다. 전체 원본 조사 결과는 `.superpowers/sdd/day1-source-workflows.md`에 있다.

### 결정 1: 일직선이 아니라 부챗살(fan-out)

n8n에서 노드의 출력은 그 노드가 만든 결과다. Gmail 노드를 지나면 `$json`은 `{id, threadId, labelIds}` 같은 발송 결과가 되고, 원래 민원 데이터는 사라진다. 시트·캘린더·AI 노드도 마찬가지다.

따라서 `샘플 민원 → 시트 → 메일 → 캘린더 → AI → IF` 로 일직선 연결하면 두 번째 노드부터 `{{ $json.이름 }}`이 빈 값이 되고, 07강의 IF는 `$json.종류`를 찾지 못해 **항상 거짓으로 빠진다.** 초보자가 원인을 찾을 수 없는 종류의 고장이다.

원본 워크플로우들이 실제로 하는 방식이 정답이다 — **모든 액션 노드가 `샘플 민원` 하나에 각각 직접 연결된다.**

```
수동 실행 → 샘플 민원 ┬→ 시트에 기록
                      ├→ 접수 메일 보내기
                      ├→ 처리 마감 일정
                      ├→ AI 안내문 작성
                      └→ 생활인가? ┬(참)→ 생활 담당자
                                   └(거짓)→ 일반 담당자
```

이 구조의 이점:
- 원본의 표현식이 **한 글자도 고치지 않고** 그대로 동작한다
- 워크플로우는 여전히 매 강의 노드 하나씩 자란다(가지가 하나씩 늘어난다)
- 새 노드 강조 장치가 그대로 유효하다
- 한 노드가 실패해도 다른 가지는 영향받지 않는다 — 초보자에게 훨씬 관대하다

### 결정 2: 08강은 트리거와 데이터 노드를 함께 교체한다

폼 트리거의 입력 필드 이름이 `이름`·`연락처`·`이메일`·`종류`·`상세설명`으로 **`샘플 민원`의 필드명과 완전히 같다.** 따라서 08강은 `수동 실행`과 `샘플 민원`을 지우고 그 자리에 `민원 입력 폼` 하나를 꽂으면 끝난다. 하류 노드의 표현식은 전혀 손대지 않는다.

원본 08번에 있는 `입력 내용 정리`(disabled) 노드는 **쓰지 않는다.** 비활성 상태로 방치된 노드이고, 위 교체에 필요하지 않다.

### 결정 3: 시트 머리글을 하나로 통일

원본 03번은 안내 메모에 머리글을 `이름·연락처·이메일·종류·상세설명·접수일시`라고 적어놓고, 실제 컬럼 매핑은 `쓰레기종류`·`등록일`을 쓴다. 그대로 따라 하면 실습이 어긋난다.

**정본:** `이름` · `연락처` · `이메일` · `종류` · `상세설명` · `등록일`

시트 머리글과 노드 매핑 양쪽 모두 이 여섯 개로 쓴다. `쓰레기종류`는 쓰지 않는다(민원 종류가 쓰레기에 한정되지 않는다).

### 결정 4: 날짜 표현식은 `toFormat()`으로 통일

원본 03번은 `$now.format('yyyy-MM-dd')`, 04번은 `$now.toFormat('yyyy년 MM월 dd일 HH시 mm분')`을 쓴다. n8n의 `$now`는 Luxon DateTime이고 **Luxon의 포맷 메서드는 `toFormat()`**이다. 강의 전체에서 `toFormat()`만 가르친다.

- 03강 시트 `등록일`: `{{ $now.toFormat('yyyy-MM-dd') }}`
- 04강 메일 본문 등록일: `{{ $now.toFormat('yyyy년 MM월 dd일 HH시 mm분') }}`

### 결정 5: Gemini 모델은 강의에서 직접 지정한다

원본 06번의 Gemini 노드는 `parameters`가 `{"options": {}}` 뿐으로 **모델이 아예 지정되어 있지 않다.** 1단계 준비물 페이지에서 경고한 상황이 원본에서 실제로 벌어져 있다. 06강 본문은 모델 드롭다운을 열어 `models/gemini-2.5-flash`를 **직접 고르는 단계**를 반드시 포함한다.

### 결정 6: 07강 두 담당자 메일은 본인 주소로

원본의 `생활 담당자`/`일반 담당자` 두 Gmail 노드는 `aqua0405@gmail.com`으로 **리터럴 하드코딩**되어 있다. 실습에서는 수강생 본인 주소를 넣게 한다. 제목으로 어느 갈래를 탔는지 구분하는 것이 이 강의의 확인 방법이므로, 두 노드 모두 같은 주소여도 학습에 지장이 없다 — 오히려 한 받은편지함에서 결과를 비교할 수 있어 낫다. 이 점을 본문에 밝힌다.

---

## 강의별 정본 사양

각 강의 종료 시점의 워크플로우다. 값은 원본에서 가져오되 위 결정들을 반영했다.

### 01강 — 수동 실행 + 값 만들기

| 노드 | type | typeVersion |
|---|---|---|
| 수동 실행 | `n8n-nodes-base.manualTrigger` | 1 |
| 값 만들기 | `n8n-nodes-base.set` | 3.4 |

`값 만들기` 필드: `인사말`(string) = `안녕하세요, 홍길동님`
연결: `수동 실행` → `값 만들기`

### 02강 — + 값 가져오기

추가: `값 가져오기` (`n8n-nodes-base.set`, 3.4)
필드: `최종문구`(string) = `={{ $json.인사말 }} 반갑습니다.`
연결: `값 만들기` → `값 가져오기`

이 강의만 순수 누적이며, 앞 노드의 출력을 그대로 받는 유일한 구간이다. 여기서 `{{ }}` 문법을 가르친다.

### 03강 — 데이터 교체 + 시트에 기록

**삭제:** `값 만들기`, `값 가져오기`
**추가:** `샘플 민원` (`n8n-nodes-base.set`, 3.4), `시트에 기록` (`n8n-nodes-base.googleSheets`, 4.7)

`샘플 민원` 필드 5개 (모두 string):
- `이름` = `김기태`
- `연락처` = `010-1111-2222`
- `이메일` = **수강생 본인 이메일** (자료에는 `본인@example.com` 형태로 두고 바꾸라고 안내)
- `종류` = `생활`
- `상세설명` = `집 앞에 쓰레기가 무단 투기되어 있습니다.`

`시트에 기록`: operation `append`, documentId는 **수강생 본인 시트**, sheetName `시트1`, mappingMode `defineBelow`
- `이름` = `={{ $json.이름 }}`
- `연락처` = `={{ $json.연락처 }}`
- `이메일` = `={{ $json.이메일 }}`
- `종류` = `={{ $json.종류 }}`
- `상세설명` = `={{ $json.상세설명 }}`
- `등록일` = `={{ $now.toFormat('yyyy-MM-dd') }}`

연결: `수동 실행` → `샘플 민원` → `시트에 기록`

### 04강 — + 접수 메일 보내기

추가: `접수 메일 보내기` (`n8n-nodes-base.gmail`, 2.2)
- sendTo = `={{ $json.이메일 }}`
- subject = `민원 접수`
- emailType = `text`
- message (원본 그대로, 등록일만 `toFormat`):
```
=담당팀께,

아래와 같이 민원이 접수되었습니다.

- 접수자명: {{ $json.이름 }}
- 연락처: {{ $json.연락처 }}
- 이메일: {{ $json.이메일 }}
- 민원 종류: {{ $json.종류 }}
- 상세 설명: {{ $json.상세설명 }}
- 등록일: {{ $now.toFormat('yyyy년 MM월 dd일 HH시 mm분') }}

내용 확인 후 신속한 처리 바랍니다.

감사합니다.
```
연결: `샘플 민원` → `접수 메일 보내기` (**`시트에 기록`이 아니라 `샘플 민원`에서 갈라진다**)

### 05강 — + 처리 마감 일정

추가: `처리 마감 일정` (`n8n-nodes-base.googleCalendar`, 1.3)
- calendar = **수강생 본인 캘린더 ID**(보통 본인 Gmail 주소)
- start = `={{ $now.plus(3,'days').toISO() }}`
- end = `={{ $now.plus(3,'days').plus(1,'hour').toISO() }}`
- additionalFields.summary = `=민원 처리 마감 - {{ $json.이름 }}`

연결: `샘플 민원` → `처리 마감 일정`

### 06강 — + AI 안내문 작성 (노드 2개)

추가: `AI 안내문 작성` (`@n8n/n8n-nodes-langchain.chainLlm`, 1.9), `Google Gemini Chat Model` (`@n8n/n8n-nodes-langchain.lmChatGoogleGemini`, 1)

`AI 안내문 작성` promptType `define`, 프롬프트(원본 그대로):
```
=당신은 친절한 시청 민원 담당 공무원입니다.
아래 민원 접수 내용을 바탕으로, 민원인에게 보낼 정중한 '접수 확인 안내문'을 작성해 주세요.

[작성 규칙]
- 존댓말을 사용하고, 4~6문장으로 작성합니다.
- 민원이 정상적으로 접수되었음을 안내합니다.
- 처리에는 다소 시간이 걸릴 수 있음을 부드럽게 안내합니다.
- 마지막은 '감사합니다.'로 끝맺습니다.

[민원 접수 내용]
- 접수자명: {{ $json.이름 }}
- 민원 종류: {{ $json.종류 }}
- 상세 설명: {{ $json.상세설명 }}
```

`Google Gemini Chat Model`: `modelName` = `models/gemini-2.5-flash` (**원본에는 없다. 반드시 넣는다.**)

연결: `샘플 민원` → `AI 안내문 작성` (main), `Google Gemini Chat Model` → `AI 안내문 작성` (ai_languageModel)

결과는 `{{ $json.text }}`로 나온다.

### 07강 — + 조건 분기 (노드 3개)

추가: `생활인가?` (`n8n-nodes-base.if`, 2.3), `생활 담당자`·`일반 담당자` (둘 다 `n8n-nodes-base.gmail`, 2.2)

`생활인가?`: combinator `and`, typeValidation `strict`, caseSensitive `true`
- 조건: leftValue `={{ $json.종류 }}`, operator `string.equals`, rightValue `생활`

`생활 담당자` (참 = output 0): sendTo **본인 주소**, subject `[생활 관련] 민원`, message `=생활 관련 민원: {{ $json.이름 }}`
`일반 담당자` (거짓 = output 1): sendTo **본인 주소**, subject `[일반] 민원`, message `=일반 민원: {{ $json.이름 }}`

연결: `샘플 민원` → `생활인가?`, `생활인가?`[0] → `생활 담당자`, `생활인가?`[1] → `일반 담당자`

### 08강 — 트리거 교체

**삭제:** `수동 실행`, `샘플 민원`
**추가:** `민원 입력 폼` (`n8n-nodes-base.formTrigger`, 2.5)
- formTitle = `민원 접수`
- formDescription = `민원이 있는 경우 이곳에서 신고하세요.`
- formFields: `이름`(text, 필수), `연락처`(text, 필수), `이메일`(email, 필수), `종류`(dropdown: `생활`/`음식물`/`대형`, 필수), `상세설명`(textarea, 필수)

연결: `민원 입력 폼` → 기존의 다섯 갈래(`시트에 기록`, `접수 메일 보내기`, `처리 마감 일정`, `AI 안내문 작성`, `생활인가?`) 전부

**하류 노드의 표현식은 하나도 바뀌지 않는다.** 폼 필드명이 `샘플 민원`의 필드명과 같기 때문이다. 이 점이 08강의 가장 인상적인 지점이므로 본문에서 명확히 짚는다.

---

## File Structure

| 파일 | 책임 |
|---|---|
| `docs/day1-workflow-spec.md` | 위 정본 사양을 구현자·후속 단계가 참조할 단일 출처로 고정 |
| `public/downloads/day1-01.json` ~ `day1-08.json` | 각 강의 종료 시점 워크플로우 (기존 자리표시자를 교체) |
| `public/day1/01.html` ~ `08.html` | `#flow` 다이어그램 교정 + `#steps`·`#verify`·`#trouble` 본문 작성 |
| `public/prep/day1.html` | 구글 시트 머리글 안내 추가 (정본 6개 컬럼) |

`public/index.html`, `public/day2/*`, CSS, `tools/*`는 이 계획에서 **수정하지 않는다.**

---

### Task 1: 정본 사양 문서와 워크플로우 JSON 8개

**Files:**
- Create: `docs/day1-workflow-spec.md`
- Modify: `public/downloads/day1-01.json` ~ `day1-08.json` (8개, 자리표시자를 실물로 교체)

**Interfaces:**
- Produces: 8개 JSON. Task 2가 이 JSON의 노드 구성을 그대로 다이어그램으로 옮기고, Task 3~6이 본문에서 이 값들을 인용한다. **이 Task의 산출물이 이후 모든 Task의 사실 출처다.**

- [ ] **Step 1: `docs/day1-workflow-spec.md` 작성**

이 계획의 "핵심 설계 결정"과 "강의별 정본 사양" 두 절을 그대로 옮겨 적는다. 계획 파일은 실행이 끝나면 참조되지 않으므로, 후속 단계(2일차, 캡처 작업)가 볼 수 있는 곳에 사실을 남긴다.

- [ ] **Step 2: 01강 JSON 작성**

`public/downloads/day1-01.json`. n8n import가 받아들이는 최소 형태:

```json
{
  "name": "[공무원] 1일차 01 첫 워크플로우",
  "nodes": [
    {
      "parameters": {},
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [0, 0],
      "id": "d1-01-trigger",
      "name": "수동 실행"
    },
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "id": "a1",
              "name": "인사말",
              "value": "안녕하세요, 홍길동님",
              "type": "string"
            }
          ]
        },
        "options": {}
      },
      "type": "n8n-nodes-base.set",
      "typeVersion": 3.4,
      "position": [220, 0],
      "id": "d1-01-set",
      "name": "값 만들기"
    }
  ],
  "connections": {
    "수동 실행": {
      "main": [[{ "node": "값 만들기", "type": "main", "index": 0 }]]
    }
  },
  "settings": { "executionOrder": "v1" }
}
```

- [ ] **Step 3: 02~08강 JSON 작성**

각 강의는 앞 강의의 JSON에서 시작해 "강의별 정본 사양"의 변경만 적용한다. `position`은 부챗살이 보이도록 배치한다 — 트리거 `[0,0]`, 데이터 노드 `[220,0]`, 갈라지는 액션 노드들은 x=`460`에 y를 `-300`부터 `150` 간격으로 늘어놓는다. 07강의 두 담당자 노드는 x=`680`.

강사 개인정보 자리에는 다음을 넣는다:
- 이메일 필드 값: `본인이메일@example.com`
- 시트 documentId: `여기에_본인_시트_ID`
- 캘린더 id: `본인이메일@example.com`

수강생이 import 후 반드시 바꿔야 하는 값이므로, 눈에 띄게 틀린 값을 넣는 것이 빈 값보다 낫다.

- [ ] **Step 4: 8개 JSON을 모두 검증**

n8n MCP의 `validate_workflow`로 각 JSON을 검사한다. **이 도구는 로컬 JSON만 검사하며 인스턴스에 아무것도 만들지 않는다.** `n8n_create_workflow`·`n8n_update_*`는 절대 호출하지 않는다.

노드 타입·typeVersion 오류, 끊어진 연결, 필수 파라미터 누락이 없어야 한다. 자격증명 미설정 경고는 정상이다(수강생이 각자 연결한다).

- [ ] **Step 5: 사이트 검사**

```bash
cd "D:/Github/n8n_WS/PublicFlow"
python tools/check_site.py
```

Expected: PASS, exit 0. 1단계에서 추가한 다운로드 JSON 유효성 검사가 8개 파일을 파싱한다.

- [ ] **Step 6: 커밋**

```bash
git add docs/day1-workflow-spec.md public/downloads/
git commit -m "feat: 1일차 누적 워크플로우 정본 사양과 단계별 JSON 8개

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: 플로우 다이어그램을 부챗살 구조로 교정

**Files:**
- Modify: `public/day1/01.html` ~ `08.html` (`#flow` 섹션만)

**Interfaces:**
- Consumes: Task 1의 JSON — 다이어그램은 JSON의 노드·연결과 정확히 일치해야 한다
- Produces: Task 3~6이 본문을 쓸 때 참조할 확정된 시각 구조

1단계의 다이어그램은 모든 노드를 일직선으로 그렸다. 실제 구조는 `샘플 민원`에서 갈라지는 부챗살이므로 03강부터 어긋난다. 01·02강은 실제로 일직선이므로 그대로 둔다.

- [ ] **Step 1: 부챗살 표현 방식 확정**

새 CSS를 만들지 않는다. 1단계에서 07강용으로 추가한 `.flow-split`(세로로 쌓는 컨테이너)가 그대로 쓰인다.

03강 이후의 구조:

```html
<div class="flow">
  <div class="flow-node is-dim"><span class="t">수동 실행</span><span class="k">수동 트리거</span></div>
  <div class="flow-arrow">▶</div>
  <div class="flow-node is-dim"><span class="t">샘플 민원</span><span class="k">Edit Fields</span></div>
  <div class="flow-arrow">▶</div>
  <div class="flow-split">
    <div class="flow-node is-dim"><span class="t">시트에 기록</span><span class="k">Google Sheets</span></div>
    <div class="flow-node is-new"><span class="t">접수 메일 보내기</span><span class="k">Gmail</span></div>
  </div>
</div>
```

`.flow-split` 안에 갈래를 세로로 쌓는다. 이번 강의에서 붙이는 갈래만 `is-new`다.

- [ ] **Step 2: 01·02강 확인만 하고 넘어가기**

01강: `수동 실행`(is-new) ▶ `값 만들기`(is-new). 변경 없음.
02강: `수동 실행`(is-dim) ▶ `값 만들기`(is-dim) ▶ `값 가져오기`(is-new). 변경 없음.

두 강의는 실제로 일직선이므로 현재 마크업이 옳다. 손대지 않는다.

- [ ] **Step 3: 03강 다이어그램**

`수동 실행`(dim) ▶ `샘플 민원`(**is-new**) ▶ `시트에 기록`(**is-new**)

`.flow-split` 불필요(갈래가 하나뿐). 03강 범례는 1단계에서 이미 노드 교체를 설명하도록 고쳐두었다 — 그 문장을 유지하되, `값 만들기`/`값 가져오기`가 사라지고 `샘플 민원`이 그 자리에 온다는 서술이 Task 1의 JSON과 맞는지 확인한다.

- [ ] **Step 4: 04~07강 다이어그램**

각 강의는 `.flow-split` 안의 갈래가 하나씩 늘어난다. 이전 갈래는 `is-dim`, 이번 갈래만 `is-new`.

| 강 | `.flow-split` 안의 갈래 (위→아래) |
|---|---|
| 04 | 시트에 기록(dim), **접수 메일 보내기(new)** |
| 05 | 시트에 기록(dim), 접수 메일 보내기(dim), **처리 마감 일정(new)** |
| 06 | 위 3개(dim), **AI 안내문 작성(new)** |
| 07 | 위 4개(dim), **생활인가?(new)** |

07강의 IF는 다시 두 갈래로 나뉜다. `생활인가?` 노드 뒤에 `.flow-arrow`와 또 하나의 `.flow-split`을 두어 `생활 담당자`(참)·`일반 담당자`(거짓)를 넣는다. 두 노드의 `.k`는 `참`·`거짓`이다(1단계에서 확정한 유일한 예외).

06강에는 `Google Gemini Chat Model`이 `AI 안내문 작성`에 붙는 보조 노드로 존재한다. 부챗살 안에 별도 갈래로 그리면 오해를 부르므로, `AI 안내문 작성` 노드 하나로만 표현하고 본문에서 모델 노드가 함께 붙는다는 것을 설명한다.

- [ ] **Step 5: 08강 다이어그램**

`민원 입력 폼`(**is-new**) ▶ `.flow-split`에 다섯 갈래 전부(dim) ▶ 07의 두 담당자(dim)

`수동 실행`과 `샘플 민원`은 **그리지 않는다**(삭제되었다). 범례에 트리거와 데이터 노드가 함께 폼으로 교체되었음을 밝힌다. 1단계에 있던 `민원 데이터 정리` 노드는 **삭제한다** — 정본 사양에서 쓰지 않기로 했다.

- [ ] **Step 6: 검사와 커밋**

```bash
python tools/check_site.py
```

Expected: PASS, exit 0.

```bash
git add public/day1/
git commit -m "fix: 1일차 플로우 다이어그램을 실제 부챗살 구조로 교정

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: 01·02강 본문

**Files:**
- Modify: `public/day1/01.html`, `public/day1/02.html`

**Interfaces:**
- Consumes: Task 1의 JSON, Task 2의 다이어그램
- Produces: 나머지 강의가 따를 본문 서술 방식(단계 쪼개기 정도, 캡처 배치, `code.val` 사용 기준)

01강은 1단계에서 이미 본문이 있다. 이 Task는 02강을 새로 쓰고, 01강은 정본 사양과 어긋나는 부분만 고친다.

- [ ] **Step 1: 01강 대조**

1단계 본문의 값이 정본과 맞는지 확인한다. `인사말` = `안녕하세요, 홍길동님`, 노드 이름 `값 만들기`. 어긋나면 정본에 맞춘다.

`#download` 링크가 가리키는 `day1-01.json`이 Task 1에서 실물로 바뀌었으므로, "이 파일을 n8n에서 불러오면 이어서 진행할 수 있습니다"가 이제 사실이다. 문구는 그대로 둔다.

- [ ] **Step 2: 02강 `#steps` 작성**

가르치는 것은 `{{ }}` 표현식 하나다. 단계:

1. 01강 워크플로우를 연다
2. `값 만들기` 오른쪽 `+`를 눌러 `Edit Fields (Set)`를 하나 더 추가한다
3. 이름 `최종문구`, 값 칸 오른쪽의 표현식 전환(`fx` 또는 `Expression` 탭)을 누른다 — **초보자가 가장 많이 막히는 지점이므로 캡처를 넣는다**
4. `{{ $json.인사말 }} 반갑습니다.` 를 입력한다
5. 노드 이름을 `값 가져오기`로 바꾼다(노드 제목을 더블클릭)

`{{ $json.인사말 }}`의 의미를 한 문단으로 설명한다: `$json`은 앞 노드가 넘겨준 데이터, `.인사말`은 그중 그 이름의 값. 앞 노드에서 만든 이름을 그대로 쓴다는 점을 짚는다.

`code.val`로 감쌀 것: `최종문구`, `{{ $json.인사말 }} 반갑습니다.`, `값 가져오기`, `Edit Fields (Set)`.

- [ ] **Step 3: 02강 `#verify`·`#trouble` 작성**

`#verify`: 실행 후 `값 가져오기` 노드를 눌러 `최종문구: 안녕하세요, 홍길동님 반갑습니다.`가 보이면 성공.

`#trouble` 3가지:
- 값이 `{{ $json.인사말 }} 반갑습니다.` 그대로 글자로 보인다 → 표현식 전환을 안 눌렀다. 값 칸이 표현식 모드인지 확인
- `undefined 반갑습니다.`가 나온다 → 앞 노드의 필드 이름과 철자가 다르다. `인사말`을 정확히 확인
- 앞 노드가 연결되지 않았다 → 선이 이어져 있는지 확인

- [ ] **Step 4: 캡처 자리 추가**

02강에 최소 2개: 표현식 전환 버튼 위치, 표현식 입력 후 미리보기 결과. id는 `fig-d1-02-2`, `fig-d1-02-3`(기존 `fig-d1-02-1`이 `#goal`에 있다). 페이지 내 연번이 끊기지 않게 한다.

- [ ] **Step 5: 검사와 커밋**

```bash
python tools/check_site.py
```
Expected: PASS, exit 0. `작성 예정입니다.`가 02강에서 사라졌는지 눈으로 확인한다.

```bash
git add public/day1/01.html public/day1/02.html
git commit -m "feat: 1일차 01·02강 본문 작성

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: 03·04강 본문

**Files:**
- Modify: `public/day1/03.html`, `public/day1/04.html`, `public/prep/day1.html`

**Interfaces:**
- Consumes: Task 1 JSON, Task 3이 확정한 서술 방식
- Produces: 외부 서비스 연결(자격증명) 서술 방식 — 05·06강이 그대로 따른다

03강은 이 강좌에서 처음으로 외부 서비스를 연결한다. 자격증명 연결이 초보자에게 가장 험한 구간이므로 단계를 잘게 쪼갠다.

- [ ] **Step 1: `prep/day1.html`에 시트 준비 안내 추가**

구글 시트를 미리 만들어두는 것이 03강 진행의 전제다. 준비물 페이지에 항목을 하나 추가한다.

- 구글 드라이브에서 새 스프레드시트를 만든다
- 이름은 자유(예: `민원 처리 리스트`)
- **1행에 머리글 6개를 정확히 이 순서로** 넣는다: `이름` `연락처` `이메일` `종류` `상세설명` `등록일`
- 머리글 철자가 다르면 03강에서 값이 엉뚱한 칸에 들어간다는 점을 `.note.warn`으로 경고

캡처 자리 1개(머리글이 입력된 시트 화면). id는 `prep/day1.html`의 기존 연번을 이어서 붙이고, 뒤 그림들의 번호를 밀지 않도록 **맨 끝 번호**를 쓴다.

- [ ] **Step 2: 03강 `#steps` 작성**

단계:
1. 01·02강에서 만든 `값 만들기`·`값 가져오기` 두 노드를 **삭제한다**(노드 클릭 후 Delete). 왜 지우는지 한 문장으로 설명 — 지금까지는 문법 연습이었고 이제 진짜 민원 데이터를 쓴다
2. `수동 실행` 오른쪽에 `Edit Fields (Set)`를 추가하고 이름을 `샘플 민원`으로 바꾼다
3. 필드 5개를 추가한다 — 이름/연락처/이메일/종류/상세설명. 값은 정본 사양대로, **이메일은 본인 주소**
4. `샘플 민원` 오른쪽에 `Google Sheets` 노드를 추가한다
5. **자격증명 연결** — `Create new credential` → 구글 로그인 → 권한 허용 → n8n으로 돌아옴. 캡처 3개(자격증명 선택 화면, 구글 동의 화면, 연결 완료 상태)
6. Resource `Sheet`, Operation `Append Row`
7. Document를 목록에서 본인 시트로 고른다. **여기서 목록이 비어 보이면 자격증명이 제대로 안 붙은 것**
8. Sheet는 `시트1`
9. Mapping을 `Map Each Column Manually`로 두고 6개 칸에 표현식을 넣는다(정본 사양의 6줄 그대로)
10. 노드 이름을 `시트에 기록`으로 바꾼다

`.note.warn`으로: 기관 계정은 외부 앱 연결이 막혀 있을 수 있으니 개인 구글 계정을 쓰라는 안내(준비물 페이지와 동일한 이유).

- [ ] **Step 3: 03강 `#verify`·`#trouble`**

`#verify`: 실행 후 시트를 새로고침하면 2행에 값이 들어가 있다. `등록일`에 오늘 날짜가 찍힌다.

`#trouble`:
- 시트 목록이 비어 있다 → 자격증명이 연결되지 않았다. 5단계를 다시
- 값이 엉뚱한 칸에 들어간다 → 시트 머리글 철자가 정본과 다르다
- 권한 오류가 난다 → 기관 계정 제약. 개인 계정으로 다시 연결

- [ ] **Step 4: 04강 `#steps`**

1. `샘플 민원` 오른쪽 `+`를 누른다 — **`시트에 기록` 뒤가 아니라 `샘플 민원`에서 갈라진다는 점을 명확히 짚는다.** 왜 그런지 한 문단: 시트 노드를 지나면 데이터가 시트 기록 결과로 바뀌어 민원 내용이 사라지기 때문
2. `Gmail` 노드 추가, 자격증명 연결(03강과 같은 방식이므로 짧게)
3. To에 `{{ $json.이메일 }}` (표현식 모드)
4. Subject `민원 접수`
5. Email Type을 `Text`로
6. 본문에 정본 사양의 메일 문구를 붙여넣는다
7. 노드 이름을 `접수 메일 보내기`로

- [ ] **Step 5: 04강 `#verify`·`#trouble`**

`#verify`: 본인 받은편지함에 `민원 접수` 메일이 도착. 본문의 이름·연락처·종류가 채워져 있고 등록일이 오늘.

`#trouble`:
- 메일이 안 온다 → 스팸함 확인, To가 표현식 모드인지 확인
- 본문에 `{{ $json.이름 }}`이 글자 그대로 나온다 → 본문 칸이 표현식 모드가 아니다
- `시트에 기록` 뒤에 붙였더니 값이 비었다 → `샘플 민원`에서 갈라지도록 연결을 옮긴다

- [ ] **Step 6: 검사와 커밋**

```bash
python tools/check_site.py
```
Expected: PASS, exit 0.

```bash
git add public/day1/03.html public/day1/04.html public/prep/day1.html
git commit -m "feat: 1일차 03·04강 본문 작성, 준비물에 시트 머리글 안내 추가

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: 05·06강 본문

**Files:**
- Modify: `public/day1/05.html`, `public/day1/06.html`

**Interfaces:**
- Consumes: Task 4가 확정한 자격증명 서술 방식
- Produces: AI 노드 서술 방식 — 2일차 프로젝트가 참조한다

- [ ] **Step 1: 05강 `#steps`**

새 개념은 날짜 계산이다.

1. `샘플 민원`에서 갈라 `Google Calendar` 노드 추가
2. 자격증명 연결(03강과 같은 구글 계정)
3. Resource `Event`, Operation `Create`
4. Calendar를 본인 것으로 고른다(보통 본인 Gmail 주소가 목록에 뜬다)
5. Start에 `{{ $now.plus(3,'days').toISO() }}`
6. End에 `{{ $now.plus(3,'days').plus(1,'hour').toISO() }}`
7. Additional Fields에서 Summary를 추가하고 `민원 처리 마감 - {{ $json.이름 }}`
8. 노드 이름을 `처리 마감 일정`으로

`$now`, `.plus(3,'days')`, `.toISO()`를 각각 한 줄로 설명한다. `toISO()`가 왜 필요한지 — 캘린더가 알아듣는 날짜 형식으로 바꿔주는 것.

- [ ] **Step 2: 05강 `#verify`·`#trouble`**

`#verify`: 구글 캘린더에서 3일 뒤 날짜에 `민원 처리 마감 - 김기태` 일정이 1시간짜리로 생성.

`#trouble`:
- 일정이 안 보인다 → 3일 뒤로 이동했는지, 캘린더를 맞게 골랐는지
- 날짜 형식 오류 → `toISO()`를 빠뜨렸다
- Summary가 글자 그대로 나온다 → 표현식 모드 확인

- [ ] **Step 3: 06강 `#steps`**

새 개념은 AI다. 노드가 두 개 붙는다는 점이 다른 강의와 다르므로 먼저 설명한다.

1. `샘플 민원`에서 갈라 `Basic LLM Chain` 노드를 추가한다
2. 노드 아래에 모델 연결 자리가 생긴다. 거기서 `Google Gemini Chat Model`을 고른다 — **캡처 필수**
3. Gemini 자격증명을 연결한다(준비물에서 발급한 API 키를 붙여넣는다)
4. **모델 드롭다운을 열어 `models/gemini-2.5-flash`를 직접 고른다** — `.note.warn`으로 강조. n8n이 미리 넣어둔 값을 그대로 두면 안 되는 이유(preview 모델은 예고 없이 바뀐다). 캡처 필수
5. `Basic LLM Chain`의 Prompt를 `Define below`로 바꾸고 정본 사양의 프롬프트를 붙여넣는다
6. 노드 이름을 `AI 안내문 작성`으로

프롬프트를 한 덩어리로 붙여넣게 하되, 구조(역할 지정 → 작성 규칙 → 데이터)를 세 문장으로 설명한다. 규칙을 바꾸면 결과가 어떻게 달라지는지 한 줄 덧붙인다.

- [ ] **Step 4: 06강 `#verify`·`#trouble`**

`#verify`: 실행 후 `AI 안내문 작성` 노드의 출력 `text` 항목에 4~6문장의 안내문이 생성된다. 매번 문장이 조금씩 달라지는 것이 정상.

`#trouble`:
- API 키 오류 → 준비물에서 발급한 키를 다시 확인. 키 앞뒤 공백 주의
- 할당량 초과 → `models/gemini-2.5-flash-lite`로 바꾼다
- 결과가 영어로 나온다 → 프롬프트가 제대로 안 들어갔다. Prompt가 `Define below`인지 확인
- 모델 목록에 `gemini-2.5-flash`가 안 보인다 → 자격증명이 연결되어야 목록이 채워진다

- [ ] **Step 5: 검사와 커밋**

```bash
python tools/check_site.py
```
Expected: PASS, exit 0.

```bash
git add public/day1/05.html public/day1/06.html
git commit -m "feat: 1일차 05·06강 본문 작성

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: 07·08강 본문

**Files:**
- Modify: `public/day1/07.html`, `public/day1/08.html`

**Interfaces:**
- Consumes: Task 1~5 전부
- Produces: 1일차 완주. 08강 종료 시점이 2일차의 출발점이 된다

- [ ] **Step 1: 07강 `#steps`**

새 개념은 조건 분기다.

1. `샘플 민원`에서 갈라 `If` 노드를 추가한다
2. 조건에 왼쪽 값 `{{ $json.종류 }}`, 연산자 `is equal to`, 오른쪽 값 `생활`
3. 노드 이름을 `생활인가?`로
4. IF 노드 오른쪽에 출력이 **두 개**인 것을 확인한다 — 위가 참(true), 아래가 거짓(false). 캡처 필수
5. 위쪽 출력에 `Gmail` 노드를 붙인다. To는 본인 주소, Subject `[생활 관련] 민원`, 본문 `생활 관련 민원: {{ $json.이름 }}`. 이름은 `생활 담당자`
6. 아래쪽 출력에 `Gmail` 노드를 하나 더 붙인다. Subject `[일반] 민원`, 본문 `일반 민원: {{ $json.이름 }}`. 이름은 `일반 담당자`

`.note`로: 실제 업무라면 두 주소가 다르겠지만, 실습에서는 둘 다 본인 주소로 두는 편이 낫다. 한 받은편지함에서 제목만 보고 어느 갈래를 탔는지 바로 확인할 수 있다.

- [ ] **Step 2: 07강 `#verify`·`#trouble`**

`#verify`: `샘플 민원`의 `종류`가 `생활`이므로 실행하면 `[생활 관련] 민원` 메일만 온다. 이어서 `종류`를 `음식물`로 바꾸고 다시 실행하면 이번엔 `[일반] 민원`이 온다 — **두 갈래를 모두 확인해보게 하는 것이 이 강의의 핵심**이므로 단계로 명시한다.

`#trouble`:
- 항상 아래쪽(거짓)으로만 간다 → `종류` 철자 확인, 왼쪽 값이 표현식 모드인지 확인
- 메일이 두 통 다 온다 → 두 Gmail이 같은 출력에 붙어 있다. 연결선을 확인
- 값 비교가 안 된다 → 오른쪽 값에 따옴표를 넣지 않았는지 확인(`생활`만 입력)

- [ ] **Step 3: 08강 `#steps`**

1일차의 마무리다. 트리거 교체 하나로 워크플로우가 실제로 쓸 수 있는 물건이 된다.

1. `수동 실행`과 `샘플 민원` 두 노드를 삭제한다
2. `Form Trigger`(`n8n Form` 트리거) 노드를 추가한다
3. Form Title `민원 접수`, Description `민원이 있는 경우 이곳에서 신고하세요.`
4. 입력 필드 5개를 추가한다 — 이름(텍스트), 연락처(텍스트), 이메일(이메일), 종류(드롭다운: 생활/음식물/대형), 상세설명(텍스트영역). 전부 필수. 캡처 2개(필드 추가 화면, 드롭다운 옵션 입력)
5. 노드 이름을 `민원 입력 폼`으로
6. 폼에서 나오는 선을 기존 다섯 갈래(`시트에 기록`, `접수 메일 보내기`, `처리 마감 일정`, `AI 안내문 작성`, `생활인가?`)에 각각 연결한다

**`.note.tip`으로 강조:** 하류 노드의 설정은 하나도 바꾸지 않았다. 폼의 입력 칸 이름이 `샘플 민원`에서 쓰던 이름과 똑같기 때문에 `{{ $json.이름 }}` 같은 표현식이 그대로 동작한다. 이름을 잘 맞춰두면 나중에 데이터가 어디서 오든 바꿔 끼울 수 있다 — 자동화를 오래 쓰는 요령이다.

- [ ] **Step 4: 08강 `#verify`·`#trouble`**

`#verify`: 워크플로우를 활성화(Active)하면 폼 주소가 생긴다. 그 주소를 열어 민원을 직접 제출한다. 제출하면 시트에 행이 추가되고, 메일이 오고, 캘린더에 일정이 잡히고, 분기 메일까지 온다 — **1일차에 만든 모든 것이 한 번에 동작한다.**

테스트만 할 때는 `Execute workflow`를 누르면 임시 폼 주소가 뜬다는 점도 안내한다.

`#trouble`:
- 폼 주소가 안 열린다 → 워크플로우가 활성화되어 있는지 확인
- 제출했는데 아무 일도 없다 → 폼에서 나가는 선이 다섯 갈래에 모두 연결되었는지
- 값이 비어 들어간다 → 폼 필드 이름 철자가 하류 표현식과 다르다
- 활성화 버튼이 비활성 상태다 → 트리거가 폼 트리거인지 확인(수동 실행은 활성화할 수 없다)

- [ ] **Step 5: 1일차 완주 안내 추가**

08강 `#download` 아래, `.pager` 위에 `.note.tip`을 하나 둔다. 1일차에 만든 것을 두 문장으로 정리하고, 2일차는 이 워크플로우를 더 키우는 게 아니라 다른 종류의 자동화 네 가지를 만든다는 것을 알린다.

- [ ] **Step 6: 검사와 커밋**

```bash
python tools/check_site.py
```
Expected: PASS, exit 0.

```bash
git add public/day1/07.html public/day1/08.html
git commit -m "feat: 1일차 07·08강 본문 작성, 1일차 완주

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: 1일차 전체 정합성 점검

**Files:**
- Modify: 점검에서 발견된 파일

**Interfaces:**
- Consumes: Task 1~6 전부
- Produces: 2단계 완료 상태

여덟 강의를 서로 다른 시점에 썼으므로 앞뒤가 어긋날 수 있다. 통째로 읽고 맞춘다.

- [ ] **Step 1: 노드 이름 일관성**

여덟 페이지에서 같은 노드를 부르는 이름이 같아야 한다. `샘플 민원`, `시트에 기록`, `접수 메일 보내기`, `처리 마감 일정`, `AI 안내문 작성`, `생활인가?`, `생활 담당자`, `일반 담당자`, `민원 입력 폼`. 본문·다이어그램·JSON 세 곳이 모두 같은지 확인한다.

- [ ] **Step 2: 이어짐 확인**

각 강의의 `#steps` 1단계가 "앞 강의를 마친 상태"에서 시작하는지 확인한다. 03강처럼 노드를 지우는 강의는 무엇을 지우는지 명확한지, 04강 이후가 `샘플 민원`에서 갈라진다는 점을 매번 짚는지 본다.

- [ ] **Step 3: 강사 개인정보 잔존 확인**

```bash
cd "D:/Github/n8n_WS/PublicFlow"
grep -rn "aqua0405\|1nMbi2VfMxQ2Bud1M7WjyZjyz6XASN2QyX0Mecc3TjXM" public/ docs/ || echo "없음"
```

Expected: 없음. 하나라도 나오면 "본인 것으로 교체" 안내로 바꾼다.

- [ ] **Step 4: 표현식 일관성**

```bash
grep -rn "now.format(" public/ docs/ || echo "없음"
```

Expected: 없음. `$now.format(`이 남아 있으면 `toFormat(`으로 고친다(결정 4).

- [ ] **Step 5: 캡처 목록 확인**

```bash
python tools/apply_captures.py --list
python tools/apply_captures.py --check
```

새로 추가한 자리들이 목록에 나오고 id 연번이 끊기지 않는지 본다. `--check`는 깨끗해야 한다.

- [ ] **Step 6: 전체 검사**

```bash
python tools/check_site.py
```

Expected: PASS, exit 0. 1일차 여덟 페이지에 `작성 예정입니다.`가 하나도 남아 있지 않아야 한다.

```bash
grep -rn "작성 예정입니다" public/day1/ || echo "1일차 본문 완료"
```

Expected: `1일차 본문 완료`.

- [ ] **Step 7: 커밋**

```bash
git add -A public/ docs/
git commit -m "fix: 1일차 전체 정합성 점검 반영

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-Review

**1. 스펙 커버리지**

| 스펙 항목 (8절 2단계) | 담당 Task |
|---|---|
| 1일차 본문 01~08 | Task 3·4·5·6 |
| JSON 스냅샷 8개 | Task 1 |
| 누적 구조 확정 | Task 1(사양) · Task 2(다이어그램) |
| 강의 2~3개 단위 확인 | Task 3~6이 각각 2강씩 — 확인 지점이 자연스럽게 생긴다 |
| 2일차 본문·캡처·배포 | **이 계획 범위 밖.** 3~5단계 |

**2. 자리표시자 점검**

계획 본문에 `TBD`/`TODO` 없음. Task 6까지 끝나면 `작성 예정입니다.`가 1일차에서 사라지며, Task 7 Step 6이 이를 자동으로 확인한다.

**3. 이름 일관성**

- 노드 이름 9개를 Task 7 Step 1에서 세 곳(본문·다이어그램·JSON) 대조
- 파일명 `day1-NN.json`은 1단계에서 고정된 것을 그대로 씀
- 그림 id는 `fig-d1-NN-N` 형식 유지, 페이지 내 연번

**4. 발견해 고친 것**

계획을 쓰면서 두 가지를 바로잡았다.

첫째, 처음에는 노드를 일직선으로 잇는 구조로 쓰다가, Gmail·Sheets·Calendar 노드의 출력이 입력을 덮어써서 하류 표현식이 전부 깨진다는 것을 확인하고 부챗살 구조로 바꿨다(결정 1). 1단계 다이어그램이 이미 일직선으로 그려져 있으므로 Task 2가 이를 교정한다.

둘째, 08강이 `민원 데이터 정리`라는 노드를 쓰는 것으로 1단계에 그려져 있으나, 폼 필드명이 `샘플 민원`과 동일해 그 노드가 필요 없다. Task 2 Step 5에서 삭제한다.
