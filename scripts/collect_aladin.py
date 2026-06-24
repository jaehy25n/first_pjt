"""
D32: 알라딘 분야별(ItemList) 카탈로그 확장 수집.

목적: 현 카탈로그(정보나루 인기대출 564권, 문학 60% 편중)를 알라딘 분야별 베스트셀러로
      넓혀 KDC 버킷 골고루 ~2,000권으로 키운다. (DECISIONS D32-확정)

설계 포인트:
  - 알라딘은 KDC를 주지 않는다 → "어느 분야를 크롤했는지"로 KDC 버킷을 부여한다
    (CATEGORY_MAP의 kdc 값). per-book KDC 조회 없이 분야균등 + 온보딩 버킷 충족.
  - books.json에 "머지만" 한다(기존 레코드는 절대 덮어쓰지 않음, 새 isbn13만 추가)
    → load_data가 그대로 적재. 재실행 = 증분 top-up(얇은 버킷만 quota 올려 다시).
  - ⚠️ CategoryId가 틀리면 엉뚱한 책이 들어온다 → 본 수집 전 반드시 `--verify`로
    알라딘이 돌려준 categoryName이 의도한 분야와 맞는지 눈으로 확인할 것.

실행 (venv, first_pjt 폴더에서):
    python scripts/collect_aladin.py --verify    # ① 먼저: 분야 매핑 점검(쓰기 없음)
    python scripts/collect_aladin.py             # ② 본 수집 → data/books.json 머지
필요: .env 의 ALADIN_TTB_KEY
"""
import os
import sys
import json
import time
import math
import argparse
import collections

import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # first_pjt
DATA_DIR = os.path.join(BASE_DIR, "data")
load_dotenv(os.path.join(BASE_DIR, ".env"))
ALADIN_KEY = os.environ.get("ALADIN_TTB_KEY")

ITEMLIST_URL = "https://www.aladin.co.kr/ttb/api/ItemList.aspx"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
SLEEP = 0.6            # 알라딘 호출 간격(초)
MAX_PAGES = 12         # 한 카테고리에서 넘길 최대 페이지(50권/페이지) — 폭주 방지
QUERY_TYPE = "Bestseller"  # 베스트셀러 = 유명·표지/소개 풍부(검색 커버리지에도 유리)

# --- 분야 매핑(알라딘 CategoryId → KDC 버킷) + 버킷별 신규 목표 ---
# kdc  = 그 분야에서 가져온 책에 부여할 KDC 대분류(0~9)
# cid  = 알라딘 도서 CategoryId (★ --verify로 categoryName 꼭 확인)
# quota= 그 카테고리에서 새로 담을 목표 권수(dedup 후 기준)
# 문학(8)은 이미 341권이라 quota 작게. 비문학을 두텁게.
CATEGORY_MAP = [
    {"kdc": "0", "cid": 351,   "label": "컴퓨터/모바일",   "quota": 150},  # 총류(컴퓨터·정보)
    {"kdc": "1", "cid": 656,   "label": "인문학",          "quota": 180},  # 철학·심리
    {"kdc": "2", "cid": 1237,  "label": "종교/역학",       "quota": 150},  # 종교
    {"kdc": "3", "cid": 798,   "label": "사회과학",        "quota": 120},  # 사회
    {"kdc": "3", "cid": 170,   "label": "경제경영",        "quota": 80},   # 사회(경제경영)
    {"kdc": "4", "cid": 987,   "label": "과학",            "quota": 170},  # 자연과학
    {"kdc": "5", "cid": 2030,  "label": "좋은부모/가정",    "quota": 120},  # 기술과학(가정·육아) ★cid 미확인 → --verify 재확인
    {"kdc": "6", "cid": 517,   "label": "예술/대중문화",    "quota": 150},  # 예술
    {"kdc": "6", "cid": 2551,  "label": "만화",            "quota": 40},   # 예술(만화)
    {"kdc": "7", "cid": 1322,  "label": "외국어",          "quota": 130},  # 언어
    {"kdc": "8", "cid": 1,     "label": "소설/시/희곡",     "quota": 30},   # 문학(이미 충분)
    {"kdc": "5", "cid": 55890, "label": "건강/취미/요리",    "quota": 80},   # 기술과학(실용) — verify상 건강·요리·살림 우세
    {"kdc": "9", "cid": 74,    "label": "역사",            "quota": 130},  # 역사
    {"kdc": "9", "cid": 1196,  "label": "여행",            "quota": 60},   # 역사/지리(여행)
]


def fetch_list(cid, start, query_type=QUERY_TYPE, retries=2):
    """ItemList 한 페이지(최대 50권). 실패 시 backoff 재시도, 끝내 실패하면 None."""
    params = {
        "ttbkey": ALADIN_KEY, "QueryType": query_type, "SearchTarget": "Book",
        "CategoryId": cid, "Start": start, "MaxResults": 50,
        "Cover": "Big", "output": "js", "Version": "20131101",
    }
    for attempt in range(retries + 1):
        try:
            r = requests.get(ITEMLIST_URL, headers=HEADERS, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            if data.get("errorCode"):
                raise RuntimeError(f"{data.get('errorCode')} {data.get('errorMessage')}")
            return data
        except (requests.exceptions.RequestException, json.JSONDecodeError, ValueError, RuntimeError) as e:
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
            else:
                print(f"   [실패] cid={cid} start={start}: {e}")
    return None


def item_to_book(item, kdc):
    """알라딘 item → books.json 레코드(기존 스키마와 동일). kdc = 크롤 분야 버킷."""
    isbn13 = (item.get("isbn13") or "").strip()
    if not (isbn13.isdigit() and len(isbn13) == 13):
        return None
    return {
        "isbn13": isbn13,
        "title": (item.get("title") or "").strip(),
        "author": (item.get("author") or "").strip(),
        "publisher": (item.get("publisher") or "").strip(),
        "pub_year": (item.get("pubDate") or "")[:4],
        "kdc_code": kdc,                                  # 분야 버킷(정확 KDC 백필=백로그 C)
        "cover_url": (item.get("cover") or "").strip(),
        "description": (item.get("description") or "").strip(),
        "page_count": None,
    }


def load_existing():
    """기존 books.json → (레코드 리스트, isbn 집합). 없으면 빈 것."""
    path = os.path.join(DATA_DIR, "books.json")
    if not os.path.exists(path):
        return [], set()
    with open(path, encoding="utf-8") as f:
        books = json.load(f)
    return books, {b.get("isbn13") for b in books if b.get("isbn13")}


def _subcats(items, n=5):
    """샘플 item들의 '국내도서>' 다음 하위분야(중복 제거)를 모아 보여준다."""
    out = []
    for it in items[:n]:
        name = (it.get("categoryName") or "").strip()
        sub = name.split(">")[1] if name.count(">") >= 1 else (name or "?")
        if sub and sub not in out:
            out.append(sub)
    return ", ".join(out) if out else "(없음)"


def verify(probe_cids=None):
    """각 카테고리 1페이지만 받아 '실제 하위분야'와 샘플 제목 출력(쓰기 없음).
    probe_cids가 있으면 그 cid들만 정체 확인(후보 id 탐색용)."""
    print("=== 분야 매핑 점검 (item의 실제 하위분야로 cid 정체 확인) ===")
    rows = ([{"kdc": "?", "cid": c, "label": "(probe)"} for c in probe_cids]
            if probe_cids else CATEGORY_MAP)
    for ent in rows:
        data = fetch_list(ent["cid"], start=1)
        items = (data or {}).get("item") or []
        sub = _subcats(items) if items else "(응답 없음)"
        titles = " · ".join((it.get("title") or "")[:16] for it in items[:3])
        print(f"  kdc {ent['kdc']} | cid {ent['cid']:>6} ({ent['label']}) → "
              f"실제: {sub} | {len(items)}권 | 예: {titles}")
        time.sleep(SLEEP)
    print("→ '실제' 하위분야가 의도와 어긋나는 cid는 고친 뒤 본 수집. "
          "후보 id 탐색은 --probe 12345,67890")


def collect(max_total):
    if not ALADIN_KEY:
        print("[중단] .env에서 ALADIN_TTB_KEY를 찾을 수 없습니다.")
        return

    existing, seen = load_existing()
    print(f"기존 카탈로그 {len(existing)}권에서 시작 (증분 머지).")

    new_books, added_by_kdc = [], collections.Counter()
    for ent in CATEGORY_MAP:
        if len(new_books) >= max_total:
            break
        kdc, cid, quota = ent["kdc"], ent["cid"], ent["quota"]
        got = 0
        pages = min(MAX_PAGES, math.ceil(quota * 2 / 50) + 1)
        for start in range(1, pages + 1):
            if got >= quota or len(new_books) >= max_total:
                break
            data = fetch_list(cid, start)
            items = (data or {}).get("item") or []
            if not items:
                break
            for it in items:
                book = item_to_book(it, kdc)
                if not book or book["isbn13"] in seen:
                    continue
                seen.add(book["isbn13"])
                new_books.append(book)
                added_by_kdc[kdc] += 1
                got += 1
                if got >= quota or len(new_books) >= max_total:
                    break
            time.sleep(SLEEP)
        print(f"  kdc {kdc} ({ent['label']}): +{got}권 (목표 {quota})")

    if not new_books:
        print("[종료] 새로 담은 책이 없습니다. (이미 다 있거나 키/카테고리 확인 필요)")
        return

    # --- 머지: 기존은 그대로, 새 isbn만 추가 + 백업 ---
    merged = existing + new_books
    path = os.path.join(DATA_DIR, "books.json")
    if os.path.exists(path):
        os.replace(path, path + ".bak")  # 직전 books.json → books.json.bak
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    # --- 요약 + 결과 KDC 분포 ---
    dist = collections.Counter((b.get("kdc_code") or "?")[:1] for b in merged)
    nm = {"0": "총류", "1": "철학", "2": "종교", "3": "사회", "4": "자연",
          "5": "기술", "6": "예술", "7": "언어", "8": "문학", "9": "역사", "?": "미상"}
    print(f"\n[완료] 신규 {len(new_books)}권 추가 → 총 {len(merged)}권 (books.json, 백업 .bak)")
    print("  버킷별 신규:", dict(added_by_kdc))
    print("  결과 KDC 분포:")
    for k in sorted(dist, key=lambda x: -dist[x]):
        print(f"    {k} {nm.get(k, ''):4}: {dist[k]:4} ({dist[k]/len(merged)*100:4.1f}%)")
    print("\n다음: scripts/enrich_books.py(빈 소개만 네이버 보강, 선택) → "
          "embed_books(신규분 임베딩) → load_data → dumpdata fixtures.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="알라딘 분야별 카탈로그 확장(D32)")
    ap.add_argument("--verify", action="store_true",
                    help="각 분야 1페이지만 찍어 매핑 점검(쓰기 없음). 본 수집 전 먼저.")
    ap.add_argument("--probe", type=str, default=None,
                    help="콤마구분 cid들의 실제 분야만 점검(후보 id 탐색, 예: --probe 2030,1230).")
    ap.add_argument("--max", type=int, default=2000,
                    help="이번 실행에서 담을 신규 권수 상한(기본 2000).")
    args = ap.parse_args()

    if args.probe:
        verify([int(x) for x in args.probe.split(",") if x.strip()])
    elif args.verify:
        verify()
    else:
        collect(args.max)
