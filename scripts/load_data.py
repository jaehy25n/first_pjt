import os
import sys
import json
import django

# Setup django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from books.models import Library, Book, Holding, CoLoan

DATA_DIR = os.path.join(BASE_DIR, "data")

def clean_isbn(isbn):
    if not isbn: return ""
    return "".join(filter(str.isdigit, str(isbn)))[-13:]

def load_libraries():
    path = os.path.join(DATA_DIR, "libraries.json")
    if not os.path.exists(path):
        print("libraries.json not found")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    count = 0
    for item in data:
        try:
            lib_info = item["data"]["response"]["libs"][0]["lib"]
            lib_code = lib_info["libCode"]
            name = lib_info["libName"]
            region = lib_info.get("address", "")
            Library.objects.update_or_create(
                lib_code=lib_code,
                defaults={"name": name, "region": region}
            )
            count += 1
        except (KeyError, IndexError):
            pass
    print(f"Loaded {count} libraries.")

def load_books():
    path = os.path.join(DATA_DIR, "books.json")
    if not os.path.exists(path):
        print("books.json not found")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    count = 0
    for item in data:
        isbn13 = clean_isbn(item.get("isbn13"))
        if not isbn13 or len(isbn13) != 13:
            continue
            
        pub_year = item.get("pub_year")
        try:
            pub_year = int(pub_year)
        except (ValueError, TypeError):
            pub_year = None
            
        page_count = item.get("page_count")
        try:
            page_count = int(page_count)
        except (ValueError, TypeError):
            page_count = None
            
        Book.objects.update_or_create(
            isbn13=isbn13,
            defaults={
                "title": item.get("title", "")[:255],
                "author": item.get("author", "")[:255],
                "publisher": item.get("publisher", "")[:255],
                "pub_year": pub_year,
                "kdc_code": item.get("kdc_code", "")[:20],
                "cover_url": item.get("cover_url", "")[:500],
                "description": item.get("description", ""),
                "page_count": page_count,
            }
        )
        count += 1
    print(f"Loaded {count} books.")

def load_holdings():
    path = os.path.join(DATA_DIR, "holdings.json")
    if not os.path.exists(path):
        print("holdings.json not found")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    count = 0
    lib_cache = {lib.lib_code: lib for lib in Library.objects.all()}
    
    for item in data:
        lib_code = item.get("libCode")
        isbn13 = clean_isbn(item.get("isbn13"))
        
        library = lib_cache.get(lib_code)
        if not library or not isbn13:
            continue
            
        try:
            book = Book.objects.get(isbn13=isbn13)
        except Book.DoesNotExist:
            continue
            
        has_book = item.get("has_book") == "Y"
        loan_available = item.get("loan_available") == "Y"
        
        Holding.objects.update_or_create(
            library=library,
            book=book,
            defaults={
                "has_book": has_book,
                "loan_available": loan_available,
            }
        )
        count += 1
    print(f"Loaded {count} holdings.")

def load_coloans():
    path = os.path.join(DATA_DIR, "coloan.json")
    if not os.path.exists(path):
        print("coloan.json not found")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # 함께대출 + 마니아추천 + 다독자추천을 유사도 엣지로 통합 (D30).
    # 가중: 함께대출 1.0 (직접 신호) / 마니아·다독자 0.8 (보조). 같은 쌍은 최고점 유지.
    LIST_WEIGHTS = [("coloan", 1.0), ("mania", 0.8), ("reader", 0.8)]
    edge_score = {}  # (base_isbn, target_isbn) -> 최고 score
    for item in data:
        base_isbn = clean_isbn(item.get("isbn13"))
        if not base_isbn:
            continue
        for key, weight in LIST_WEIGHTS:
            for i, co_item in enumerate(item.get(key, [])):
                target_isbn = clean_isbn(co_item.get("isbn13"))
                if not target_isbn or target_isbn == base_isbn:
                    continue
                score = float(max(100 - i, 1)) * weight
                k = (base_isbn, target_isbn)
                if score > edge_score.get(k, 0):
                    edge_score[k] = score

    # DB에 양쪽 책이 다 있는 엣지만 적재
    existing = set(Book.objects.values_list("isbn13", flat=True))
    count = 0
    for (base_isbn, target_isbn), score in edge_score.items():
        if base_isbn not in existing or target_isbn not in existing:
            continue
        CoLoan.objects.update_or_create(
            book_id=base_isbn,
            co_book_id=target_isbn,
            defaults={"score": round(score, 2)}
        )
        count += 1
    print(f"Loaded {count} edges (coloan+mania+reader).")

if __name__ == "__main__":
    load_libraries()
    load_books()
    load_holdings()
    load_coloans()
    load_coloans()
    print("Done loading data.")
