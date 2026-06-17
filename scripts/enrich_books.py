import os
import json
import time
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
load_dotenv(os.path.join(BASE_DIR, ".env"))
ALADIN_KEY = os.environ.get("ALADIN_TTB_KEY")
NAVER_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

MAX_BOOKS = 1000

def collect_unique_books():
    with open(os.path.join(DATA_DIR, "popular.json"), encoding="utf-8") as f:
        popular = json.load(f)
    books = {}
    for entry in popular:
        docs = entry.get("data", {}).get("response", {}).get("docs", [])
        for d in docs:
            doc = d.get("doc", d)
            isbn = (doc.get("isbn13") or "").strip()
            if not isbn or isbn in books:
                continue
            books[isbn] = {
                "isbn13": isbn,
                "title": (doc.get("bookname") or "").strip(),
                "author": (doc.get("authors") or "").strip(),
                "publisher": (doc.get("publisher") or "").strip(),
                "pub_year": (doc.get("publication_year") or "").strip(),
                "kdc_code": (doc.get("class_no") or "").strip(),
                "cover_url": (doc.get("bookImageURL") or "").strip(),
                "description": "",
                "page_count": None,
            }
    return list(books.values())

def fetch_aladin(isbn):
    if not ALADIN_KEY:
        return None, None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        r = requests.get(
            "https://www.aladin.co.kr/ttb/api/ItemLookUp.aspx",
            headers=headers,
            params={
                "ttbkey": ALADIN_KEY, "itemIdType": "ISBN13", "ItemId": isbn,
                "output": "js", "Version": "20131101", "OptResult": "packing",
            },
            timeout=15,
        )
        data = r.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        return None, None

    item = (data.get("item") or [None])[0]
    if not item:
        return None, None
    desc = (item.get("description") or "").strip()
    page = (item.get("subInfo") or {}).get("itemPage") or None
    return desc, page

def fetch_naver(isbn):
    if not (NAVER_ID and NAVER_SECRET):
        return None
    try:
        r = requests.get(
            "https://openapi.naver.com/v1/search/book.json",
            params={"query": isbn},
            headers={"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET},
            timeout=15,
        )
        items = r.json().get("items") or []
    except requests.exceptions.RequestException:
        return None

    if not items:
        return None
    return (items[0].get("description") or "").strip()

def main():
    if not ALADIN_KEY and not (NAVER_ID and NAVER_SECRET):
        print("[중단] .env에 ALADIN_TTB_KEY 또는 NAVER_CLIENT_ID/SECRET이 없습니다.")
        return

    books = collect_unique_books()
    target = books[:MAX_BOOKS]
    print(f"고유 도서 {len(books)}권 중 {len(target)}권 보강 시작...")

    for i, b in enumerate(target, 1):
        desc, page = None, None
        try:
            desc, page = fetch_aladin(b["isbn13"])
        except Exception as e:
            print(f"   알라딘 실패 {b['isbn13']}: {e}")
            
        if not desc:
            try:
                desc = fetch_naver(b["isbn13"])
            except Exception as e:
                print(f"   네이버 실패 {b['isbn13']}: {e}")
                
        if desc:
            b["description"] = desc
        if page:
            b["page_count"] = page
            
        if i % 25 == 0:
            print(f"   {i}/{len(target)} ...")
            
        time.sleep(0.5)

    out_path = os.path.join(DATA_DIR, "books.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
        
    enriched = sum(1 for b in books if b["description"])
    print(f"[완료] {out_path} — 총 {len(books)}권, 소개 보강 {enriched}권")

if __name__ == "__main__":
    main()