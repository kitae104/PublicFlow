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

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
