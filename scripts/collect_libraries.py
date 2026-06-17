"""
E-1: 정보나루(data4library)에서
  1) 대상 도서관 정보  -> data/libraries.json
  2) 도서관별 인기대출도서 -> data/popular.json
를 받아 저장한다.

실행 (venv 켠 상태, first_pjt 폴더에서):
    python scripts/collect_libraries.py
필요: .env 의 LIBRARY_API_KEY
"""
import os
import json
import time
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

# --- 경로 / 키 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # first_pjt
DATA_DIR = os.path.join(BASE_DIR, "data")
load_dotenv(os.path.join(BASE_DIR, ".env"))          # .env 읽기 (배운 방식)
API_KEY = os.environ.get("LIBRARY_API_KEY")

# --- 설정 ---
# 대상 도서관 코드 (★열린 결정: 실제 자치구 도서관 코드로 교체.
#  정보나루 사이트 또는 libSrch(region 파라미터)로 코드를 확인해 넣으세요.)
TARGET_LIB_CODES = ["111014", "111086", "111257"]

# 인기대출 집계 기간 = 최근 30일
END_DT = date.today()
START_DT = END_DT - timedelta(days=30)
PAGE_SIZE = 200  # 도서관당 인기대출 상위 N권

LIB_INFO_URL = "http://data4library.kr/api/libSrch"            # 도서관 정보
POPULAR_URL = "http://data4library.kr/api/loanItemSrchByLib"   # 도서관별 인기대출


def fetch_json(url, params):
    """GET 후 JSON 반환. HTTP 에러 또는 정보나루 본문 에러(키 미승인 등)면 알리고 예외."""
    res = requests.get(url, params=params, timeout=20)
    if not res.ok:
        print(f"   [HTTP {res.status_code}] {res.text[:300]}")
        res.raise_for_status()
    data = res.json()
    # 정보나루는 키 미승인 등도 HTTP 200 + 본문 error로 준다 → 잡아서 실패 처리
    err = data.get("response", {}).get("error") if isinstance(data, dict) else None
    if err:
        raise RuntimeError(err)
    return data


def main():
    if not API_KEY:
        print("[중단] .env에서 LIBRARY_API_KEY를 찾을 수 없습니다.")
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    libraries, popular = [], []

    for code in TARGET_LIB_CODES:
        print(f"[수집] 도서관 {code} ...")
        try:
            # 1) 도서관 정보
            lib = fetch_json(LIB_INFO_URL, {
                "authKey": API_KEY,
                "libCode": code,
                "format": "json",
            })
            libraries.append({"libCode": code, "data": lib})

            # 2) 도서관별 인기대출 (최근 30일, 상위 PAGE_SIZE권)
            pop = fetch_json(POPULAR_URL, {
                "authKey": API_KEY,
                "libCode": code,
                "startDt": START_DT.isoformat(),
                "endDt": END_DT.isoformat(),
                "pageSize": PAGE_SIZE,
                "format": "json",
            })
            popular.append({"libCode": code, "data": pop})
            print("   OK")
            time.sleep(0.5)  # 호출 제한 배려
        except Exception as e:
            print(f"   [실패] {code}: {e}")

    with open(os.path.join(DATA_DIR, "libraries.json"), "w", encoding="utf-8") as f:
        json.dump(libraries, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA_DIR, "popular.json"), "w", encoding="utf-8") as f:
        json.dump(popular, f, ensure_ascii=False, indent=2)

    print(f"[완료] data/libraries.json ({len(libraries)}곳) · data/popular.json ({len(popular)}곳)")


if __name__ == "__main__":
    main()
