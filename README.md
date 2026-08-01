# 공무원을 위한 n8n 업무 자동화

코딩 경험이 없는 공무원을 대상으로 한 이틀짜리 n8n 실습 강의 자료입니다.

**https://kitae-n8n.vercel.app**

1일차에는 워크플로우 하나를 여덟 번에 걸쳐 키워 민원 접수 시스템을 완성하고,
2일차에는 그 조각들을 조합해 실무용 자동화 네 가지를 만듭니다.

## 구성

```
public/            그대로 배포되는 정적 사이트 (빌드 도구 없음)
  index.html       목차
  prep/            준비물 — n8n 접속, 구글·Gemini, 텔레그램
  day1/            1일차 01~08강
  day2/            2일차 P1~P4
  downloads/       각 강의 완성본 워크플로우 JSON
  assets/img/      화면 캡처
docs/              작성자용 문서
tools/             캡처 삽입·링크 점검 스크립트
```

## 자주 쓰는 명령

```bash
# 캡처 넣기 — public/assets/img/에 fig-*.png 저장 후 실행
python tools/apply_captures.py

# 남은 촬영 목록 보기
python tools/apply_captures.py --list

# 링크·구조 점검
python tools/check_site.py
```

자세한 캡처 작업 방법은 [docs/capture-guide.md](docs/capture-guide.md)를 보세요.

## 배포

`main`에 푸시하면 Vercel이 자동으로 배포합니다. 별도 명령이 필요 없습니다.

## 워크플로우 JSON에 대하여

`public/downloads/`의 JSON에는 실제 자격증명이 들어 있지 않습니다. 시트 ID, API 키,
chat id 자리에는 `여기에_본인_...` 형태의 자리표시자가 들어 있으니, 내려받은 뒤
각자 값으로 바꿔서 쓰면 됩니다.
