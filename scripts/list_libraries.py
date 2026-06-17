"""
정보나루 libSrch로 서울 도서관 목록(libCode·이름·주소)을 받아
검색어가 들어간 곳만 화면에 출력하고, 전체 원본은 data/_libraries_seoul.json에 저장한다.
→ 여기서 신촌(서대문구) 도서관 3~5곳을 골라 그 libCode를
   collect_libraries.py 의 TARGET_LIB_CODES 에 넣으면 된다.

실행 (venv 켠 상태, first_pjt 폴더에서):
    python scripts/list_libraries.py            # 기본: '서대문' 포함만
    python scripts/list_libraries.py 마포        # 다른 구로 보고 싶으면 검색어 지정
"""
import os
import sys
import json

import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # first_pjt
load_dotenv(os.path.join(BASE_DIR, ".env"))
API_KEY = os.environ.get("LIBRARY_API_KEY")

REGION_SEOUL = "11"  # 정보나루 지역코드: 서울 = 11
KEYWORD = sys.argv[1] if len(sys.argv) > 1 else "마포"  # 이름/주소에 이게 들어간 것만 표시


def main():
    if not API_KEY:
        print("[중단] .env에서 LIBRARY_API_KEY를 찾을 수 없습니다.")
        return

    res = requests.get(
        "http://data4library.kr/api/libSrch",
        params={"authKey": API_KEY, "region": REGION_SEOUL, "pageSize": 1000, "format": "json"},
        timeout=30,
    )
    data = res.json()
    err = data.get("response", {}).get("error") if isinstance(data, dict) else None
    if err:
        print(f"[실패] {err}")
        return

    libs = data.get("response", {}).get("libs", [])
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    with open(os.path.join(BASE_DIR, "data", "_libraries_seoul.json"), "w", encoding="utf-8") as f:
        json.dump(libs, f, ensure_ascii=False, indent=2)

    print(f"서울 도서관 {len(libs)}곳 수신. '{KEYWORD}' 포함만 표시:\n")
    print(f"{'libCode':<10} 이름 / 주소")
    print("-" * 60)
    hit = 0
    for item in libs:
        lib = item.get("lib", item)  # 보통 {'lib': {...}} 구조
        name = lib.get("libName", "")
        addr = lib.get("address", "")
        if KEYWORD in name or KEYWORD in addr:
            print(f"{lib.get('libCode',''):<10} {name}  |  {addr}")
            hit += 1
    print("-" * 60)
    print(f"{hit}곳 매칭. (전체 원본: data/_libraries_seoul.json)")
    print("→ 신촌 근처 3~5곳을 골라 libCode를 collect_libraries.py TARGET_LIB_CODES에 넣으세요.")


if __name__ == "__main__":
    main()
