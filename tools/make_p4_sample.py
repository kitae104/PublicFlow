"""2일차 P4 실습용 가상 집행내역 엑셀 생성.

출력: public/downloads/day2-p4-sample.xlsx
오류를 일부러 심어둔 가상 데이터다. 실제 인물·부서·금액과 무관하다.

  - 한도 초과  : 1건 100,000원 초과 (4건)
  - 증빙 누락  : 증빙번호 칸이 빈 건 (5건)
  - 중복 결제  : 사용일·사용자·항목·금액이 모두 같은 건이 두 번 (2쌍, 도전 과제용)

사용법: python tools/make_p4_sample.py
"""
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = Path(__file__).resolve().parent.parent / "public" / "downloads" / "day2-p4-sample.xlsx"

HEADER = ["사용일", "부서", "사용자", "항목", "금액", "증빙번호"]
DEPT = "복지정책과"

# (사용일, 사용자, 항목, 금액) — 정상 건. 증빙번호는 아래에서 순번으로 붙인다.
NORMAL = [
    ("2026-09-01", "한지우", "회의 다과", 38000),
    ("2026-09-01", "오서윤", "사무용품 구입", 27500),
    ("2026-09-02", "강민재", "출장 교통비", 21400),
    ("2026-09-02", "윤하린", "업무추진비 식비", 64000),
    ("2026-09-03", "한지우", "출장 교통비", 15800),
    ("2026-09-03", "서도윤", "사무용품 구입", 43200),
    ("2026-09-04", "오서윤", "회의 다과", 29000),
    ("2026-09-04", "강민재", "업무추진비 식비", 72000),
    ("2026-09-07", "윤하린", "출장 교통비", 33600),
    ("2026-09-07", "서도윤", "회의 다과", 41000),
    ("2026-09-08", "한지우", "업무추진비 식비", 58000),
    ("2026-09-08", "강민재", "사무용품 구입", 19800),
    ("2026-09-09", "오서윤", "출장 교통비", 27200),
    ("2026-09-09", "윤하린", "회의 다과", 35500),
    ("2026-09-10", "서도윤", "업무추진비 식비", 81000),
    ("2026-09-10", "한지우", "사무용품 구입", 52300),
    ("2026-09-11", "강민재", "회의 다과", 24000),
    ("2026-09-11", "오서윤", "업무추진비 식비", 67000),
    ("2026-09-14", "윤하린", "사무용품 구입", 31900),
    ("2026-09-14", "서도윤", "출장 교통비", 18600),
    ("2026-09-15", "한지우", "회의 다과", 46000),
    ("2026-09-15", "강민재", "업무추진비 식비", 89000),
    ("2026-09-16", "오서윤", "사무용품 구입", 22700),
    ("2026-09-16", "윤하린", "출장 교통비", 39400),
    ("2026-09-17", "서도윤", "회의 다과", 33000),
    ("2026-09-17", "한지우", "업무추진비 식비", 76000),
    ("2026-09-18", "강민재", "출장 교통비", 25100),
    ("2026-09-18", "오서윤", "회의 다과", 28500),
    ("2026-09-21", "윤하린", "업무추진비 식비", 93000),
    ("2026-09-21", "서도윤", "사무용품 구입", 36800),
    ("2026-09-22", "한지우", "출장 교통비", 17300),
    ("2026-09-22", "강민재", "회의 다과", 44000),
]

# 한도 초과 (1건 100,000원 초과)
OVER = [
    ("2026-09-05", "윤하린", "업무추진비 식비", 132000),
    ("2026-09-12", "강민재", "업무추진비 식비", 158000),
    ("2026-09-19", "서도윤", "사무용품 구입", 215000),
    ("2026-09-23", "오서윤", "회의 다과", 108000),
]

# 증빙 누락 (증빙번호를 비워둔다)
NO_EVIDENCE = [
    ("2026-09-02", "한지우", "회의 다과", 31000),
    ("2026-09-08", "서도윤", "출장 교통비", 26400),
    ("2026-09-15", "윤하린", "사무용품 구입", 48500),
    ("2026-09-18", "한지우", "업무추진비 식비", 55000),
    ("2026-09-22", "오서윤", "출장 교통비", 19200),
]

# 중복 결제: 같은 건을 두 번 올림 (2쌍). 증빙번호는 서로 다르게 붙는다.
DUPLICATE_BASE = [
    ("2026-09-10", "오서윤", "회의 다과", 36000),
    ("2026-09-17", "강민재", "사무용품 구입", 41500),
]


def build_rows():
    rows = []  # (사용일, 사용자, 항목, 금액, 증빙 있음?)
    for r in NORMAL + OVER + DUPLICATE_BASE + DUPLICATE_BASE:
        rows.append(r + (True,))
    for r in NO_EVIDENCE:
        rows.append(r + (False,))
    rows.sort(key=lambda r: (r[0], r[1]))
    out = []
    for n, (day, user, item, amount, has_ev) in enumerate(rows, start=1):
        ev = f"EV-2609-{n:03d}" if has_ev else None
        out.append([day, DEPT, user, item, amount, ev])
    return out


def main():
    rows = build_rows()
    wb = Workbook()
    ws = wb.active
    ws.title = "집행내역"
    ws.append(HEADER)
    for r in rows:
        ws.append(r)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for i, w in enumerate([12, 12, 10, 18, 12, 16], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    # 사용일은 문자열로 둔다 (엑셀 날짜 일련번호로 읽히는 문제를 피한다)
    for row in ws.iter_rows(min_row=2, max_col=1):
        row[0].number_format = "@"
    for row in ws.iter_rows(min_row=2, min_col=5, max_col=5):
        row[0].number_format = "#,##0"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)

    over = [r for r in rows if r[5] and r[4] > 100000]
    miss = [r for r in rows if not r[5]]
    print(f"저장: {OUT}")
    print(f"전체 {len(rows)}건 / 한도 초과 {len(over)}건 / 증빙 누락 {len(miss)}건")
    print("한도 초과:", [(r[0], r[2], r[4]) for r in over])
    print("증빙 누락:", [(r[0], r[2], r[3], r[4]) for r in miss])


if __name__ == "__main__":
    main()
