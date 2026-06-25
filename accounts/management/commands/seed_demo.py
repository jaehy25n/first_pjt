"""시연용 데모 계정 시드 (U). 멱등 — 여러 번 돌려도 안전.

demo 계정에 좋아요(취향)·읽는 중·완독(평점)을 미리 채워, 로그인하면 곧바로
마이서재·독서통계·오늘의 추천이 풍성하게 보이도록 한다. 카탈로그 fixtures와 무관(사용자 데이터만).
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from books.models import Book, LoanSignal
from accounts.models import BookPreference, ReadingLog

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo1234"


class Command(BaseCommand):
    help = "시연용 demo 계정 + 취향/독서기록 시드 (멱등)"

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username=DEMO_USERNAME)
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(f"demo 계정 생성 (pw: {DEMO_PASSWORD})")
        else:
            self.stdout.write("demo 계정 이미 있음 — 시드 갱신")

        # 표지 있는 인기책을 인기순으로 모아 풀 구성
        pop_ids = list(
            LoanSignal.objects.filter(scope="popular")
            .order_by("-value")
            .values_list("book_id", flat=True)
        )
        by_id = Book.objects.in_bulk(pop_ids)
        pool = []
        for bid in pop_ids:
            b = by_id.get(bid)
            if b and b.cover_url:
                pool.append(b)
            if len(pool) >= 20:
                break

        if len(pool) < 13:
            self.stderr.write("표지 있는 인기책이 부족합니다. fixtures 적재(loaddata)를 먼저 하세요.")
            return

        liked = pool[:8]      # 좋아요 8
        reading = pool[8:10]  # 읽는 중 2
        finished = pool[10:13]  # 완독 3 (평점 5,4,5)

        for b in liked:
            BookPreference.objects.get_or_create(
                user=user, book=b, defaults={"sentiment": "like"}
            )
        for b in reading:
            ReadingLog.objects.update_or_create(
                user=user, book=b, defaults={"status": "reading"}
            )
        for i, b in enumerate(finished):
            ReadingLog.objects.update_or_create(
                user=user, book=b, defaults={"status": "finished", "rating": 5 - (i % 2)}
            )

        self.stdout.write(self.style.SUCCESS(
            f"완료 — demo: 좋아요 {len(liked)} · 읽는중 {len(reading)} · 완독 {len(finished)}"
        ))
