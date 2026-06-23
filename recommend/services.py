from books.models import Book, Holding, CoLoan, LoanSignal
from accounts.models import BookPreference, ReadingLog

# 긍정 seed 가중치
W_SEED = 3.0      # 선택/완독한 책 (즉시 맥락)
W_LIKE = 2.0      # 표지픽 좋아요
W_WISH = 1.0      # 찜 (약한 긍정)
POP_BONUS = 0.02  # 인기 보충(작게)


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
    if not libraries:
        return []

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

    # 3) 긍정 seed → CoLoan 이웃 점수 누적 (+ 출처 seed 기록)
    scores = {}   # isbn -> 누적 점수
    source = {}   # isbn -> (출처 seed isbn, 그 기여도)
    for seed, weight in positive:
        for co_book_id, score in CoLoan.objects.filter(book_id=seed).values_list('co_book_id', 'score'):
            if co_book_id in exclude:
                continue
            contrib = weight * (score or 0.0)
            scores[co_book_id] = scores.get(co_book_id, 0.0) + contrib
            if contrib > source.get(co_book_id, (None, -1.0))[1]:
                source[co_book_id] = (seed, contrib)

    # 4) 부족하면 관심사 / 전체 인기대출로 보충 (낮은 가중)
    interest_prefixes = [it.kdc_prefix for it in user.profile.interests.all() if it.kdc_prefix]
    for book_id, kdc_code, value in LoanSignal.objects.filter(scope='popular').values_list('book_id', 'book__kdc_code', 'value'):
        if book_id in exclude:
            continue
        bonus = POP_BONUS * (value or 0.0)
        if interest_prefixes and (kdc_code or '')[:1] in interest_prefixes:
            bonus += 0.5  # 관심사 분야 약간 가산
        scores[book_id] = scores.get(book_id, 0.0) + bonus

    # 5) 선택 도서관 union 가용 필터 + 점수순 정렬 (어디서든 가능하면 후보)
    def assemble(require_loan_available):
        out = []
        for isbn, sc in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
            if len(out) >= candidate_limit:
                break
            holdings = list(Holding.objects.filter(library__in=libraries, book_id=isbn).select_related('library'))
            owned = [h for h in holdings if h.has_book]
            if not owned:
                continue
            available = [h for h in owned if h.loan_available]
            if require_loan_available and not available:
                continue
            chosen = available[0] if available else owned[0]  # 빌릴 수 있는 곳 우선
            book = Book.objects.filter(isbn13=isbn).first()
            if not book:
                continue
            via_isbn = source.get(isbn, (None, 0.0))[0]
            via_title = seed_titles.get(via_isbn)
            out.append({
                "isbn13": isbn,
                "title": book.title,
                "author": book.author,
                "kdc_code": book.kdc_code,
                "via_isbn13": via_isbn,
                "via_title": via_title,
                "signal": ("좋아한 '%s'와 함께 많이 빌린 책" % via_title) if via_title else "도서관 인기 대출 도서",
                "library_name": chosen.library.name,
                "score": round(sc, 3),
            })
        return out

    candidate_list = assemble(require_loan_available=True) or assemble(require_loan_available=False)

    # 식별 번호(n) 부여 (R-2가 번호로 선별 → 환각 차단)
    for idx, cand in enumerate(candidate_list, 1):
        cand['n'] = idx
    return candidate_list
