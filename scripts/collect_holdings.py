"""
E-3: 정보나루로
  1) 소장/대출가능(bookExist)        -> data/holdings.json  (소장 루프 끝나면 바로 저장)
       [{libCode, isbn13, has_book(Y/N), loan_available(Y/N)}]
  2) 함께대출/마니아/다독자(usageAnalysisList) -> data/coloan.json
       [{isbn13, coloan:[{isbn13,title}], mania:[...], reader:[...]}]
  + 첫 성공 응답 원본 -> data/_usage_sample.json (구조 확인용)

⚠️ 정보나루는 빠르게 많이 호출하면 일시 차단(throttle)됨 → SLEEP를 넉넉히, 실패 시 backoff 재시도.
   검증용으로 분량을 작게 시작하고, 잘 되면 상한을 올리세요.

실행 (venv 켠 상태, first_pjt 폴더에서): python scripts/collect_holdings.py
필요: .env 의 LIBRARY_API_KEY
"""
import os
import json
import time

import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # first_pjt
DATA_DIR = os.path.join(BASE_DIR, "data")
load_dotenv(os.path.join(BASE_DIR, ".env"))
API_KEY = os.environ.get("LIBRARY_API_KEY")

HOLDINGS_PER_LIB = 100   # 도서관당 인기 상위 N권만 소장 조회 (작게 시작)
COLOAN_MAX = 150         # 함께대출 분석할 고유 책 수 상한
SLEEP = 2.0             # 호출 간격(초) — throttle 방지

BOOK_EXIST_URL = "http://data4library.kr/api/bookExist"
USAGE_URL = "http://data4library.kr/api/usageAnalysisList"


def fetch(url, params, retries=2):
    """response(dict) 반환. throttle/빈응답이면 backoff 재시도, 끝내 실패하면 None."""
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()                      # throttle 시 list/빈값 → 예외 또는 dict 아님
            if isinstance(data, dict):
                resp = data.get("response", {})
                if isinstance(resp, dict) and resp.get("error"):
                    raise RuntimeError(resp["error"])
                return resp
        except (requests.exceptions.RequestException, json.JSONDecodeError, ValueError):
            pass
        if attempt < retries:
            time.sleep(5 * (attempt + 1))        # 5s, 10s 대기 후 재시도
    return None


def load_per_lib_isbns():
    with open(os.path.join(DATA_DIR, "popular.json"), encoding="utf-8") as f:
        popular = json.load(f)
    per_lib = {}
    for entry in popular:
        isbns = []
        for d in entry.get("data", {}).get("response", {}).get("docs", []):
            isbn = (d.get("doc", d).get("isbn13") or "").strip()
            if isbn:
                isbns.append(isbn)
        per_lib[entry["libCode"]] = isbns
    return per_lib


def parse_reclist(node):
    """coLoanBooks/maniaRecBooks/readerRecBooks → [{isbn13, title}].
    정보나루는 이걸 [{"book":{...}}, ...] 리스트로 준다(가끔 {"books":[...]}형태일 수도)."""
    if isinstance(node, dict):
        node = node.get("books", [])
    out = []
    for it in (node or []):
        bk = it.get("book", it) if isinstance(it, dict) else None
        if not isinstance(bk, dict):
            continue
        out.append({"isbn13": (bk.get("isbn13") or "").strip(),
                    "title": (bk.get("bookname") or "").strip()})
    return out


def main():
    if not API_KEY:
        print("[중단] .env에서 LIBRARY_API_KEY를 찾을 수 없습니다.")
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    per_lib = load_per_lib_isbns()

    # --- 1) 소장/대출가능 (이미 받았으면 건너뜀 → 재실행 때 throttle/시간 절약) ---
    holdings_path = os.path.join(DATA_DIR, "holdings.json")
    if os.path.exists(holdings_path):
        print("[소장] holdings.json 이미 있음 → 건너뜀(다시 받으려면 그 파일 삭제 후 실행).")
    else:
        holdings, fails = [], 0
        for lib, isbns in per_lib.items():
            print(f"[소장] 도서관 {lib} (상위 {HOLDINGS_PER_LIB}권)")
            for isbn in isbns[:HOLDINGS_PER_LIB]:
                resp = fetch(BOOK_EXIST_URL, {"authKey": API_KEY, "libCode": lib, "isbn13": isbn, "format": "json"})
                if resp is None:
                    fails += 1
                else:
                    result = resp.get("result", {})
                    holdings.append({"libCode": lib, "isbn13": isbn,
                                     "has_book": result.get("hasBook"),
                                     "loan_available": result.get("loanAvailable")})
                time.sleep(SLEEP)
        with open(holdings_path, "w", encoding="utf-8") as f:
            json.dump(holdings, f, ensure_ascii=False, indent=2)
        avail = sum(1 for h in holdings if h.get("loan_available") == "Y")
        print(f"   → holdings.json 저장: {len(holdings)}건(대출가능 {avail}), 실패 {fails}")

    # --- 2) 함께대출/마니아/다독자 ---
    unique, seen = [], set()
    for isbns in per_lib.values():
        for isbn in isbns:
            if isbn not in seen:
                seen.add(isbn); unique.append(isbn)
    coloan, sample_saved = [], False
    for i, isbn in enumerate(unique[:COLOAN_MAX], 1):
        resp = fetch(USAGE_URL, {"authKey": API_KEY, "isbn13": isbn, "format": "json"})
        if resp is None:
            print(f"   [건너뜀] usage {isbn} (throttle/빈응답)")
        else:
            if not sample_saved:
                with open(os.path.join(DATA_DIR, "_usage_sample.json"), "w", encoding="utf-8") as f:
                    json.dump(resp, f, ensure_ascii=False, indent=2)
                sample_saved = True
            coloan.append({"isbn13": isbn,
                           "coloan": parse_reclist(resp.get("coLoanBooks")),
                           "mania": parse_reclist(resp.get("maniaRecBooks")),
                           "reader": parse_reclist(resp.get("readerRecBooks"))})
        if i % 10 == 0:
            print(f"   함께대출 {i}/{min(len(unique), COLOAN_MAX)} ...")
        time.sleep(SLEEP)
    with open(os.path.join(DATA_DIR, "coloan.json"), "w", encoding="utf-8") as f:
        json.dump(coloan, f, ensure_ascii=False, indent=2)
    withco = sum(1 for c in coloan if c["coloan"])
    print(f"[완료] coloan.json {len(coloan)}권(함께대출有 {withco})")
    if coloan and withco == 0:
        print("※ 함께대출이 0이면 data/_usage_sample.json을 Cowork에 보내주세요(키 이름 확인).")


if __name__ == "__main__":
    main()
