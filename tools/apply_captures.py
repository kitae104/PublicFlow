"""캡처 이미지를 강의 페이지의 figure.capture 안에 끼워 넣는다.

사용법:
  python tools/apply_captures.py            촬영된 이미지를 대응 figure에 삽입/갱신 (멱등)
  python tools/apply_captures.py --list     전체 figure 목록과 상태를 표로 출력
  python tools/apply_captures.py --check    public/assets/img/ 에 있는데 대응하는
                                             figure id가 없는 이미지(오타 등)를 경고

이미지 저장 위치: public/assets/img/
파일명 규칙:      figure id 그대로 + 확장자 (fig-d1-03-2.png / .jpg / .webp)

주의: python3 는 이 머신에서 스토어 스텁이므로 반드시 python 을 쓸 것.
"""
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
IMG_DIR = PUBLIC / "assets" / "img"

IMG_EXTS = (".png", ".jpg", ".webp")

FIGURE_RE = re.compile(
    r'<figure class="capture" id="(?P<id>fig-[a-z0-9-]+)">(?P<body>.*?)</figure>',
    re.DOTALL,
)
CAPTION_RE = re.compile(r'<div class="capture-cap">(?P<cap>.*?)</div>', re.DOTALL)
GUIDE_RE = re.compile(r'(?P<indent>[ \t]*)<div class="capture-guide">(?P<guide>.*?)</div>', re.DOTALL)
IMG_TAG_RE = re.compile(r'<img\b[^>]*>')
COMMENT_RE = re.compile(r'<!--\s*(?P<text>.*?)\s*-->', re.DOTALL)
SRC_ATTR_RE = re.compile(r'src\s*=\s*"[^"]*"')
CAP_PREFIX_RE = re.compile(r'^\s*\[그림[^\]]*\]\s*')


def html_files():
    return sorted(PUBLIC.rglob("*.html"))


def find_images():
    """id -> 이미지 경로. 같은 id에 확장자가 여러 개면 conflicts에 담는다."""
    by_id = {}
    if IMG_DIR.is_dir():
        for p in sorted(IMG_DIR.iterdir()):
            if p.is_file() and p.suffix.lower() in IMG_EXTS and p.stem.startswith("fig-"):
                by_id.setdefault(p.stem, []).append(p)
    images, conflicts = {}, {}
    for fig_id, paths in by_id.items():
        if len(paths) > 1:
            conflicts[fig_id] = paths
        else:
            images[fig_id] = paths[0]
    return images, conflicts


def make_alt(caption: str) -> str:
    stripped = CAP_PREFIX_RE.sub("", caption).strip()
    return stripped if stripped else caption.strip()


def rel_src(page: Path, image: Path) -> str:
    return os.path.relpath(image, start=page.parent).replace("\\", "/")


def scan_figures():
    """모든 figure.capture를 순서대로 모은다. 반환: (figures, dup_ids)"""
    figures = []
    seen_ids = {}
    dup_ids = set()
    for page in html_files():
        text = page.read_text(encoding="utf-8")
        for m in FIGURE_RE.finditer(text):
            fig_id = m.group("id")
            body = m.group("body")
            cap_m = CAPTION_RE.search(body)
            caption = cap_m.group("cap").strip() if cap_m else ""
            guide_m = GUIDE_RE.search(body)
            has_img = bool(IMG_TAG_RE.search(body))
            if guide_m:
                guide_text = guide_m.group("guide").strip()
            else:
                cm = COMMENT_RE.search(body)
                guide_text = cm.group("text").strip() if cm else ""
            info = {
                "id": fig_id,
                "page": page.relative_to(ROOT).as_posix(),
                "caption": caption,
                "guide": guide_text,
                "filled": has_img,
            }
            figures.append(info)
            seen_ids.setdefault(fig_id, []).append(info["page"])
    for fig_id, pages in seen_ids.items():
        if len(pages) > 1:
            dup_ids.add(fig_id)
    return figures, dup_ids


def cmd_list():
    figures, dup_ids = scan_figures()
    print("id | 페이지 | 캡션 | 촬영 안내 | 상태")
    for f in figures:
        status = "완료" if f["filled"] else "대기"
        dup_flag = " (중복id!)" if f["id"] in dup_ids else ""
        print(f'{f["id"]}{dup_flag} | {f["page"]} | {f["caption"]} | {f["guide"]} | {status}')
    waiting = sum(1 for f in figures if not f["filled"])
    done = len(figures) - waiting
    print(f"\n총 {len(figures)}개 — 완료 {done}개, 대기 {waiting}개")
    if dup_ids:
        print(f"경고: id 중복 {len(dup_ids)}건 -> {', '.join(sorted(dup_ids))}")
    return 0


def cmd_check():
    images, conflicts = find_images()
    figures, _ = scan_figures()
    known_ids = {f["id"] for f in figures}
    orphans = sorted(set(images) - known_ids)
    if not IMG_DIR.is_dir():
        print(f"public/assets/img/ 폴더가 없습니다: {IMG_DIR}")
        return 0
    if orphans:
        print("경고: 대응하는 figure id가 없는 이미지 (오타 확인)")
        for fig_id in orphans:
            print(f"  - {images[fig_id].name}")
    else:
        print("대응 figure 없는 이미지 없음")
    if conflicts:
        print("경고: 같은 id에 확장자가 여러 개인 이미지 (하나만 남기세요)")
        for fig_id, paths in sorted(conflicts.items()):
            names = ", ".join(p.name for p in paths)
            print(f"  - {fig_id}: {names}")
    return 0


def transform_body(fig_id, body, page, images, conflicts, dup_ids):
    """(new_body, action) 반환. action: insert/update/unchanged/skip_*"""
    if fig_id in dup_ids:
        return body, "skip_dup"
    if fig_id in conflicts:
        return body, "skip_conflict"
    image = images.get(fig_id)
    if image is None:
        return body, "skip_no_image"

    src = rel_src(page, image)
    img_m = IMG_TAG_RE.search(body)
    if img_m:
        old_tag = img_m.group(0)
        if SRC_ATTR_RE.search(old_tag):
            new_tag = SRC_ATTR_RE.sub(f'src="{src}"', old_tag, count=1)
        else:
            new_tag = old_tag.replace("<img", f'<img src="{src}"', 1)
        if new_tag == old_tag:
            return body, "unchanged"
        new_body = body[: img_m.start()] + new_tag + body[img_m.end() :]
        return new_body, "update"

    guide_m = GUIDE_RE.search(body)
    if guide_m:
        cap_m = CAPTION_RE.search(body)
        caption = cap_m.group("cap").strip() if cap_m else ""
        alt = make_alt(caption)
        indent = guide_m.group("indent")
        guide_text = guide_m.group("guide").strip()
        replacement = f'{indent}<!-- {guide_text} -->\n{indent}<img src="{src}" alt="{alt}">'
        new_body = body[: guide_m.start()] + replacement + body[guide_m.end() :]
        return new_body, "insert"

    return body, "skip_unrecognized"


def cmd_apply():
    images, conflicts = find_images()
    _, dup_ids = scan_figures()

    counts = {"insert": 0, "update": 0, "unchanged": 0, "skip_no_image": 0,
              "skip_conflict": 0, "skip_dup": 0, "skip_unrecognized": 0}
    changed_files = 0

    for page in html_files():
        text = page.read_text(encoding="utf-8")

        def repl(m, page=page):
            fig_id = m.group("id")
            body = m.group("body")
            new_body, action = transform_body(fig_id, body, page, images, conflicts, dup_ids)
            counts[action] += 1
            return f'<figure class="capture" id="{fig_id}">{new_body}</figure>'

        new_text = FIGURE_RE.sub(repl, text)
        if new_text != text:
            page.write_text(new_text, encoding="utf-8")
            changed_files += 1

    print(f"결과: {counts['insert']}개 삽입, {counts['update']}개 갱신, "
          f"{counts['unchanged']}개 변경없음, {counts['skip_no_image']}개 대기(이미지 없음)")
    print(f"수정된 파일: {changed_files}개")

    if conflicts:
        print("경고: 같은 id에 확장자가 여러 개라 건너뛴 이미지 (하나만 남기세요)")
        for fig_id, paths in sorted(conflicts.items()):
            print(f"  - {fig_id}: {', '.join(p.name for p in paths)}")
    if dup_ids:
        print(f"경고: HTML에 같은 id가 중복 사용되어 건너뛰었습니다 -> {', '.join(sorted(dup_ids))}")
    if counts["skip_unrecognized"]:
        print(f"경고: 형식을 알아볼 수 없는 figure {counts['skip_unrecognized']}건 (직접 확인 필요)")

    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        return cmd_apply()
    if args == ["--list"]:
        return cmd_list()
    if args == ["--check"]:
        return cmd_check()
    print("사용법: python tools/apply_captures.py [--list|--check]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
