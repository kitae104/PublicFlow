"""공무원 n8n 강의자료 사이트 무결성 검사.

검사 항목:
  1. 내부 링크(href/src)가 실제 존재하는 파일을 가리키는가
  2. 강의 페이지가 필수 섹션 id 7개를 <section> 요소에 모두 가지는가
  3. 금지 자리표시자 토큰이 남아있지 않은가
  4. 외부 자원(<script>, 외부 http(s)/프로토콜 상대 경로의 link/script/img/iframe/source)이 없는가
  5. public/downloads/ 의 모든 JSON이 유효하고 UTF-8 BOM이 없는가
  6. <figure class="capture" id="fig-...">의 속성 순서/형식이 정확한가

사용법:  python tools/check_site.py
주의:    python3 은 이 머신에서 스토어 스텁이므로 반드시 python 을 쓸 것.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
DOWNLOADS = PUBLIC / "downloads"

REQUIRED_SECTIONS = ["goal", "flow", "why", "steps", "verify", "trouble", "download"]
FORBIDDEN_TOKENS = ["TBD", "TODO", "FIXME", "lorem ipsum", "XXX"]

ATTR_RE = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
SECTION_TAG_RE = re.compile(r'<section\b[^>]*>', re.IGNORECASE)
ID_IN_TAG_RE = re.compile(r'id\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

SCRIPT_TAG_RE = re.compile(r'<script\b', re.IGNORECASE)
RESOURCE_TAG_RE = re.compile(r'<(link|script|img|iframe|source)\b[^>]*?/?>', re.IGNORECASE)
EXTERNAL_URL_RE = re.compile(r'^(?:https?:)?//', re.IGNORECASE)

FIGURE_TAG_RE = re.compile(r'<figure\b[^>]*>', re.IGNORECASE)
VALID_FIGURE_RE = re.compile(r'^<figure class="capture" id="fig-[a-z0-9][a-z0-9-]*">$')


def is_external(url: str) -> bool:
    if url.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return True
    return bool(urlparse(url).scheme)


def lesson_pages(pages):
    """강의 페이지만 — index 와 prep 은 7섹션 규칙에서 제외."""
    return [p for p in pages if p.parent.name in ("day1", "day2")]


def check_downloads(errors) -> None:
    if not DOWNLOADS.is_dir():
        return
    for jf in sorted(DOWNLOADS.glob("*.json")):
        rel_j = jf.relative_to(ROOT).as_posix()
        raw = jf.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            errors.append(f"{rel_j}: UTF-8 BOM이 포함되어 있습니다")
            continue
        try:
            json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            errors.append(f"{rel_j}: JSON 파싱 실패 -> {e}")


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
    lessons = set(lesson_pages(pages))

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

        # 2. 필수 섹션 id (강의 페이지만, <section> 요소 위에 있어야 함)
        if page in lessons:
            section_ids = set()
            for tag in SECTION_TAG_RE.findall(text):
                m = ID_IN_TAG_RE.search(tag)
                if m:
                    section_ids.add(m.group(1))
            missing = [s for s in REQUIRED_SECTIONS if s not in section_ids]
            if missing:
                errors.append(f"{rel}: 필수 섹션 누락 -> {', '.join(missing)}")

        # 3. 금지 토큰
        lowered = text.lower()
        for token in FORBIDDEN_TOKENS:
            if token.lower() in lowered:
                errors.append(f"{rel}: 금지 토큰 발견 -> {token}")

        # 4. 외부 자원 금지
        if SCRIPT_TAG_RE.search(text):
            errors.append(f"{rel}: <script> 태그는 금지되어 있습니다")
        for tag_m in RESOURCE_TAG_RE.finditer(text):
            tag_html = tag_m.group(0)
            tag_name = tag_m.group(1).lower()
            for attr_m in ATTR_RE.finditer(tag_html):
                val = attr_m.group(1)
                if EXTERNAL_URL_RE.match(val):
                    errors.append(f"{rel}: 외부 자원 참조 금지 -> <{tag_name}> {val}")

        # 6. figure 태그 형식 (class="capture" id="fig-..." 속성 순서 고정)
        for tag_html in FIGURE_TAG_RE.findall(text):
            if not VALID_FIGURE_RE.match(tag_html):
                errors.append(f"{rel}: figure 태그 형식이 어긋남 -> {tag_html}")

    # 5. downloads JSON 유효성
    check_downloads(errors)

    if errors:
        print(f"FAIL: {len(errors)}건")
        for e in errors:
            print("  -", e)
        return 1

    print(f"OK: {len(pages)} pages, {link_count} links checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
