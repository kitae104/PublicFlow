"""캡처 이미지를 강의 페이지의 figure.capture 안에 끼워 넣는다.

사용법:
  python tools/apply_captures.py            촬영된 이미지를 대응 figure에 삽입/갱신 (멱등)
  python tools/apply_captures.py --list     전체 figure 목록과 상태를 표로 출력
  python tools/apply_captures.py --check    public/assets/img/ 에 있는데 대응하는
                                             figure id가 없는 이미지(오타 등)를 경고

이미지 저장 위치: public/assets/img/
파일명 규칙:      figure id 그대로 + 확장자 (fig-d1-03-2.png / .jpg / .jpeg / .webp), 전부 소문자 권장

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

IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp")

FIGURE_RE = re.compile(
    r'<figure class="capture" id="(?P<id>fig-[a-z0-9-]+)">(?P<body>.*?)</figure>',
    re.DOTALL,
)
CAPTION_RE = re.compile(r'<div class="capture-cap">(?P<cap>.*?)</div>', re.DOTALL)
GUIDE_RE = re.compile(r'(?P<indent>[ \t]*)<div class="capture-guide">(?P<guide>.*?)</div>', re.DOTALL)
IMG_TAG_RE = re.compile(r'<img\b[^>]*>')
COMMENT_RE = re.compile(r'<!--\s*(?P<text>.*?)\s*-->', re.DOTALL)
# 안내 주석 바로 다음 줄에 이어지는 <img> — 삽입 시 만든 것과 정확히 같은 모양이어야
# 되돌리기 대상으로 인식한다 (사람이 손으로 고친 것은 건드리지 않기 위함).
COMMENT_IMG_RE = re.compile(
    r'(?P<indent>[ \t]*)<!--\s*(?P<guide>.*?)\s*-->\s*\n[ \t]*<img\b[^>]*>',
    re.DOTALL,
)
SRC_ATTR_RE = re.compile(r'src\s*=\s*"[^"]*"')
SRC_VALUE_RE = re.compile(r'src\s*=\s*"([^"]*)"')
CAP_PREFIX_RE = re.compile(r'^\s*\[그림[^\]]*\]\s*')


def html_files():
    return sorted(PUBLIC.rglob("*.html"))


def find_images():
    """public/assets/img/ 를 훑어 네 가지를 반환한다.

    images:        id(소문자 canonical) -> 이미지 경로
    conflicts:     id -> [경로, ...]  (같은 id에 확장자가 여러 개)
    case_warnings: [(경로, 소문자 canonical id), ...]  (파일명 대소문자가 규칙과 다름)
    unrecognized:  [경로, ...]  (fig-*.{png,jpg,jpeg,webp} 패턴 자체가 아닌 파일)

    id와 확장자 매칭은 대소문자를 가리지 않는다 — Fig-D1-01-2.PNG 도 fig-d1-01-2로
    인식해서 적용하되, 실제 파일의 진짜 이름(대소문자 그대로)을 src로 쓰기 때문에
    대소문자를 가리는 배포 환경에서도 깨지지 않는다. 다만 프로젝트 규칙(소문자
    케밥케이스)과 다르므로 case_warnings로 알려준다.
    """
    by_id = {}
    case_warnings = []
    unrecognized = []
    if IMG_DIR.is_dir():
        for p in sorted(IMG_DIR.iterdir()):
            if not p.is_file() or p.name == ".gitkeep":
                continue
            if p.suffix.lower() not in IMG_EXTS or not p.stem.lower().startswith("fig-"):
                unrecognized.append(p)
                continue
            canonical_id = p.stem.lower()
            if p.stem != canonical_id:
                case_warnings.append((p, canonical_id))
            by_id.setdefault(canonical_id, []).append(p)
    images, conflicts = {}, {}
    for fig_id, paths in by_id.items():
        if len(paths) > 1:
            conflicts[fig_id] = paths
        else:
            images[fig_id] = paths[0]
    return images, conflicts, case_warnings, unrecognized


def is_own_image_src(fig_id: str, src: str) -> bool:
    """src가 이 도구가 넣었을 법한, 이 figure 자신의 이미지를 가리키는지 확인.

    assets/img/ 아래, 파일명이 이 fig_id(대소문자 무시)와 같고 지원 확장자일 때만
    '우리 것'으로 본다. 조건에 안 맞으면 되돌리기 대상에서 제외한다 — 사람이
    다른 목적으로 넣은 이미지를 건드리지 않기 위함이다.
    """
    if not src:
        return False
    norm = src.replace("\\", "/")
    if "/" not in norm:
        return False
    dir_part, filename = norm.rsplit("/", 1)
    stem, ext = os.path.splitext(filename)
    if ext.lower() not in IMG_EXTS:
        return False
    if stem.lower() != fig_id:
        return False
    return dir_part.rstrip("/").endswith("assets/img")


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
    if not IMG_DIR.is_dir():
        print(f"public/assets/img/ 폴더가 없습니다: {IMG_DIR}")
        return 0

    images, conflicts, case_warnings, unrecognized = find_images()
    figures, _ = scan_figures()
    known_ids = {f["id"] for f in figures}
    orphans = sorted(set(images) - known_ids)

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
    if case_warnings:
        print("경고: 파일명 대소문자가 규칙과 다릅니다 (배포 환경에 따라 문제가 될 수 있으니 소문자로 바꾸세요)")
        for p, canonical_id in case_warnings:
            print(f'  - {p.name} -> 권장 파일명: {canonical_id}{p.suffix.lower()}')
    if unrecognized:
        print("경고: figure id 형식(fig-*.png/.jpg/.jpeg/.webp)이 아닌 파일 (오타로 잘못 넣은 것은 아닌지 확인)")
        for p in unrecognized:
            print(f"  - {p.name}")
    return 0


def transform_body(fig_id, body, page, images, conflicts, dup_ids):
    """(new_body, action, detail) 반환.

    action: insert/update/unchanged/revert/skip_no_image/skip_conflict/
            skip_dup/skip_unrecognized/skip_not_ours/skip_no_comment
    detail: skip_not_ours일 때 문제의 src 문자열, 그 외에는 None.
    """
    if fig_id in dup_ids:
        return body, "skip_dup", None
    if fig_id in conflicts:
        return body, "skip_conflict", None

    image = images.get(fig_id)
    img_m = IMG_TAG_RE.search(body)

    if image is None:
        # 대응 이미지가 없다. 이미 <img>가 들어 있다면(찍었던 사진을 지운 경우)
        # 우리가 넣은 것이 확실할 때만 자리표시자로 되돌린다.
        if img_m:
            src_m = SRC_VALUE_RE.search(img_m.group(0))
            src_val = src_m.group(1) if src_m else ""
            if not is_own_image_src(fig_id, src_val):
                return body, "skip_not_ours", src_val
            combo_m = COMMENT_IMG_RE.search(body)
            if not combo_m:
                return body, "skip_no_comment", None
            indent = combo_m.group("indent")
            guide_text = combo_m.group("guide").strip()
            replacement = f'{indent}<div class="capture-guide">{guide_text}</div>'
            new_body = body[: combo_m.start()] + replacement + body[combo_m.end() :]
            return new_body, "revert", None
        return body, "skip_no_image", None

    src = rel_src(page, image)
    if img_m:
        old_tag = img_m.group(0)
        if SRC_ATTR_RE.search(old_tag):
            new_tag = SRC_ATTR_RE.sub(f'src="{src}"', old_tag, count=1)
        else:
            new_tag = old_tag.replace("<img", f'<img src="{src}"', 1)
        if new_tag == old_tag:
            return body, "unchanged", None
        new_body = body[: img_m.start()] + new_tag + body[img_m.end() :]
        return new_body, "update", None

    guide_m = GUIDE_RE.search(body)
    if guide_m:
        cap_m = CAPTION_RE.search(body)
        caption = cap_m.group("cap").strip() if cap_m else ""
        alt = make_alt(caption)
        indent = guide_m.group("indent")
        guide_text = guide_m.group("guide").strip()
        replacement = f'{indent}<!-- {guide_text} -->\n{indent}<img src="{src}" alt="{alt}">'
        new_body = body[: guide_m.start()] + replacement + body[guide_m.end() :]
        return new_body, "insert", None

    return body, "skip_unrecognized", None


def cmd_apply():
    images, conflicts, case_warnings, unrecognized = find_images()
    _, dup_ids = scan_figures()

    counts = {"insert": 0, "update": 0, "unchanged": 0, "revert": 0,
              "skip_no_image": 0, "skip_conflict": 0, "skip_dup": 0,
              "skip_unrecognized": 0, "skip_not_ours": 0, "skip_no_comment": 0}
    changed_files = 0
    not_ours_notices = []
    no_comment_notices = []

    for page in html_files():
        text = page.read_text(encoding="utf-8")

        def repl(m, page=page):
            fig_id = m.group("id")
            body = m.group("body")
            new_body, action, detail = transform_body(fig_id, body, page, images, conflicts, dup_ids)
            counts[action] += 1
            page_rel = page.relative_to(ROOT).as_posix()
            if action == "skip_not_ours":
                not_ours_notices.append((page_rel, fig_id, detail))
            elif action == "skip_no_comment":
                no_comment_notices.append((page_rel, fig_id))
            return f'<figure class="capture" id="{fig_id}">{new_body}</figure>'

        new_text = FIGURE_RE.sub(repl, text)
        if new_text != text:
            page.write_text(new_text, encoding="utf-8")
            changed_files += 1

    print(f"결과: {counts['insert']}개 삽입, {counts['update']}개 갱신, "
          f"{counts['unchanged']}개 변경없음, {counts['revert']}개 되돌림, "
          f"{counts['skip_no_image']}개 대기(이미지 없음)")
    print(f"수정된 파일: {changed_files}개")

    if conflicts:
        print("경고: 같은 id에 확장자가 여러 개라 건너뛴 이미지 (하나만 남기세요)")
        for fig_id, paths in sorted(conflicts.items()):
            print(f"  - {fig_id}: {', '.join(p.name for p in paths)}")
    if dup_ids:
        print(f"경고: HTML에 같은 id가 중복 사용되어 건너뛰었습니다 -> {', '.join(sorted(dup_ids))}")
    if case_warnings:
        print("경고: 파일명 대소문자가 규칙과 다릅니다 (배포 환경에 따라 문제가 될 수 있으니 소문자로 바꾸세요)")
        for p, canonical_id in case_warnings:
            print(f'  - {p.name} -> 권장 파일명: {canonical_id}{p.suffix.lower()}')
    if unrecognized:
        print("경고: figure id 형식(fig-*.png/.jpg/.jpeg/.webp)이 아닌 파일이 있습니다 (오타 확인)")
        for p in unrecognized:
            print(f"  - {p.name}")
    if counts["skip_unrecognized"]:
        print(f"경고: 형식을 알아볼 수 없는 figure {counts['skip_unrecognized']}건 (직접 확인 필요)")
    if not_ours_notices:
        print("경고: 이미지는 없어졌는데, figure 안의 <img>가 이 도구가 넣은 것인지 확인할 수 없어 그대로 두었습니다")
        for page_rel, fig_id, src in not_ours_notices:
            print(f'  - {page_rel} ({fig_id}): src="{src}"')
    if no_comment_notices:
        print("경고: 이미지는 없어졌는데, 되돌릴 안내 주석을 찾을 수 없어 그대로 두었습니다 (직접 확인 필요)")
        for page_rel, fig_id in no_comment_notices:
            print(f"  - {page_rel} ({fig_id})")

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
