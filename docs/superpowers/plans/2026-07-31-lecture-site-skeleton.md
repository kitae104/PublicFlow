# 공무원 n8n 강의자료 사이트 — 1단계(뼈대) 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 빌드 도구 없이 Vercel에 그대로 올라가는 정적 강의 사이트의 뼈대를 만들고, 링크·구조 자동 검사로 무결성을 보장한다.

**Architecture:** `public/` 아래 순수 HTML/CSS만 둔다. 공통 디자인은 CSS 커스텀 프로퍼티 한 곳에서 관리하고, 페이지는 서로를 import하지 않는 독립 파일로 둔다(빌드 없음의 대가로 네비게이션 HTML 중복을 허용). 무결성은 `tools/check_site.py`가 링크·필수 섹션·자리표시자 토큰을 검사해 지킨다.

**Tech Stack:** 정적 HTML5, CSS3(커스텀 프로퍼티 + `prefers-color-scheme`), 인라인 SVG, 검사 스크립트는 표준 라이브러리만 쓰는 Python 3.11.

## Global Constraints

- **작업 루트:** `D:\Github\n8n_WS\PublicFlow`
- **Python 실행은 반드시 `python`** — 이 머신의 `python3`은 Windows 스토어 스텁이라 코드를 실행하지 않고 문자열 `Python`만 출력한 뒤 exit 0을 반환한다. `python3`을 쓰면 검사가 통과한 것처럼 보이면서 실제로는 아무것도 검사하지 않는다.
- **빌드 도구 금지:** npm/webpack/Next.js 등 도입하지 않는다. `public/`의 파일이 곧 배포물이다.
- **외부 리소스 금지:** CDN 스크립트, 웹폰트, 외부 이미지 모두 쓰지 않는다. 폰트는 시스템 스택, 아이콘은 인라인 SVG 또는 이모지.
- **Gemini 모델 문자열은 정확히 `models/gemini-2.5-flash`** — 대체 모델은 `models/gemini-2.5-flash-lite`.
- **배포 금지:** 이 계획의 어떤 단계도 Vercel 배포나 n8n 워크플로우 생성을 수행하지 않는다. 로컬 파일 작성까지만이다.
- **언어:** 모든 사용자 노출 텍스트는 한국어. 코드 식별자·파일명은 영문 소문자 케밥케이스.
- **페이지 필수 섹션 id:** 강의 페이지는 `#goal`, `#flow`, `#why`, `#steps`, `#verify`, `#trouble`, `#download` 7개를 모두 가진다.

---

## File Structure

| 파일 | 책임 |
|---|---|
| `.gitignore` | 산출물·임시파일 제외 |
| `vercel.json` | `public/`을 정적 루트로 지정 |
| `tools/check_site.py` | 링크·필수 섹션·자리표시자 검사 (유일한 테스트 도구) |
| `public/assets/style.css` | 색·타이포·레이아웃·컴포넌트 전체 |
| `public/assets/flow.css` | SVG 플로우 다이어그램 전용 스타일 |
| `public/index.html` | 커리큘럼 개요 + 전체 목차 |
| `public/prep/day1.html` | 준비물 ① 구글 계정·Gemini 키 |
| `public/prep/day2.html` | 준비물 ② 텔레그램 봇 |
| `public/day1/01.html` | 1일차 1강 — **완전 구현(참조용)** |
| `public/day1/02.html`~`08.html` | 1일차 2~8강 뼈대 |
| `public/day2/p1.html`~`p4.html` | 2일차 프로젝트 뼈대 |
| `public/downloads/.gitkeep` | JSON 스냅샷 자리 (2단계에서 채움) |

파일이 서로를 import하지 않으므로, 한 페이지를 고쳐도 다른 페이지가 깨지지 않는다. 대신 네비게이션·푸터 HTML이 중복되는데, 이는 빌드 도구를 안 쓰기로 한 결정의 대가로 받아들인다. 중복 블록이 어긋나는 것은 `check_site.py`의 링크 검사가 잡는다.

---

### Task 1: 저장소 초기화와 검사 도구

**Files:**
- Create: `.gitignore`
- Create: `vercel.json`
- Create: `tools/check_site.py`
- Create: `public/downloads/.gitkeep`

**Interfaces:**
- Produces: `python tools/check_site.py` — 성공 시 exit 0 + `OK: N pages, M links checked`, 실패 시 exit 1 + 항목별 오류 목록. 이후 모든 Task가 이 명령으로 검증한다.

- [ ] **Step 1: git 저장소 초기화**

```bash
cd "D:/Github/n8n_WS/PublicFlow"
git init
git branch -M main
```

- [ ] **Step 2: `.gitignore` 작성**

```gitignore
node_modules/
.vercel/
.DS_Store
Thumbs.db
*.log
__pycache__/
```

- [ ] **Step 3: `vercel.json` 작성**

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "outputDirectory": "public",
  "cleanUrls": true,
  "trailingSlash": false
}
```

- [ ] **Step 4: 검사 스크립트 `tools/check_site.py` 작성**

```python
"""공무원 n8n 강의자료 사이트 무결성 검사.

검사 항목:
  1. 내부 링크(href/src)가 실제 존재하는 파일을 가리키는가
  2. 강의 페이지가 필수 섹션 id 7개를 모두 가지는가
  3. 금지 자리표시자 토큰이 남아있지 않은가

사용법:  python tools/check_site.py
주의:    python3 은 이 머신에서 스토어 스텁이므로 반드시 python 을 쓸 것.
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

REQUIRED_SECTIONS = ["goal", "flow", "why", "steps", "verify", "trouble", "download"]
FORBIDDEN_TOKENS = ["TBD", "TODO", "FIXME", "lorem ipsum", "XXX"]

ATTR_RE = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
ID_RE = re.compile(r'id\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)


def is_external(url: str) -> bool:
    if url.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return True
    return bool(urlparse(url).scheme)


def lesson_pages(pages):
    """강의 페이지만 — index 와 prep 은 7섹션 규칙에서 제외."""
    return [p for p in pages if p.parent.name in ("day1", "day2")]


def main() -> int:
    if not PUBLIC.is_dir():
        print(f"FAIL: public/ 디렉터리가 없습니다: {PUBLIC}")
        return 1

    pages = sorted(PUBLIC.rglob("*.html"))
    if not pages:
        print("FAIL: public/ 아래 HTML 파일이 하나도 없습니다")
        return 1

    errors = []
    link_count = 0

    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        text = page.read_text(encoding="utf-8")

        # 1. 내부 링크 존재 확인
        for raw in ATTR_RE.findall(text):
            if is_external(raw):
                continue
            link_count += 1
            target = unquote(raw.split("#", 1)[0].split("?", 1)[0])
            if not target:
                continue
            if target.startswith("/"):
                resolved = PUBLIC / target.lstrip("/")
            else:
                resolved = page.parent / target
            # cleanUrls 대응: 확장자 없는 링크는 .html 도 허용
            if not resolved.exists() and not resolved.with_suffix(".html").exists():
                errors.append(f"{rel}: 끊어진 링크 -> {raw}")

        # 2. 필수 섹션 id (강의 페이지만)
        if page in lesson_pages(pages):
            ids = set(ID_RE.findall(text))
            missing = [s for s in REQUIRED_SECTIONS if s not in ids]
            if missing:
                errors.append(f"{rel}: 필수 섹션 누락 -> {', '.join(missing)}")

        # 3. 금지 토큰
        lowered = text.lower()
        for token in FORBIDDEN_TOKENS:
            if token.lower() in lowered:
                errors.append(f"{rel}: 금지 토큰 발견 -> {token}")

    if errors:
        print(f"FAIL: {len(errors)}건")
        for e in errors:
            print("  -", e)
        return 1

    print(f"OK: {len(pages)} pages, {link_count} links checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: 검사 스크립트가 빈 사이트를 올바르게 거부하는지 확인**

```bash
cd "D:/Github/n8n_WS/PublicFlow"
mkdir -p public/downloads
touch public/downloads/.gitkeep
python tools/check_site.py
```

Expected: FAIL — `public/ 아래 HTML 파일이 하나도 없습니다`, exit 1.

이것이 이 계획의 "실패하는 테스트"다. HTML이 생기기 전까지 검사는 반드시 실패해야 한다.

- [ ] **Step 6: 커밋**

```bash
git add .gitignore vercel.json tools/check_site.py public/downloads/.gitkeep
git commit -m "chore: 사이트 뼈대 저장소 초기화와 무결성 검사 도구 추가

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: 공통 디자인 시스템

**Files:**
- Create: `public/assets/style.css`
- Create: `public/assets/flow.css`

**Interfaces:**
- Produces: 이후 모든 페이지가 쓰는 CSS 클래스 계약
  - 레이아웃: `.wrap`, `.page-head`, `.crumb`, `.pager`
  - 섹션: `.sec`, `.sec-title`
  - 단계: `ol.steps > li`, `.step-title`, `.hint`
  - 캡처 자리: `figure.capture`, `.capture-cap`, `.capture-guide`
  - 강조 박스: `.note`, `.note.warn`, `.note.tip`
  - 다운로드: `.dl`, `.dl-name`
  - 코드/값: `code.val`
  - 플로우(별도 파일): `.flow`, `.flow-node`, `.flow-node.is-new`, `.flow-node.is-dim`, `.flow-arrow`

- [ ] **Step 1: `public/assets/style.css` 작성**

색은 커스텀 프로퍼티 한 곳에서만 정의한다. 다크 모드는 `prefers-color-scheme`으로 값만 갈아끼운다. 인쇄 시 배경을 없애고 링크 URL을 펼친다.

```css
/* ── 색·간격 토큰 ───────────────────────────────────────── */
:root {
  --paper: #ffffff;
  --paper-2: #f6f9fb;
  --ink: #16202a;
  --muted: #5b6b7a;
  --line: #dde5ec;
  --accent: #0f766e;
  --accent-ink: #ffffff;
  --accent-soft: #ccfbf1;
  --new: #c2410c;
  --new-soft: #ffedd5;
  --warn: #b45309;
  --warn-soft: #fef3c7;
  --radius: 10px;
  --maxw: 46rem;
}

@media (prefers-color-scheme: dark) {
  :root {
    --paper: #11171d;
    --paper-2: #171f27;
    --ink: #e6edf3;
    --muted: #9fb0bf;
    --line: #2a3641;
    --accent: #5eead4;
    --accent-ink: #06231f;
    --accent-soft: #10403a;
    --new: #fb923c;
    --new-soft: #46220d;
    --warn: #fbbf24;
    --warn-soft: #3d2f0a;
  }
}

/* ── 기본 ──────────────────────────────────────────────── */
* { box-sizing: border-box; }

body {
  margin: 0;
  padding: 0 1rem 5rem;
  background: var(--paper);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
               "Malgun Gothic", "맑은 고딕", AppleSDGothicNeo-Regular,
               "Apple SD Gothic Neo", sans-serif;
  font-size: 17px;
  line-height: 1.85;
  word-break: keep-all;
  overflow-wrap: break-word;
}

.wrap { max-width: var(--maxw); margin: 0 auto; }

a { color: var(--accent); }
a:hover { text-decoration: none; }

h1, h2, h3 { line-height: 1.4; letter-spacing: -0.01em; }
h1 { font-size: 1.9rem; margin: 0 0 .3rem; }
h2 { font-size: 1.3rem; margin: 2.6rem 0 .9rem; }
h3 { font-size: 1.05rem; margin: 1.8rem 0 .5rem; }

/* ── 머리말·이동 ───────────────────────────────────────── */
.crumb {
  font-size: .85rem;
  color: var(--muted);
  padding: 1.5rem 0 0;
}
.crumb a { color: var(--muted); }

.page-head {
  padding: .5rem 0 1.5rem;
  border-bottom: 2px solid var(--line);
  margin-bottom: 1rem;
}
.page-head .sub { color: var(--muted); margin: 0; }

.pager {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 4rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--line);
  font-size: .95rem;
}
.pager span { color: var(--muted); }

/* ── 섹션 ──────────────────────────────────────────────── */
.sec { scroll-margin-top: 1rem; }

.sec-title {
  display: flex;
  align-items: center;
  gap: .55rem;
}
.sec-title::before {
  content: "";
  width: .3rem;
  height: 1.1em;
  background: var(--accent);
  border-radius: 2px;
  flex: none;
}

/* ── 따라하기 단계 ─────────────────────────────────────── */
ol.steps { list-style: none; counter-reset: s; padding: 0; margin: 0; }

ol.steps > li {
  counter-increment: s;
  position: relative;
  padding: 0 0 1.6rem 3rem;
  border-left: 2px solid var(--line);
  margin-left: 1rem;
}
ol.steps > li:last-child { border-left-color: transparent; padding-bottom: 0; }

ol.steps > li::before {
  content: counter(s);
  position: absolute;
  left: -1rem;
  top: 0;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: var(--accent);
  color: var(--accent-ink);
  font-size: .9rem;
  font-weight: 700;
  display: grid;
  place-items: center;
}

.step-title { font-weight: 700; display: block; margin-bottom: .2rem; }
.hint { color: var(--muted); font-size: .92rem; }

/* ── 입력값 강조 ───────────────────────────────────────── */
code.val {
  background: var(--accent-soft);
  color: var(--ink);
  padding: .12em .45em;
  border-radius: 5px;
  font-size: .92em;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  word-break: break-all;
}

/* ── 안내 박스 ─────────────────────────────────────────── */
.note {
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-left: 4px solid var(--accent);
  border-radius: var(--radius);
  padding: .9rem 1.1rem;
  margin: 1.2rem 0;
}
.note p:first-child { margin-top: 0; }
.note p:last-child { margin-bottom: 0; }
.note.warn { border-left-color: var(--warn); background: var(--warn-soft); }
.note.tip  { border-left-color: var(--accent); background: var(--accent-soft); }
.note b { display: block; margin-bottom: .2rem; }

/* ── 캡처 자리표시자 ───────────────────────────────────── */
figure.capture { margin: 1rem 0; }

figure.capture img { max-width: 100%; border-radius: var(--radius); border: 1px solid var(--line); }

.capture-cap {
  font-size: .88rem;
  font-weight: 700;
  color: var(--muted);
  margin-bottom: .4rem;
}

.capture-guide {
  border: 2px dashed var(--line);
  border-radius: var(--radius);
  background: var(--paper-2);
  color: var(--muted);
  padding: 1.6rem 1.1rem;
  text-align: center;
  font-size: .92rem;
}
.capture-guide::before { content: "📷"; display: block; font-size: 1.5rem; margin-bottom: .3rem; }

/* ── 다운로드 ──────────────────────────────────────────── */
.dl {
  display: inline-flex;
  align-items: center;
  gap: .6rem;
  background: var(--accent);
  color: var(--accent-ink);
  text-decoration: none;
  padding: .8rem 1.2rem;
  border-radius: var(--radius);
  font-weight: 700;
}
.dl:hover { filter: brightness(1.08); }
.dl-name { font-family: ui-monospace, Consolas, monospace; font-weight: 400; font-size: .85em; opacity: .85; }

/* ── 목차(index) ───────────────────────────────────────── */
.toc { list-style: none; padding: 0; }
.toc li { border-bottom: 1px solid var(--line); }
.toc a {
  display: flex;
  gap: .9rem;
  align-items: baseline;
  padding: .85rem .3rem;
  text-decoration: none;
  color: var(--ink);
}
.toc a:hover { background: var(--paper-2); }
.toc .n { color: var(--accent); font-weight: 700; font-variant-numeric: tabular-nums; flex: none; }
.toc .d { color: var(--muted); font-size: .88rem; margin-left: auto; text-align: right; flex: none; }

/* ── 인쇄 ──────────────────────────────────────────────── */
@media print {
  :root { --paper: #fff; --paper-2: #fff; --ink: #000; --muted: #444; --line: #bbb; }
  body { font-size: 11pt; padding: 0; }
  .pager, .crumb { display: none; }
  .sec { break-inside: avoid; }
  a[href^="http"]::after { content: " (" attr(href) ")"; font-size: .85em; color: var(--muted); }
}
```

- [ ] **Step 2: `public/assets/flow.css` 작성**

플로우는 인라인 SVG가 아니라 **HTML + CSS**로 그린다. SVG보다 한글 줄바꿈과 반응형 처리가 쉽고, 노드 개수가 늘어도 마크업이 단순하다.

```css
/* 워크플로우 흐름도 — 가로 스크롤 허용, 새 노드만 강조 */
.flow {
  display: flex;
  align-items: stretch;
  gap: 0;
  overflow-x: auto;
  padding: 1rem .2rem;
  margin: 1rem 0;
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}

.flow-node {
  flex: none;
  min-width: 7.5rem;
  max-width: 10rem;
  padding: .7rem .8rem;
  border: 2px solid var(--accent);
  border-radius: var(--radius);
  background: var(--paper);
  font-size: .85rem;
  line-height: 1.45;
  text-align: center;
}

.flow-node .t { display: block; font-weight: 700; }
.flow-node .k { display: block; color: var(--muted); font-size: .78rem; }

/* 이전 시간까지 만든 노드 — 존재감 낮춤 */
.flow-node.is-dim { border-color: var(--line); color: var(--muted); }
.flow-node.is-dim .t { font-weight: 400; }

/* 이번 시간에 새로 붙이는 노드 */
.flow-node.is-new {
  border-color: var(--new);
  background: var(--new-soft);
  box-shadow: 0 0 0 3px var(--new-soft);
}
.flow-node.is-new .t { color: var(--new); }

.flow-arrow {
  flex: none;
  align-self: center;
  padding: 0 .45rem;
  color: var(--muted);
  font-size: 1.1rem;
}

.flow-legend { font-size: .85rem; color: var(--muted); margin-top: -.4rem; }
.flow-legend .sw {
  display: inline-block;
  width: .8rem; height: .8rem;
  border: 2px solid var(--new);
  background: var(--new-soft);
  border-radius: 3px;
  vertical-align: -1px;
  margin-right: .25rem;
}
```

- [ ] **Step 3: 커밋**

```bash
git add public/assets/style.css public/assets/flow.css
git commit -m "feat: 공통 디자인 시스템과 플로우 다이어그램 스타일 추가

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: 표지 페이지

**Files:**
- Create: `public/index.html`

**Interfaces:**
- Consumes: Task 2의 `.wrap`, `.toc`, `.note`, `.page-head`
- Produces: 12개 강의 페이지 + 준비물 2페이지로 가는 링크 구조. 이 링크가 `check_site.py`의 검사 대상이 되므로, 이후 Task들이 만들 파일 경로의 정본이 된다.

- [ ] **Step 1: `public/index.html` 작성**

```html
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>공무원을 위한 n8n 업무 자동화 — 2일 과정</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<main class="wrap">

  <header class="page-head">
    <h1>공무원을 위한 n8n 업무 자동화</h1>
    <p class="sub">코딩 없이 반복 업무를 자동으로 — 2일 과정</p>
  </header>

  <div class="note tip">
    <b>이 과정을 마치면</b>
    민원이 접수되면 시트에 기록되고, 담당자에게 메일이 가고, 처리 마감이 캘린더에 잡히고,
    AI가 안내문 초안까지 써주는 시스템을 직접 만들 수 있습니다.
  </div>

  <h2>시작하기 전에</h2>
  <ul class="toc">
    <li><a href="prep/day1.html"><span class="n">준비 ①</span><span>1일차 준비물 — 구글 계정, Gemini API 키</span><span class="d">30분</span></a></li>
    <li><a href="prep/day2.html"><span class="n">준비 ②</span><span>2일차 준비물 — 텔레그램 봇 만들기</span><span class="d">20분</span></a></li>
  </ul>

  <h2>1일차 — 민원 접수 자동화 시스템 만들기</h2>
  <p>워크플로우 하나를 8단계에 걸쳐 조금씩 키웁니다. 매 시간 노드를 하나씩 얹습니다.</p>
  <ul class="toc">
    <li><a href="day1/01.html"><span class="n">01</span><span>첫 워크플로우</span><span class="d">노드와 실행</span></a></li>
    <li><a href="day1/02.html"><span class="n">02</span><span>데이터 흐름과 표현식</span><span class="d">{{ }} 문법</span></a></li>
    <li><a href="day1/03.html"><span class="n">03</span><span>구글 시트에 자동 기록</span><span class="d">계정 연결</span></a></li>
    <li><a href="day1/04.html"><span class="n">04</span><span>이메일 자동 발송</span><span class="d">Gmail</span></a></li>
    <li><a href="day1/05.html"><span class="n">05</span><span>캘린더 일정 자동 생성</span><span class="d">날짜 계산</span></a></li>
    <li><a href="day1/06.html"><span class="n">06</span><span>AI 안내문 자동 생성</span><span class="d">Gemini</span></a></li>
    <li><a href="day1/07.html"><span class="n">07</span><span>조건에 따라 나누기</span><span class="d">IF 분기</span></a></li>
    <li><a href="day1/08.html"><span class="n">08</span><span>입력 폼으로 실제 접수받기</span><span class="d">완성</span></a></li>
  </ul>

  <h2>2일차 — 업무별 자동화 프로젝트</h2>
  <p>1일차에서 배운 것을 조합해 실제 업무에 쓸 수 있는 자동화를 네 가지 만듭니다.</p>
  <ul class="toc">
    <li><a href="day2/p1.html"><span class="n">P1</span><span>공문서 요약 서비스</span><span class="d">PDF 요약</span></a></li>
    <li><a href="day2/p2.html"><span class="n">P2</span><span>매일 아침 민원 브리핑 봇</span><span class="d">정시 자동실행</span></a></li>
    <li><a href="day2/p3.html"><span class="n">P3</span><span>AI 민원 자동 분류·답변 초안</span><span class="d">AI 분류</span></a></li>
    <li><a href="day2/p4.html"><span class="n">P4</span><span>날씨 알리미</span><span class="d">공공데이터 API</span></a></li>
  </ul>

  <div class="note warn">
    <b>준비물을 먼저 확인하세요</b>
    구글 계정과 Gemini API 키가 없으면 1일차 3강부터 진행할 수 없습니다.
    기상청 API는 신청 후 승인까지 시간이 걸리니 <a href="prep/day1.html">준비 ①</a> 맨 아래를 미리 봐두세요.
  </div>

</main>
</body>
</html>
```

- [ ] **Step 2: 검사 실행 — 링크 12개가 아직 없으므로 실패해야 함**

```bash
cd "D:/Github/n8n_WS/PublicFlow"
python tools/check_site.py
```

Expected: FAIL, `끊어진 링크 -> prep/day1.html` 등 14건.

이 실패가 정상이다. Task 4~7이 대상 파일을 만들면 사라진다.

- [ ] **Step 3: 커밋**

```bash
git add public/index.html
git commit -m "feat: 커리큘럼 표지와 전체 목차 추가

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: 준비물 페이지 2개 (완전 작성)

**Files:**
- Create: `public/prep/day1.html`
- Create: `public/prep/day2.html`

**Interfaces:**
- Consumes: Task 2 CSS 클래스
- Produces: 두 페이지 모두 `../index.html`로 돌아가는 `.crumb`, 다음 강의로 가는 `.pager`

준비물 페이지는 뼈대가 아니라 **완성본**으로 쓴다. 워크플로우 내용과 무관하게 확정된 절차라 나중에 바뀔 일이 없고, 수강생이 강의 전에 미리 봐야 하는 문서이기 때문이다.

- [ ] **Step 1: `public/prep/day1.html` 작성**

7섹션 규칙은 강의 페이지에만 적용되므로 준비물 페이지는 자유 구조다. 다음 내용을 담는다.

- 준비물 요약표: 구글 계정 / Gemini API 키 / (2일차용) 기상청 키
- **구글 계정** — 기관 계정이 외부 앱 연결을 막는 경우가 있으니 개인 Gmail 계정 권장. 캡처 자리 1개.
- **Gemini API 키 발급** — `https://aistudio.google.com/apikey` 접속 → 로그인 → `API 키 만들기` → 키 복사. 캡처 자리 3개(접속 화면 / 키 만들기 버튼 / 발급된 키).
- **키 보관 주의** `.note.warn` — 키는 비밀번호와 같다. 화면 공유·메신저 전송 금지.
- **무료 한도 안내** `.note` — 무료로 쓸 수 있으나 구글이 한도 수치를 공개 표로 게시하지 않고 계정별 화면에서 보여준다. AI Studio의 사용량 화면에서 확인.
- **모델 지정 안내** `.note.warn` — 강의에서는 <code class="val">models/gemini-2.5-flash</code>를 쓴다. n8n이 기본값으로 <code class="val">models/gemini-3-flash-preview</code>를 넣어둘 수 있는데, preview 모델은 예고 없이 바뀌므로 **직접 골라서 바꿔야 한다**. 한도가 막히면 <code class="val">models/gemini-2.5-flash-lite</code>로 교체.
- **맨 아래 별도 섹션 "2일차에 쓸 것 — 지금 미리 신청해두세요"** — 공공데이터포털 기상청 단기예보 API 신청. 승인에 시간이 걸리므로 미리 신청. **1일차 실습에는 필요 없다**고 명시.

- [ ] **Step 2: `public/prep/day2.html` 작성**

- **텔레그램 앱 설치** (휴대폰 또는 데스크톱)
- **BotFather로 봇 만들기** — 텔레그램에서 `@BotFather` 검색 → `/newbot` → 봇 이름 입력 → 사용자명 입력(반드시 `bot`으로 끝나야 함) → 토큰 발급. 캡처 자리 3개.
- **내 chat id 알아내기** — 만든 봇에게 아무 메시지나 보낸 뒤 `https://api.telegram.org/bot<토큰>/getUpdates` 접속 → `"chat":{"id":숫자}` 확인. 캡처 자리 2개. 초보자가 가장 많이 막히는 지점이므로 단계를 잘게 쪼갠다.
- **자주 막히는 곳** `.note.warn` — 봇에게 먼저 말을 걸지 않으면 `getUpdates` 결과가 비어 있다. 기관 네트워크에서 텔레그램이 차단될 수 있으니 휴대폰 데이터로 시도.

- [ ] **Step 3: 검사 실행**

```bash
python tools/check_site.py
```

Expected: FAIL이지만 `prep/day1.html`, `prep/day2.html` 관련 끊어진 링크는 사라지고 `day1/*`, `day2/*` 12건만 남는다.

- [ ] **Step 4: 커밋**

```bash
git add public/prep/
git commit -m "feat: 1일차/2일차 준비물 페이지 작성

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: 1강 참조 구현

**Files:**
- Create: `public/day1/01.html`

**Interfaces:**
- Produces: **이후 11개 페이지가 그대로 복제할 페이지 템플릿.** 섹션 순서, 클래스 사용법, 플로우 마크업, 캡처 자리 형식이 여기서 확정된다.

이 Task의 산출물이 톤·디자인 확인의 대상이다. 다음 페이지들을 만들기 전에 사용자 승인을 받는다.

- [ ] **Step 1: `public/day1/01.html` 작성**

전체 골격:

```html
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>01 첫 워크플로우 — 공무원을 위한 n8n</title>
<link rel="stylesheet" href="../assets/style.css">
<link rel="stylesheet" href="../assets/flow.css">
</head>
<body>
<main class="wrap">

  <nav class="crumb"><a href="../index.html">목차</a> › 1일차 › 01</nav>

  <header class="page-head">
    <h1>01 첫 워크플로우</h1>
    <p class="sub">n8n에서 무언가를 만들고 실행해봅니다</p>
  </header>

  <section class="sec" id="goal">
    <h2 class="sec-title">이번 시간에 만들 것</h2>
    <p>실행 버튼을 누르면 <code class="val">인사말</code>이라는 값이 만들어지는,
       가장 단순한 워크플로우를 만듭니다.</p>
    <figure class="capture">
      <div class="capture-cap">[그림 1-1] 완성된 모습</div>
      <div class="capture-guide">캡처 위치: 노드 2개가 연결된 캔버스 전체</div>
    </figure>
  </section>

  <section class="sec" id="flow">
    <h2 class="sec-title">지금까지의 흐름</h2>
    <div class="flow">
      <div class="flow-node is-new"><span class="t">수동 실행</span><span class="k">트리거</span></div>
      <div class="flow-arrow">▶</div>
      <div class="flow-node is-new"><span class="t">값 만들기</span><span class="k">Set</span></div>
    </div>
    <p class="flow-legend"><span class="sw"></span> 이번 시간에 새로 만드는 노드</p>
  </section>

  <section class="sec" id="why">
    <h2 class="sec-title">왜 이게 필요한가</h2>
    <p>모든 자동화는 "언제 시작할지"와 "무엇을 할지" 두 가지로 이뤄집니다.
       n8n에서는 앞의 것을 <b>트리거</b>, 뒤의 것을 <b>노드</b>라고 부릅니다.
       지금은 가장 단순한 형태 — 내가 버튼을 누르면(트리거) 값을 하나 만든다(노드) — 를 만들어
       이 구조에 익숙해집니다.</p>
  </section>

  <section class="sec" id="steps">
    <h2 class="sec-title">따라하기</h2>
    <ol class="steps">
      <li><span class="step-title">새 워크플로우 만들기</span>
        n8n 화면 오른쪽 위 <code class="val">Create Workflow</code> 버튼을 누릅니다.
        <figure class="capture">
          <div class="capture-cap">[그림 1-2] 새 워크플로우 만들기</div>
          <div class="capture-guide">캡처 위치: 우측 상단 버튼 주변</div>
        </figure>
      </li>
      <li><span class="step-title">트리거 추가하기</span>
        캔버스 가운데 <code class="val">Add first step…</code>을 누르고
        <code class="val">Trigger manually</code>를 고릅니다.
        <span class="hint">직접 실행 버튼을 눌러 시작하는 트리거입니다.</span>
      </li>
      <li><span class="step-title">Set 노드 붙이기</span>
        방금 만든 노드 오른쪽 <code class="val">+</code>를 누르고 <code class="val">Edit Fields (Set)</code>를 고릅니다.
      </li>
      <li><span class="step-title">값 채우기</span>
        이름에 <code class="val">인사말</code>, 값에 <code class="val">안녕하세요, 홍길동님</code>을 넣습니다.
      </li>
      <li><span class="step-title">이름 바꾸기</span>
        노드 이름을 <code class="val">값 만들기</code>로 바꿉니다.
        <span class="hint">노드가 많아지면 이름이 곧 설명서가 됩니다.</span>
      </li>
    </ol>
  </section>

  <section class="sec" id="verify">
    <h2 class="sec-title">실행하고 확인하기</h2>
    <p>아래쪽 <code class="val">Execute workflow</code>를 누릅니다.
       노드마다 초록 체크가 뜨고, <code class="val">값 만들기</code>를 누르면 오른쪽에
       <code class="val">인사말: 안녕하세요, 홍길동님</code>이 보이면 성공입니다.</p>
  </section>

  <section class="sec" id="trouble">
    <h2 class="sec-title">안 될 때</h2>
    <p><b>실행 버튼이 안 보입니다</b> — 트리거 노드가 없으면 실행할 수 없습니다. 2단계를 다시 확인하세요.</p>
    <p><b>두 노드가 선으로 이어지지 않았습니다</b> — 노드 오른쪽 동그라미를 끌어다 다음 노드 왼쪽에 놓으면 연결됩니다.</p>
    <p><b>값이 비어 보입니다</b> — 이름 칸과 값 칸을 바꿔 넣지 않았는지 확인하세요.</p>
  </section>

  <section class="sec" id="download">
    <h2 class="sec-title">이번 단계 워크플로우 받기</h2>
    <p>따라오다 막혔다면 이 파일을 받아 n8n에서 불러오면 이어서 진행할 수 있습니다.</p>
    <a class="dl" href="../downloads/day1-01.json" download>
      워크플로우 내려받기 <span class="dl-name">day1-01.json</span>
    </a>
  </section>

  <nav class="pager">
    <a href="../prep/day1.html">← 준비물</a>
    <a href="02.html">02 데이터 흐름과 표현식 →</a>
  </nav>

</main>
</body>
</html>
```

- [ ] **Step 2: 다운로드 자리표시 JSON 생성**

`check_site.py`가 `../downloads/day1-01.json` 링크를 검사하므로 빈 파일이라도 있어야 한다. 2단계에서 실제 워크플로우로 교체한다.

```bash
cd "D:/Github/n8n_WS/PublicFlow"
printf '{"name":"[공무원] 1일차 01 첫 워크플로우","nodes":[],"connections":{}}' > public/downloads/day1-01.json
```

- [ ] **Step 3: 검사 실행**

```bash
python tools/check_site.py
```

Expected: FAIL, 남은 오류는 `day1/02.html`~`08.html`, `day2/p1.html`~`p4.html` 11건뿐.

- [ ] **Step 4: 브라우저로 눈으로 확인**

`public/day1/01.html`을 브라우저로 열어 다음을 확인한다.

- 단계 번호 동그라미가 세로선 위에 정렬되는가
- 플로우 노드 2개가 주황색으로 강조되는가
- 캡처 자리표시자가 점선 박스로 보이는가
- 창을 좁혀도 가로 스크롤이 생기지 않는가(플로우 내부만 스크롤)
- 다크 모드에서 글자가 읽히는가

- [ ] **Step 5: 커밋**

```bash
git add public/day1/01.html public/downloads/day1-01.json
git commit -m "feat: 1강 참조 구현 - 강의 페이지 템플릿 확정

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

- [ ] **Step 6: 사용자 승인 받기**

여기서 멈추고 톤·디자인 확인을 받는다. 승인 전에는 Task 6으로 넘어가지 않는다.

---

### Task 6: 나머지 11개 페이지 뼈대

**Files:**
- Create: `public/day1/02.html` ~ `08.html` (7개)
- Create: `public/day2/p1.html` ~ `p4.html` (4개)
- Create: `public/downloads/day1-02.json` ~ `day1-08.json`, `day2-p1.json` ~ `day2-p4.json` (11개)

**Interfaces:**
- Consumes: Task 5가 확정한 템플릿 구조
- Produces: 7섹션을 모두 갖추고 링크가 이어진 12페이지 완결 사이트

각 페이지는 Task 5의 구조를 그대로 따르되, `#steps`·`#verify`·`#trouble` 본문은 한 줄 안내로 비워둔다. 제목·플로우·다운로드 링크·페이저는 실제 값으로 채운다. 본문은 2단계 계획에서 작성한다.

- [ ] **Step 1: 각 페이지의 확정 값 표 준비**

| 파일 | 제목 | 부제 | 플로우 노드(왼→오, `is-new` 표시) | 이전 | 다음 |
|---|---|---|---|---|---|
| `day1/02.html` | 02 데이터 흐름과 표현식 | 앞 노드의 값을 가져다 씁니다 | 수동 실행·값 만들기 / **값 가져오기** | `01.html` | `03.html` |
| `day1/03.html` | 03 구글 시트에 자동 기록 | 만든 데이터를 시트에 쌓습니다 | 수동 실행·샘플 민원 / **시트에 기록** | `02.html` | `04.html` |
| `day1/04.html` | 04 이메일 자동 발송 | 접수 내용을 담당자에게 보냅니다 | …·시트에 기록 / **접수 메일 보내기** | `03.html` | `05.html` |
| `day1/05.html` | 05 캘린더 일정 자동 생성 | 3일 뒤 처리 마감을 잡습니다 | …·접수 메일 / **처리 마감 일정** | `04.html` | `06.html` |
| `day1/06.html` | 06 AI 안내문 자동 생성 | Gemini가 안내문 초안을 씁니다 | …·처리 마감 / **AI 안내문 작성** | `05.html` | `07.html` |
| `day1/07.html` | 07 조건에 따라 나누기 | 민원 종류로 담당자를 가릅니다 | …·AI 안내문 / **생활인가?** · **담당자 분기** | `06.html` | `08.html` |
| `day1/08.html` | 08 입력 폼으로 실제 접수받기 | 수동 실행을 폼으로 바꿉니다 | **민원 입력 폼** / 나머지 전부 | `07.html` | `../day2/p1.html` |
| `day2/p1.html` | P1 공문서 요약 서비스 | PDF를 올리면 요약을 보내줍니다 | 폼(PDF) ▶ 텍스트 추출 ▶ AI 요약 ▶ 텔레그램 | `../day1/08.html` | `p2.html` |
| `day2/p2.html` | P2 매일 아침 민원 브리핑 봇 | 정해진 시각에 스스로 실행됩니다 | 매일 9시 ▶ 시트 읽기 ▶ AI 브리핑 ▶ 메일·텔레그램 | `p1.html` | `p3.html` |
| `day2/p3.html` | P3 AI 민원 자동 분류·답변 초안 | AI가 분류하고 초안을 씁니다 | 폼 ▶ AI 분류·답변 ▶ 시트 기록 | `p2.html` | `p4.html` |
| `day2/p4.html` | P4 날씨 알리미 | 공공데이터를 받아 알려줍니다 | 매일 7시 ▶ 기상청 API ▶ 메시지 가공 ▶ 텔레그램 | `p3.html` | `../index.html` |

`day2/*.html`의 CSS 경로도 `../assets/`로 동일하다.

- [ ] **Step 2: 11개 페이지 생성**

각 파일은 Task 5의 HTML을 복제해 제목·부제·플로우·페이저·다운로드 파일명을 위 표대로 바꾼다. 본문 3개 섹션은 다음으로 채운다.

```html
  <section class="sec" id="steps">
    <h2 class="sec-title">따라하기</h2>
    <p class="hint">작성 예정입니다.</p>
  </section>

  <section class="sec" id="verify">
    <h2 class="sec-title">실행하고 확인하기</h2>
    <p class="hint">작성 예정입니다.</p>
  </section>

  <section class="sec" id="trouble">
    <h2 class="sec-title">안 될 때</h2>
    <p class="hint">작성 예정입니다.</p>
  </section>
```

`#goal`, `#why`는 표의 부제를 풀어 한두 문장으로 실제 작성한다. 빈 페이지처럼 보이지 않게 하기 위해서다.

`TODO`·`TBD`는 절대 쓰지 않는다. `check_site.py`가 거부한다.

- [ ] **Step 3: 다운로드 자리표시 JSON 11개 생성**

```bash
cd "D:/Github/n8n_WS/PublicFlow/public/downloads"
for f in day1-02 day1-03 day1-04 day1-05 day1-06 day1-07 day1-08 day2-p1 day2-p2 day2-p3 day2-p4; do
  printf '{"name":"[공무원] %s","nodes":[],"connections":{}}' "$f" > "$f.json"
done
```

- [ ] **Step 4: 검사 실행 — 이번엔 통과해야 함**

```bash
cd "D:/Github/n8n_WS/PublicFlow"
python tools/check_site.py
```

Expected: PASS — `OK: 15 pages, N links checked`, exit 0.

이것이 이 계획의 완료 조건이다.

- [ ] **Step 5: 페이저 왕복 확인**

`index.html`에서 시작해 `01 → 02 → … → 08 → p1 → … → p4 → index`로 한 바퀴 돌아 끊기는 곳이 없는지 브라우저로 확인한다.

- [ ] **Step 6: 커밋**

```bash
git add public/day1/ public/day2/ public/downloads/
git commit -m "feat: 나머지 11개 강의 페이지 뼈대와 다운로드 자리표시 추가

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: 캡처 삽입 체계

**Files:**
- Create: `public/assets/img/.gitkeep`
- Create: `tools/apply_captures.py`
- Create: `docs/capture-guide.md`
- Modify: 모든 `figure.capture`를 가진 페이지 (id 부여)
- Modify: `public/day1/01.html` (5단계 문구 보완)

**Interfaces:**
- Produces: `python tools/apply_captures.py --list` — 촬영해야 할 그림 목록을 표로 출력
- Produces: `python tools/apply_captures.py` — `public/assets/img/`에 있는 이미지를 대응하는 `figure.capture` 안에 `<img>`로 끼워 넣는다. 이미 끼워진 것은 갱신한다(멱등).

**배경.** 1단계 종료 시점에 강의에 필요한 화면 캡처는 하나도 확보할 수 없다. n8n 인스턴스·Google AI Studio·공공데이터포털·텔레그램 모두 사용자 계정 로그인 뒤에 있고, 더 근본적으로 강의 캡처 대부분은 *워크플로우를 만드는 중간 화면*이라 n8n에 실제로 워크플로우를 만들어야 찍을 수 있다. 그것은 승인 전까지 금지된 작업이다. 따라서 이 Task는 캡처를 **확보**하지 않고, 나중에 **끼워 넣기 쉽게** 만든다.

사용자가 해야 할 일이 "이미지 파일을 정해진 이름으로 폴더에 넣고 명령 하나 실행"으로 끝나야 한다. HTML을 손으로 고치게 하면 안 된다.

- [ ] **Step 1: 그림 id 체계 정의와 부여**

모든 `figure.capture`에 ASCII 슬러그 id를 붙인다. 한글 캡션은 그대로 두고, id와 파일명만 영문으로 간다(파일명 규칙 준수).

| 페이지 | id 형식 | 예 |
|---|---|---|
| `prep/day1.html` | `fig-prep1-N` | `fig-prep1-3` |
| `prep/day2.html` | `fig-prep2-N` | `fig-prep2-1` |
| `day1/NN.html` | `fig-d1-NN-N` | `fig-d1-03-2` |
| `day2/pN.html` | `fig-d2-pN-N` | `fig-d2-p1-1` |

번호는 각 페이지의 기존 캡션 번호(`[그림 준1-3]`, `[그림 3-2]`)와 1:1로 맞춘다. 캡션 텍스트는 바꾸지 않는다.

- [ ] **Step 2: `tools/apply_captures.py` 작성**

표준 라이브러리만 쓴다. 동작:

1. `public/assets/img/` 를 훑어 `fig-*.png` / `fig-*.jpg` / `fig-*.webp` 를 모은다
2. `public/**/*.html` 에서 `<figure class="capture" id="fig-...">` 를 찾는다
3. id가 일치하는 이미지가 있으면, 그 figure 안의 `<div class="capture-guide">…</div>` 를 `<img src="…" alt="캡션 텍스트">` 로 바꾼다
4. 이미 `<img>` 가 들어 있으면 `src` 만 갱신한다 (멱등)
5. 대응 이미지가 없는 figure는 건드리지 않는다 — 자리표시자 그대로 남는다

`src` 는 각 페이지 위치 기준 상대경로로 쓴다(`public/day1/` 에서는 `../assets/img/…`).

`--list` 옵션은 전체 figure 목록을 `id | 페이지 | 캡션 | 촬영 안내 | 상태(대기/완료)` 표로 출력한다.

`--check` 옵션은 `public/assets/img/` 에 있는데 대응하는 figure id가 없는 이미지를 경고한다(오타로 넣은 파일 잡기).

- [ ] **Step 3: `docs/capture-guide.md` 작성**

사용자가 읽을 문서다. 다음을 담는다.

- 저장 위치: `public/assets/img/`
- 파일명: figure id 그대로 + 확장자 (`fig-d1-03-2.png`)
- 권장 형식: PNG, 가로 1200~1600px, 개인정보·API 키가 찍히지 않도록 주의
- 넣는 방법: 파일을 넣고 `python tools/apply_captures.py` 실행. HTML을 직접 고칠 필요 없음
- 다시 찍었을 때: 같은 이름으로 덮어쓰고 다시 실행하면 갱신됨
- 전체 목록: `python tools/apply_captures.py --list` 로 확인

문서 끝에 현재 촬영 대상 전체 목록을 표로 붙인다.

- [ ] **Step 4: `day1/01.html` 5단계 문구 보완**

"이름 바꾸기" 단계가 바꾸라고만 하고 방법을 알려주지 않는다. 다른 단계는 모두 위치를 짚어주므로 이 단계만 예외다. 노드 제목을 더블클릭해 바꾼다는 안내를 한 문장 넣는다.

- [ ] **Step 5: 검증**

```bash
cd "D:/Github/n8n_WS/PublicFlow"
python tools/apply_captures.py --list
python tools/apply_captures.py
python tools/check_site.py
```

Expected:
- `--list` 가 모든 figure를 상태 `대기` 로 출력 (아직 이미지가 하나도 없으므로)
- 인자 없는 실행이 `0개 삽입` 을 보고하고 HTML을 하나도 바꾸지 않음
- `check_site.py` 가 여전히 PASS, exit 0

이미지를 하나 임시로 넣어 삽입 → 재실행(멱등) → 삭제 후 복원까지 왕복 시험한다. 시험용 이미지는 커밋하지 않는다.

- [ ] **Step 6: 커밋**

```bash
git add public/ tools/apply_captures.py docs/capture-guide.md
git commit -m "feat: 캡처 이미지 삽입 체계와 촬영 가이드 추가

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-Review

**1. 스펙 커버리지**

| 스펙 항목 | 담당 Task |
|---|---|
| 사이트 파일 구조 (5절) | Task 1·3·4·5·6 |
| 페이지 7단 구성 (5절) | Task 5가 확정, Task 6이 복제 |
| 공통 CSS (8절 1단계) | Task 2 |
| SVG 플로우 컴포넌트 (8절 1단계) | Task 2 — **HTML+CSS로 변경**. 한글 줄바꿈과 반응형이 인라인 SVG보다 쉽다. 스펙 5절의 "SVG 플로우"는 시각적 산출물을 뜻하므로 구현 수단 변경은 요구사항을 해치지 않는다. |
| 다운로드 버튼 (8절 1단계) | Task 5·6 |
| 캡처 자리표시자 규격 (6절) | Task 5 — 스펙의 `figure.capture-todo` 대신 `figure.capture` + `.capture-guide` 사용. 나중에 실제 이미지로 교체할 때 클래스를 바꾸지 않아도 되도록 한 것이다. |
| Gemini 모델 고정·preview 함정 (4절) | Task 4 (prep/day1.html) |
| 배포 금지 (7절) | Global Constraints — 이 계획에 배포 단계 없음 |
| 기상청 API 분리 안내 (9절) | Task 4 Step 1 마지막 항목 |
| git 저장소 결정 (9절) | Task 1 Step 1에서 `git init` 수행 (로컬 전용, 원격 연결 없음) |
| 1일차 본문·2일차 본문·캡처 삽입·배포 (8절 2~5단계) | **이 계획 범위 밖.** 별도 계획으로 작성 |

**2. 자리표시자 점검**

계획 본문에 `TBD`/`TODO`는 없다. Task 6이 만드는 페이지의 "작성 예정입니다"는 의도된 최종 문구이며 `check_site.py`의 금지 토큰 목록에 걸리지 않는다.

**3. 이름 일관성**

- 검사 명령은 전 구간 `python tools/check_site.py`로 통일 (`python3` 아님)
- 필수 섹션 id 7개는 스크립트 `REQUIRED_SECTIONS`와 Task 5 HTML, Task 6 템플릿에서 모두 `goal, flow, why, steps, verify, trouble, download`로 일치
- 다운로드 파일명은 `day1-NN.json` / `day2-pN.json` 형식으로 Task 5·6에서 일치
- CSS 클래스는 Task 2가 정의한 것만 Task 3~6에서 사용

**4. 발견해 고친 것**

Task 3의 `index.html`이 12개 강의 페이지를 링크하는데 그 파일들은 Task 5·6에서 만들어진다. Task 3 시점에 검사가 실패하는 것이 정상임을 각 Task의 Expected에 명시해, 실행자가 실패를 버그로 오해하지 않도록 했다.
