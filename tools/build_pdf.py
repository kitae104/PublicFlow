"""public/ 의 강의 HTML 을 인쇄용 교재 PDF 한 권으로 묶는다.
사용: python tools/build_pdf.py   → print/PublicFlow_교재.pdf
"""
import re, sys, io
from pathlib import Path
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter
import pymupdf

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "public"
OUT = ROOT / "print" / "PublicFlow_교재.pdf"

ORDER = [
    ("사전 준비", ["prep/n8n-setup.html", "prep/day1.html", "prep/day2.html",
                  "prep/glossary.html", "prep/security.html"]),
    ("Day 1", [f"day1/0{i}.html" for i in range(1, 9)]),
    ("Day 2", [f"day2/p{i}.html" for i in range(1, 5)]),
    ("부록", ["extra/weather.html", "wrapup/my-workflow.html",
             "roadmap.html", "troubleshoot.html"]),
]

FOOTER = ('<div style="font-size:8px;width:100%;text-align:center;color:#666;">'
          '<span class="pageNumber"></span></div>')  # 임시: 병합 후 통합 쪽번호로 교체


COMPACT_CSS = """
@media print {
  body, body.lecture-mode { font-size: 10pt !important; line-height: 1.45 !important; }
  body.lecture-mode .page-head h1 { font-size: 16pt !important; }
  body.lecture-mode h2, .sec-title { font-size: 11.5pt !important; }
  body.lecture-mode h3 { font-size: 10.5pt !important; }
  .sec { break-inside: auto !important; margin-top: .45rem !important; padding-top: .45rem !important; }
  .note, ol.steps > li, pre.code-block, table.tbl, .tbl-wrap { break-inside: auto !important; }
  .note { margin: .4rem 0 !important; padding: .4rem .65rem !important; }
  ol.steps > li { margin-bottom: .3rem !important; }
  figure.capture { margin: .5rem 0 !important; break-inside: avoid; text-align: center; }
  figure.capture img, body.lecture-mode figure.capture img {
    max-width: 78% !important; max-height: 85mm !important; width: auto !important; height: auto !important;
    object-fit: contain; margin: 0 auto; display: block;
  }
  figcaption { font-size: 8.5pt !important; }
  pre, code { font-size: 8.5pt !important; }
  table.tbl th, table.tbl td { padding: .2rem .4rem !important; font-size: 9pt !important; }
  p, ul, ol { margin-top: .3rem !important; margin-bottom: .3rem !important; }
}
"""

def title_of(page):
    t = page.title()
    return re.sub(r"\s*[—–|]\s*공무원을 위한 n8n.*$", "", t).strip() or t

def main():
    writer = PdfWriter()
    toc = []  # (level, title, start_page_index)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.emulate_media(media="print")
        for part, files in ORDER:
            toc.append((1, part, len(writer.pages)))
            for f in files:
                path = PUB / f
                if not path.exists():
                    print("없음:", f); continue
                pg.goto(path.as_uri(), wait_until="networkidle")
                pg.evaluate("document.fonts.ready")
                # 접힌 details 는 인쇄에서 닫힌 채이므로 정답 제외 나머지는 펼친다
                pg.evaluate("document.querySelectorAll('details:not(.quiz-answer)').forEach(d=>d.open=true)")
                # 촬영 예정(캡처 자리표시자) figure 제거
                pg.evaluate("document.querySelectorAll('figure').forEach(f=>{if(f.querySelector('.capture-guide'))f.remove()})")
                pg.evaluate("document.querySelectorAll('.capture-guide').forEach(e=>e.remove())")
                pg.add_style_tag(content=COMPACT_CSS)
                title = title_of(pg)
                data = pg.pdf(format="A4", print_background=True,
                              margin=dict(top="12mm", bottom="15mm", left="14mm", right="14mm"),
                              prefer_css_page_size=False)
                r = PdfReader(io.BytesIO(data))
                toc.append((2, title, len(writer.pages)))
                for pgx in r.pages: writer.add_page(pgx)
                print(f"{f}: {len(r.pages)}쪽  {title}")
        # 표지
        pg.set_content("""<html><body style="font-family:'Malgun Gothic',sans-serif;text-align:center;padding-top:80mm">
        <h1 style="font-size:36pt;margin:0">공무원을 위한 n8n</h1>
        <p style="font-size:18pt;color:#444">업무 자동화 실습 교재</p></body></html>""")
        cover = PdfReader(io.BytesIO(pg.pdf(format="A4")))

        # 목차: 쪽수를 먼저 가늠(자리표시)하고 실제 번호로 다시 그린다
        def toc_pdf(offset):
            rows = []
            for lvl, t, idx in toc:
                num = idx + 1 + offset if offset is not None else 0
                cls = "p" if lvl == 1 else "c"
                rows.append(f'<div class="{cls}"><span class="t">{t}</span><span class="d"></span><span class="n">{num}</span></div>')
            html = """<html><meta charset="utf-8"><style>
            body{font-family:'Malgun Gothic',sans-serif;font-size:10.5pt;color:#111;margin:0}
            h1{font-size:20pt;margin:0 0 6mm;padding-bottom:3mm;border-bottom:2px solid #111}
            .p{font-weight:700;font-size:12pt;margin-top:5mm}
            .c{padding-left:6mm;margin-top:1.6mm}
            .p,.c{display:flex;align-items:baseline}
            .d{flex:1;border-bottom:1px dotted #888;margin:0 2mm;transform:translateY(-2px)}
            </style><body><h1>목차</h1>""" + "".join(rows) + "</body></html>"
            pg.set_content(html)
            return PdfReader(io.BytesIO(pg.pdf(format="A4", margin=dict(top="18mm", bottom="15mm", left="20mm", right="20mm"))))
        n_toc = len(toc_pdf(None).pages)
        tocr = toc_pdf(n_toc)
        assert len(tocr.pages) == n_toc
        b.close()

    final = PdfWriter()
    final.add_page(cover.pages[0])
    for pgx in tocr.pages: final.add_page(pgx)
    for pgx in writer.pages: final.add_page(pgx)
    parent = None
    for lvl, t, idx in toc:
        o = final.add_outline_item(t, idx + 1 + n_toc, parent=parent if lvl == 2 else None)
        if lvl == 1: parent = o
    buf = io.BytesIO(); final.write(buf)

    # 통합 쪽번호
    doc = pymupdf.open(stream=buf.getvalue(), filetype="pdf")
    for i, page in enumerate(doc):
        if i == 0: continue
        r = page.rect
        page.insert_textbox(pymupdf.Rect(0, r.height - 30, r.width, r.height - 10),
                            str(i), fontsize=9, fontname="helv", align=1, color=(.4, .4, .4))
    OUT.parent.mkdir(exist_ok=True)
    doc.save(OUT, garbage=3, deflate=True)
    print("완료:", OUT, f"{len(doc)}쪽", f"{OUT.stat().st_size/1e6:.1f}MB")

if __name__ == "__main__":
    main()
