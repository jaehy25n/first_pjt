import os
import time

import requests
from django.core.management.base import BaseCommand

from books.models import Book, BookEmbedding

EMBED_MODEL = "text-embedding-3-small"   # 1536차원, 다국어 (D30)
BATCH_SIZE = 64                          # 한 번의 API 호출에 넣는 책 수


def build_text(book):
    """임베딩 입력 텍스트 = 제목 + 저자 + 소개(길면 자름)."""
    parts = [book.title or ""]
    if book.author:
        parts.append(book.author)
    if book.description:
        parts.append(book.description[:2000])
    return "\n".join(p for p in parts if p).strip()


class Command(BaseCommand):
    help = "GMS 임베딩으로 전 도서 벡터를 계산해 BookEmbedding에 저장한다. 재실행 안전(이미 있으면 건너뜀)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="이미 임베딩된 책도 다시 계산")
        parser.add_argument("--limit", type=int, default=0, help="처음 N권만(테스트용)")

    def handle(self, *args, **opts):
        url = os.getenv("GMS_URL", "https://gms.ssafy.io/gmsapi/api.openai.com/v1")
        key = os.getenv("GMS_KEY")
        if not key:
            self.stderr.write(self.style.ERROR("GMS_KEY 없음 — .env 확인"))
            return

        qs = Book.objects.all()
        if not opts["force"]:
            done = set(BookEmbedding.objects.values_list("book_id", flat=True))
            qs = qs.exclude(isbn13__in=done)
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        books = list(qs)
        if not books:
            self.stdout.write(self.style.SUCCESS("새로 임베딩할 책이 없습니다."))
            return

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        saved, failed = 0, 0

        for start in range(0, len(books), BATCH_SIZE):
            batch = books[start : start + BATCH_SIZE]
            inputs = [build_text(b) for b in batch]

            vectors = None
            for attempt in range(3):
                try:
                    r = requests.post(
                        f"{url}/embeddings",
                        headers=headers,
                        json={"model": EMBED_MODEL, "input": inputs},
                        timeout=60,
                    )
                    r.raise_for_status()
                    data = sorted(r.json()["data"], key=lambda d: d["index"])
                    vectors = [d["embedding"] for d in data]
                    break
                except Exception as e:
                    wait = 3 * (attempt + 1)
                    self.stderr.write(f"  배치 {start} 실패({e}) → {wait}s 후 재시도")
                    time.sleep(wait)

            if vectors is None or len(vectors) != len(batch):
                failed += len(batch)
                continue

            for book, vec in zip(batch, vectors):
                BookEmbedding.objects.update_or_create(
                    book=book, defaults={"model": EMBED_MODEL, "vector": vec}
                )
                saved += 1

            self.stdout.write(f"  {min(start + BATCH_SIZE, len(books))}/{len(books)} 저장…")
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS(f"임베딩 완료: 저장 {saved}건, 실패 {failed}건 ({EMBED_MODEL})"))
