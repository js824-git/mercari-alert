"""
메루카리 신착 알리미
- 키워드로 메루카리(jp.mercari.com)를 신착순 검색
- 처음 보는 상품만 텔레그램으로 사진 + 이름 + 가격 + 링크 전송
- GitHub Actions / Windows PC 양쪽에서 동일하게 동작

필요한 환경변수
  TELEGRAM_TOKEN    : @BotFather 에서 받은 봇 토큰
  TELEGRAM_CHAT_ID  : 내 chat_id
  KEYWORD           : 검색 키워드 (일본어 상품명 권장)
선택
  TEST_MODE=1       : 이미 본 상품이어도 최신 1건을 보내서 알림 테스트
"""

import asyncio
import html
import json
import os
import random
import sys
from pathlib import Path

import requests
from mercapi import Mercapi
from mercapi.requests import SearchRequestData

STATE_FILE = Path(__file__).with_name("seen.json")
MAX_SEEN = 500          # 기억해 둘 상품 ID 개수 (파일이 무한히 커지지 않게)
MAX_SEND_PER_RUN = 10   # 한 번 실행에 보낼 최대 알림 수 (폭주 방지)


def load_env(name: str, required: bool = True) -> str:
    value = os.environ.get(name, "").strip()
    if required and not value:
        sys.exit(f"[오류] 환경변수 {name} 가 비어 있어요.")
    return value


def load_seen() -> list[str]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return []


def save_seen(seen: list[str]) -> None:
    STATE_FILE.write_text(
        json.dumps(seen[-MAX_SEEN:], ensure_ascii=False, indent=0),
        encoding="utf-8",
    )


def item_url(item) -> str:
    # 메루카리 Shops(업체) 상품은 주소 형식이 다름
    if item.item_type == "ITEM_TYPE_BEYOND":
        return f"https://jp.mercari.com/shops/product/{item.id_}"
    return f"https://jp.mercari.com/item/{item.id_}"


def send_telegram(token: str, chat_id: str, item) -> None:
    price = "가격 미정" if item.is_no_price else f"¥{item.price:,}"
    caption = (
        f"<b>{html.escape(item.name)}</b>\n"
        f"{price}\n"
        f'<a href="{item_url(item)}">메루카리에서 보기</a>'
    )
    base = f"https://api.telegram.org/bot{token}"
    photo = item.thumbnails[0] if item.thumbnails else None

    if photo:
        r = requests.post(
            f"{base}/sendPhoto",
            data={"chat_id": chat_id, "photo": photo,
                  "caption": caption, "parse_mode": "HTML"},
            timeout=20,
        )
        if r.ok:
            return
        print(f"[경고] 사진 전송 실패, 글로만 보냄: {r.text[:200]}")

    r = requests.post(
        f"{base}/sendMessage",
        data={"chat_id": chat_id, "text": caption, "parse_mode": "HTML"},
        timeout=20,
    )
    r.raise_for_status()


async def search(keyword: str):
    m = Mercapi()
    res = await m.search(
        keyword,
        sort_by=SearchRequestData.SortBy.SORT_CREATED_TIME,
        sort_order=SearchRequestData.SortOrder.ORDER_DESC,
        status=[SearchRequestData.Status.STATUS_ON_SALE],
    )
    return res.items


def main() -> None:
    token = load_env("TELEGRAM_TOKEN")
    chat_id = load_env("TELEGRAM_CHAT_ID")
    keyword = load_env("KEYWORD")
    test_mode = os.environ.get("TEST_MODE") == "1"

    # 매번 같은 초에 요청하지 않도록 0~30초 랜덤 대기
    if not test_mode:
        import time
        time.sleep(random.uniform(0, 30))

    items = asyncio.run(search(keyword))
    print(f"검색 결과 {len(items)}건")

    seen = load_seen()
    seen_set = set(seen)
    first_run = not STATE_FILE.exists()

    if test_mode and items:
        send_telegram(token, chat_id, items[0])
        print("테스트 알림 1건 보냄")

    new_items = [it for it in items if it.id_ not in seen_set]

    if first_run:
        # 첫 실행: 지금 올라와 있는 상품은 기록만 하고 알림은 보내지 않음
        print(f"첫 실행 — 기존 상품 {len(new_items)}건 기록만 함")
    else:
        # 오래된 것부터 순서대로 보내기
        for it in reversed(new_items[:MAX_SEND_PER_RUN]):
            send_telegram(token, chat_id, it)
            print(f"알림: {it.name}")
        if len(new_items) > MAX_SEND_PER_RUN:
            print(f"[참고] 새 상품 {len(new_items)}건 중 {MAX_SEND_PER_RUN}건만 보냄")

    for it in reversed(new_items):
        seen.append(it.id_)
    save_seen(seen)


if __name__ == "__main__":
    main()
