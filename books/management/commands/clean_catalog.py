"""소개 없는 책 정리(3갈래) — 보강 / 비도서 삭제 / 잔여 신호제거. (D32 후속)

대상 = description 빈 책. 각각:
  ① 비도서/정크(제목에 DVD·disc·블루레이·OST 등) → --delete-junk 시 삭제(임베딩·소장·신호 cascade)
  ② 보강 성공(알라딘 ItemLookUp→네이버로 소개 채움) → DB 갱신 + 임베딩 삭제(→ embed_books 재계산)
  ③ 보강 실패 잔여(진짜 책인데 소개 못 구함, 주로 영어 아동 리더스)
        → 카탈로그·검색엔 유지하되 popular/bestseller 신호 제거(추천/발견에 안 밀림)

실행 (venv, first_pjt):
    python manage.py clean_catalog                 # dry-run: 3갈래 목록만(외부 조회는 함, 쓰기 X)
    python manage.py clean_catalog --apply         # ②보강+재임베딩표시, ③신호제거
    python manage.py clean_catalog --apply --delete-junk   # + ①비도서 삭제

※ --apply는 DB만 수정한다(books.json 미수정) → 이후 load_data를 다시 돌리면 되돌아감.
   최종 fixtures는 dumpdata가 DB에서 뜨므로 OK. 정리는 load_data '다음에' 1회.
※ 끝나면 `python manage.py embed_books`로 ②(소개 채워진 책) 재임베딩.
"""
import os
import re
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from books.models import Book, BookEmbedding, LoanSignal

# 비도서(미디어) 판별 — 보수적으로(오검출 줄이려 CD는 제외: 'Book+CD' 같은 정상 책 있음)
JUNK_RE = re.compile(r"(?i)(\bdvd\b|\d*\s*disc\b|블루레이|blu-?ray|\bost\b|\blp\b)")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
SLEEP = 0.4


def fetch_aladin(isbn, key):
    if not key:
        return ""
    try:
        r = requests.get("https://www.aladin.co.kr/ttb/api/ItemLookUp.aspx", headers=UA,
                         params={"ttbkey": key, "itemIdType": "ISBN13", "ItemId": isbn,
                                 "output": "js", "Version": "20131101", "OptResult": "packing"},
                         timeout=15)
        item = (r.json().get("item") or [None])[0]
        return (item.get("description") or "").strip() if item else ""
    except Exception:
        return ""


def fetch_naver(isbn, nid, nsec):
    if not (nid and nsec):
        return ""
    try:
        r = requests.get("https://openapi.naver.com/v1/search/book.json",
                         params={"query": isbn},
                         headers={"X-Naver-Client-Id": nid, "X-Naver-Client-Secret": nsec},
                         timeout=15)
        items = r.json().get("items") or []
        return (items[0].get("description") or "").strip() if items else ""
    except Exception:
        return ""


class Command(BaseCommand):
    help = "소개 없는 책을 3갈래로 정리(보강/비도서삭제/잔여 신호제거). (D32 후속)"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="②보강·③신호제거를 실제 반영")
        parser.add_argument("--delete-junk", action="store_true", help="①비도서/정크도 삭제")

    def handle(self, *args, **opts):
        ak = os.environ.get("ALADIN_TTB_KEY")
        nid = os.environ.get("NAVER_CLIENT_ID")
        nsec = os.environ.get("NAVER_CLIENT_SECRET")
        apply = opts["apply"]
        del_junk = opts["delete_junk"]

        empties = list(Book.objects.filter(description="").values_list("isbn13", "title", "author"))
        if not empties:
            self.stdout.write("소개 없는 책이 없습니다.")
            return

        junk, to_enrich = [], []
        for isbn, title, author in empties:
            (junk if JUNK_RE.search(title or "") else to_enrich).append((isbn, title, author))

        self.stdout.write(f"소개 없음 {len(empties)}권 → 비도서후보 {len(junk)} / 보강시도 {len(to_enrich)}")
        self.stdout.write(f"알라딘 ItemLookUp→네이버로 소개 조회 중… (외부 {len(to_enrich)}콜)")

        filled, residual = [], []  # filled: (isbn, desc) / residual: (isbn, title)
        for isbn, title, author in to_enrich:
            desc = fetch_aladin(isbn, ak) or fetch_naver(isbn, nid, nsec)
            (filled.append((isbn, desc)) if desc else residual.append((isbn, title)))
            time.sleep(SLEEP)

        # --- 리포트 ---
        def show(label, rows, getter):
            self.stdout.write(f"\n[{label}] {len(rows)}권")
            for r in rows[:15]:
                self.stdout.write(f"   {getter(r)[:50]}")
            if len(rows) > 15:
                self.stdout.write(f"   … 외 {len(rows)-15}권")

        title_of = dict((i, t) for i, t, _ in empties)
        show("① 비도서/정크 (삭제 후보)", junk, lambda r: r[1])
        show("② 보강 성공 (소개 채움 → 재임베딩)", filled, lambda r: f"{title_of.get(r[0],'')} ← {r[1][:30]}…")
        show("③ 잔여: 소개 못 구함 (유지+신호제거)", residual, lambda r: r[1])

        if not apply:
            self.stdout.write("\n[dry-run] 쓰기 안 함. 적용: --apply (비도서삭제는 --delete-junk 추가)")
            return

        # --- 적용 ---
        # ② 소개 채움 + 임베딩 삭제(재계산 대상)
        for isbn, desc in filled:
            Book.objects.filter(isbn13=isbn).update(description=desc)
        f_ids = [i for i, _ in filled]
        emb_del, _ = BookEmbedding.objects.filter(book_id__in=f_ids).delete()

        # ③ 잔여 → popular/bestseller 신호 제거(검색은 유지)
        r_ids = [i for i, _ in residual]
        sig_del, _ = LoanSignal.objects.filter(book_id__in=r_ids,
                                               scope__in=["popular", "bestseller"]).delete()

        msg = [f"② 소개 {len(filled)}권 갱신(임베딩 {emb_del}건 삭제→재계산 대상)",
               f"③ 잔여 {len(residual)}권 신호 {sig_del}건 제거"]
        # ① 비도서 삭제(옵션)
        if del_junk and junk:
            j_ids = [i for i, _, _ in junk]
            bk_del, _ = Book.objects.filter(isbn13__in=j_ids).delete()
            msg.append(f"① 비도서 {len(junk)}권 삭제(관련행 {bk_del} cascade)")
        elif junk:
            msg.append(f"① 비도서 {len(junk)}권 보존(삭제하려면 --delete-junk)")

        self.stdout.write("\n[적용 완료] " + " · ".join(msg))
        self.stdout.write("→ 다음: python manage.py embed_books  (②재임베딩)")
