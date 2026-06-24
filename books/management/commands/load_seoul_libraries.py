"""서울 도서관 355곳을 data/_libraries_seoul.json에서 Library로 적재(upsert) — D34 Tier1.

위경도·주소 포함. `lib_code` 기준 update_or_create라 기존 도서관(마포 3관)·Holding 관계는 유지된다.
실행 (venv, first_pjt): python manage.py load_seoul_libraries
"""
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from books.models import Library


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class Command(BaseCommand):
    help = "서울 도서관 355곳(위경도·주소)을 Library로 upsert (D34 Tier1)"

    def handle(self, *args, **opts):
        path = os.path.join(settings.BASE_DIR, "data", "_libraries_seoul.json")
        if not os.path.exists(path):
            self.stderr.write(f"{path} 없음")
            return
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)

        created, updated, skipped = 0, 0, 0
        for row in rows:
            lib = row.get("lib", row) if isinstance(row, dict) else {}
            code = (lib.get("libCode") or "").strip()
            if not code:
                skipped += 1
                continue
            address = (lib.get("address") or "").strip()
            parts = address.split()
            region = parts[1] if len(parts) > 1 else "서울특별시"   # 주소에서 '구' 추출, 없으면 서울
            _, was_created = Library.objects.update_or_create(
                lib_code=code,
                defaults={
                    "name": (lib.get("libName") or "").strip(),
                    "region": region,
                    "address": address,
                    "latitude": _to_float(lib.get("latitude")),
                    "longitude": _to_float(lib.get("longitude")),
                },
            )
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS(
            f"[완료] Library upsert: 신규 {created}, 갱신 {updated}, 건너뜀 {skipped} / 총 {Library.objects.count()}곳"
        ))
