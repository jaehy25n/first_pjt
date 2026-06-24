"""KDC가 빈 책(미상)을 임베딩 이웃의 KDC 다수결(유사도 가중)로 추정해 채운다.
(#1 (b), D32 후속 — 기존 정보나루 책 중 class_no 없던 ~70권 주로 아동 세트물)

실행 (venv, first_pjt):
    python manage.py backfill_kdc --dry-run   # 추정만 미리보기(저장 X)
    python manage.py backfill_kdc             # DB의 Book.kdc_code 갱신

주의: load_data를 다시 돌리면 books.json의 빈 KDC로 70권이 되돌아간다 →
      그때는 이 명령을 다시 실행할 것. (최종 fixtures는 dumpdata가 DB에서 뜨므로 OK.)
"""
import collections

from django.core.management.base import BaseCommand

from books.models import Book
from recommend.similarity import similar_books, reset_cache

DIGITS = set("0123456789")


def first_digit(kdc):
    k = (kdc or "").strip()
    return k[0] if k and k[0] in DIGITS else None


class Command(BaseCommand):
    help = "KDC 빈 책을 임베딩 이웃 KDC 다수결(유사도 가중)로 추정해 채운다. (#1 b)"

    def add_arguments(self, parser):
        parser.add_argument("--neighbors", type=int, default=20, help="참고할 최근접 이웃 수")
        parser.add_argument("--dry-run", action="store_true", help="저장 없이 추정만 출력")

    def handle(self, *args, **opts):
        reset_cache()  # 방금 추가된 신규 임베딩까지 반영
        k = opts["neighbors"]
        dry = opts["dry_run"]

        rows = list(Book.objects.values_list("isbn13", "kdc_code", "title"))
        kdc_map = {i: first_digit(c) for i, c, _ in rows}
        title_map = {i: t for i, _, t in rows}
        unknown = [i for i, d in kdc_map.items() if d is None]
        unknown_set = set(unknown)

        if not unknown:
            self.stdout.write("미상(KDC 빈) 책이 없습니다.")
            return
        self.stdout.write(f"미상 {len(unknown)}권 → 임베딩 이웃 {k}명 유사도가중 다수결로 추정…")

        filled, skipped = 0, 0
        dist = collections.Counter()
        for isbn in unknown:
            # 이웃은 KDC 있는 책만 보도록 미상 전체를 exclude
            neigh = similar_books([isbn], exclude=unknown_set, limit=k)
            score = collections.Counter()
            for nisbn, sim, _ in neigh:
                d = kdc_map.get(nisbn)
                if d:
                    score[d] += sim
            if not score:
                skipped += 1
                continue
            best = score.most_common(1)[0][0]
            dist[best] += 1
            filled += 1
            if dry:
                top = ", ".join(f"{d}:{s:.2f}" for d, s in score.most_common(3))
                self.stdout.write(f"  {title_map.get(isbn, '')[:28]:30} → KDC {best}  ({top})")
            else:
                Book.objects.filter(isbn13=isbn).update(kdc_code=best)

        head = "[dry-run] " if dry else ""
        self.stdout.write(f"{head}추정 완료: {filled}권 채움, {skipped}권 보류(이웃 KDC 없음)")
        self.stdout.write(f"  추정 KDC 분포: {dict(sorted(dist.items()))}")
