import json

from django.conf import settings
from django.core.management.base import BaseCommand

from books.models import Book, LoanSignal

# 인기 점수 = Σ (PAGE_BASE - 각 도서관 순위). 여러 도서관에서 상위권일수록 높음.
PAGE_BASE = 201


class Command(BaseCommand):
    help = "data/popular.json(인기대출 순위)을 읽어 LoanSignal(scope='popular')로 적재한다. 외부 API 호출 없음."

    def handle(self, *args, **options):
        path = settings.BASE_DIR / 'data' / 'popular.json'
        if not path.exists():
            self.stderr.write(self.style.ERROR(f"popular.json 없음: {path}"))
            return

        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        # isbn13 -> 누적 인기 점수
        scores = {}
        for lib in data:
            docs = (lib.get('data', {})
                       .get('response', {})
                       .get('docs', []))
            for entry in docs:
                doc = entry.get('doc', {})
                isbn = (doc.get('isbn13') or '').strip()
                if not isbn:
                    continue
                try:
                    rank = int(doc.get('ranking', 0))
                except (TypeError, ValueError):
                    continue
                if rank <= 0:
                    continue
                scores[isbn] = scores.get(isbn, 0) + max(0, PAGE_BASE - rank)

        # DB에 존재하는 책만 적재 (재실행 안전: 기존 popular 신호 비우고 다시)
        existing = set(Book.objects.values_list('isbn13', flat=True))
        LoanSignal.objects.filter(scope='popular').delete()
        signals = [
            LoanSignal(book_id=isbn, scope='popular', value=float(score))
            for isbn, score in scores.items()
            if isbn in existing
        ]
        LoanSignal.objects.bulk_create(signals)

        self.stdout.write(self.style.SUCCESS(
            f"popular 신호 적재 완료: {len(signals)}건 "
            f"(popular.json 고유 ISBN {len(scores)}개 중 DB 존재분)"
        ))
