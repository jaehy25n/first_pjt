"""신규 알라딘 책의 '베스트셀러 순위'를 LoanSignal(scope='bestseller')로 적재.
(#2, D32 후속 — 콜드스타트/피커 라운드1/세렌디피티용 약한 인기 프라이어)

신규책 식별 = data/books.json - data/books.json.bak(수집 직전 564권).
순위 = books.json에서 신규책이 등장한 순서(분야별 크롤이 베스트셀러 순서였음)를
       KDC 버킷별로 0,1,2…로 매기고 value = max(BASE - 순위, 1).
※ 정보나루 대출수(scope='popular')와 단위가 달라 별도 scope로 분리 저장 →
  build_candidates에서 약한 가중으로 합산(라이브 대출신호를 압도하지 않게).

실행 (venv, first_pjt):
    python manage.py load_bestseller_signal
"""
import os
import json

from django.conf import settings
from django.core.management.base import BaseCommand

from books.models import Book, LoanSignal

BASE = 200.0  # 버킷 1위 ≈ 200점, 하위로 갈수록 감소(최소 1)


def clean_isbn(isbn):
    return "".join(filter(str.isdigit, str(isbn or "")))[-13:]


def first_digit(kdc):
    k = (kdc or "").strip()
    return k[0] if k and k[0].isdigit() else "?"


class Command(BaseCommand):
    help = "신규 알라딘 책의 베스트셀러 순위를 LoanSignal(scope='bestseller')로 적재. (#2)"

    def handle(self, *args, **opts):
        data_dir = os.path.join(settings.BASE_DIR, "data")
        cur_path = os.path.join(data_dir, "books.json")
        bak_path = os.path.join(data_dir, "books.json.bak")

        if not os.path.exists(cur_path):
            self.stderr.write("data/books.json 이 없습니다.")
            return
        with open(cur_path, encoding="utf-8") as f:
            cur = json.load(f)

        # 신규책 식별: .bak(수집 직전)과의 차집합. 없으면 'KDC 한 자리' 휴리스틱.
        if os.path.exists(bak_path):
            with open(bak_path, encoding="utf-8") as f:
                old_isbns = {clean_isbn(b.get("isbn13")) for b in json.load(f)}
            is_new = lambda b: clean_isbn(b.get("isbn13")) not in old_isbns
            self.stdout.write("신규책 식별: books.json - books.json.bak")
        else:
            is_new = lambda b: len((b.get("kdc_code") or "").strip()) == 1
            self.stdout.write("⚠️ .bak 없음 → 'KDC 한 자리' 휴리스틱으로 신규책 식별")

        # books.json 등장 순서 = 분야별 베스트셀러 순서. 버킷별로 0,1,2… 순위 부여.
        known = set(Book.objects.values_list("isbn13", flat=True))
        rank_in_bucket = {}
        rows, missing = [], 0
        for b in cur:
            if not is_new(b):
                continue
            isbn = clean_isbn(b.get("isbn13"))
            if isbn not in known:
                missing += 1
                continue
            bucket = first_digit(b.get("kdc_code"))
            r = rank_in_bucket.get(bucket, 0)
            rank_in_bucket[bucket] = r + 1
            value = max(BASE - r, 1.0)
            rows.append(LoanSignal(book_id=isbn, scope="bestseller", value=value))

        # 재실행 안전: 기존 bestseller 신호 비우고 다시 적재
        deleted, _ = LoanSignal.objects.filter(scope="bestseller").delete()
        LoanSignal.objects.bulk_create(rows, batch_size=500)

        self.stdout.write(
            f"[완료] bestseller 신호 {len(rows)}건 적재(기존 {deleted}건 교체)"
            + (f", DB에 없는 신규 {missing}건 건너뜀" if missing else "")
        )
        self.stdout.write(f"  버킷별 신규 수: {dict(sorted(rank_in_bucket.items()))}")
