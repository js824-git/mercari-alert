# Mercari 신착 알리미

메루카리(jp.mercari.com)에 키워드 상품이 새로 올라오면 텔레그램으로 사진·이름·가격·링크를 보내 줍니다.
GitHub Actions(5분 주기)로 PC가 꺼져 있어도 동작하고, 같은 스크립트를 Windows 작업 스케줄러로도 돌릴 수 있습니다.

## 구조
- `mercari_watch.py` : 검색 → 새 상품 판별(seen.json) → 텔레그램 전송
- `.github/workflows/watch.yml` : 5분마다 실행, seen.json을 저장소에 다시 커밋
- `run_windows.bat` : PC 실행용 (토큰이 들어가므로 .gitignore 처리됨)

## 설정
GitHub 저장소 Settings → Secrets and variables → Actions 에
`TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `KEYWORD` 를 등록합니다.

## 주의
- 비공식 라이브러리(mercapi) 사용 — 메루카리 구조가 바뀌면 동작이 멈출 수 있습니다.
- 개인용, 낮은 빈도로만 사용하세요.
