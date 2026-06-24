"""내용 기반 임베딩 유사도 (D30).
저장된 BookEmbedding 벡터로 코사인 최근접만 계산 — 외부 호출 0.
build_candidates의 co-loan dead-end 보강 + 홈 '반복정제 발견'의 엔진."""
import math

from books.models import BookEmbedding

_UNIT = None  # isbn -> 단위벡터(정규화) 캐시 (프로세스 단위)


def _normalize(vec):
    n = math.sqrt(sum(x * x for x in vec))
    return [x / n for x in vec] if n else vec


def _load():
    global _UNIT
    if _UNIT is None:
        _UNIT = {e.book_id: _normalize(e.vector) for e in BookEmbedding.objects.all()}
    return _UNIT


def reset_cache():
    global _UNIT
    _UNIT = None


def similar_books(seed_isbns, exclude=None, limit=20):
    """seed들과 내용이 가장 비슷한 책 목록. 각 책 점수 = seed들 중 최대 코사인.
    반환: [(isbn13, sim, best_seed_isbn), ...] 점수 내림차순."""
    units = _load()
    exclude = set(exclude or []) | set(seed_isbns)
    seeds = [(i, units[i]) for i in seed_isbns if i in units]
    if not seeds:
        return []

    out = []
    for isbn, vec in units.items():
        if isbn in exclude:
            continue
        best_sim, best_seed = -1.0, None
        for si, sv in seeds:
            d = sum(a * b for a, b in zip(vec, sv))
            if d > best_sim:
                best_sim, best_seed = d, si
        out.append((isbn, round(best_sim, 4), best_seed))

    out.sort(key=lambda t: t[1], reverse=True)
    return out[:limit]
