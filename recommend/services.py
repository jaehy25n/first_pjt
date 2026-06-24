from books.models import Book, Holding, CoLoan, LoanSignal
from accounts.models import BookPreference, ReadingLog
from .similarity import similar_books

# 긍정 seed 가중치
W_SEED = 3.0      # 선택/완독한 책 (즉시 맥락)
W_LIKE = 2.0      # 표지픽 좋아요
W_WISH = 1.0      # 찜 (약한 긍정)
POP_BONUS = 0.02  # 인기 보충(작게)
W_EMBED = 10.0    # 내용 임베딩 이웃(co-loan dead-end 보강, sim 0~1 스케일업) (D30)
POP_BONUS_BEST = 0.015  # 베스트셀러(전국 판매순위) — popular(대출수)보다 약한 콜드스타트 프라이어 (D33 #2)
AVAIL_BONUS = 0.4       # 선택 도서관에서 '지금 대출가능'이면 동점 우대(게이트 아님, D2 완화 · D33)
LOANED_BONUS = 0.1      # 소장이나 대출중이면 약간 우대


def build_candidates(user, seed_isbn13=None, limit=5):
    """가중 다중 seed 후보 생성 (D19, 데이터만 · 외부 API 없음).

    긍정 seed = seed_isbn13(선택/완독) + BookPreference 좋아요 + ReadingLog 찜.
    부정 seed = BookPreference 별로 → 그 함께대출 이웃·동일 저자를 후보에서 제외.
    이미 읽은 책(ReadingLog finished)·별로 책·seed 자신도 제외.
    각 긍정 seed의 CoLoan 이웃에 (seed 가중치 × coloan score)를 누적해 점수화하고,
    부족하면 관심사/전체 인기대출로 낮은 가중치 보충.
    주 도서관 '지금 대출가능' 필터(없으면 소장으로 1단계 완화) 적용.
    각 후보에 via_isbn13/via_title(어느 seed의 이웃인지)을 달아 R-2(이유 생성)가 근거로 쓰게 함.
    """
    candidate_limit = 50

    # 선택한 도서관들(union). 비어 있으면 대표(primary)로 폴백 (D29)
    try:
        profile = user.profile
    except Exception:
        return []
    libraries = list(profile.libraries.all())
    if not libraries and profile.primary_library:
        libraries = [profile.primary_library]
    # 도서관 미선택도 허용 — 가용성은 게이트가 아니라 배지(D33). 취향 ⊥ 도서관(D35).

    # 1) 사용자 시드 수집
    # 좋아요=긍정 seed. 찜(wish)은 좋아요로 통합됨 → 별도 분기 제거 (D28)
    liked = list(BookPreference.objects.filter(user=user, sentiment='like').values_list('book_id', flat=True))
    disliked = list(BookPreference.objects.filter(user=user, sentiment='dislike').values_list('book_id', flat=True))
    read = set(ReadingLog.objects.filter(user=user, status='finished').values_list('book_id', flat=True))

    positive = []  # [(isbn, weight)]
    if seed_isbn13:
        positive.append((seed_isbn13, W_SEED))
    positive += [(i, W_LIKE) for i in liked]

    seed_titles = dict(
        Book.objects.filter(isbn13__in=[s for s, _ in positive]).values_list('isbn13', 'title')
    )

    # 후보에서 제외할 책: 이미 읽음 + 별로 + 긍정 seed 자신
    exclude = set(read) | set(disliked) | {s for s, _ in positive}

    # 2) 부정 seed의 함께대출 이웃·동일 저자 → 제외 확장
    if disliked:
        exclude |= set(CoLoan.objects.filter(book_id__in=disliked).values_list('co_book_id', flat=True))
        dis_authors = [a for a in Book.objects.filter(isbn13__in=disliked).values_list('author', flat=True) if a]
        if dis_authors:
            exclude |= set(Book.objects.filter(author__in=dis_authors).values_list('isbn13', flat=True))

    # 3) 긍정 seed → CoLoan 이웃 점수 누적 (+ 출처 seed·종류 기록)
    scores = {}   # isbn -> 누적 점수
    source = {}   # isbn -> (출처 seed isbn, 기여도, 종류: 'coloan'/'embed')
    for seed, weight in positive:
        for co_book_id, score in CoLoan.objects.filter(book_id=seed).values_list('co_book_id', 'score'):
            if co_book_id in exclude:
                continue
            contrib = weight * (score or 0.0)
            scores[co_book_id] = scores.get(co_book_id, 0.0) + contrib
            if contrib > source.get(co_book_id, (None, -1.0, None))[1]:
                source[co_book_id] = (seed, contrib, 'coloan')

    # 3.5) 임베딩 이웃으로 보강 — co-loan이 없는(dead-end) 책도 내용 유사로 후보화 (D30)
    seed_weight = {s: w for s, w in positive}
    pos_isbns = [s for s, _ in positive]
    for isbn, sim, best_seed in similar_books(pos_isbns, exclude=exclude, limit=40):
        contrib = seed_weight.get(best_seed, 1.0) * sim * W_EMBED
        scores[isbn] = scores.get(isbn, 0.0) + contrib
        if contrib > source.get(isbn, (None, -1.0, None))[1]:
            source[isbn] = (best_seed, contrib, 'embed')

    # 4) 인기로 보충 — popular(정보나루 대출수) + bestseller(알라딘 판매순위, 약하게) (D33 #2)
    #    콜드스타트(seed 없음)·세렌디피티의 backbone. bestseller는 신규 카탈로그를 콜드 경로에 태움.
    interest_prefixes = [it.kdc_prefix for it in user.profile.interests.all() if it.kdc_prefix]

    def add_popularity(scope, mult, kind):
        for book_id, kdc_code, value in (LoanSignal.objects.filter(scope=scope)
                                         .values_list('book_id', 'book__kdc_code', 'value')):
            if book_id in exclude:
                continue
            bonus = mult * (value or 0.0)
            if interest_prefixes and (kdc_code or '')[:1] in interest_prefixes:
                bonus += 0.5  # 관심사 분야 약간 가산
            scores[book_id] = scores.get(book_id, 0.0) + bonus
            if kind == 'bestseller' and book_id not in source:
                source[book_id] = (None, bonus, 'bestseller')

    add_popularity('popular', POP_BONUS, 'popular')
    add_popularity('bestseller', POP_BONUS_BEST, 'bestseller')

    # 5) 가용성 = 하드게이트 아님(D33). 전체 카탈로그에서 점수순으로 뽑고,
    #    선택 도서관 소장/대출가능은 '배지'로 부착(+ 동점이면 빌릴 수 있는 책 약간 우대).
    hold_map = {}  # isbn -> (rank: 2=대출가능/1=소장, library_name)
    if libraries:
        for h in Holding.objects.filter(library__in=libraries, has_book=True).select_related('library'):
            rank = 2 if h.loan_available else 1
            cur = hold_map.get(h.book_id)
            if not cur or rank > cur[0]:
                hold_map[h.book_id] = (rank, h.library.name)
        for isbn, (rank, _) in hold_map.items():
            if isbn in scores:
                scores[isbn] += AVAIL_BONUS if rank == 2 else LOANED_BONUS

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_isbns = [isbn for isbn, _ in ranked[: candidate_limit + 30]]
    book_map = {b.isbn13: b for b in Book.objects.filter(isbn13__in=top_isbns)}

    candidate_list = []
    for isbn, sc in ranked:
        if len(candidate_list) >= candidate_limit:
            break
        book = book_map.get(isbn)
        if not book:
            continue
        # 가용성 배지 (선택 도서관 기준; 미선택이면 None=배지 없음)
        if not libraries:
            availability, library_name = None, ""
        elif isbn in hold_map:
            rank, library_name = hold_map[isbn]
            availability = "available" if rank == 2 else "loaned"
        else:
            availability, library_name = "none", ""

        via_isbn, _, kind = source.get(isbn, (None, 0.0, None))
        via_title = seed_titles.get(via_isbn)
        if kind == 'coloan' and via_title:
            signal = "좋아한 '%s'와 함께 많이 빌린 책" % via_title
        elif kind == 'embed' and via_title:
            signal = "좋아한 '%s'와 내용이 비슷한 책" % via_title
        elif kind == 'bestseller':
            signal = "요즘 많이 읽히는 책"
        else:
            signal = "도서관 인기 대출 도서"

        candidate_list.append({
            "isbn13": isbn,
            "title": book.title,
            "author": book.author,
            "kdc_code": book.kdc_code,
            "via_isbn13": via_isbn,
            "via_title": via_title,
            "signal": signal,
            "library_name": library_name,
            "availability": availability,
            "score": round(sc, 3),
        })

    # 식별 번호(n) 부여 (R-2가 번호로 선별 → 환각 차단)
    for idx, cand in enumerate(candidate_list, 1):
        cand['n'] = idx
    return candidate_list
