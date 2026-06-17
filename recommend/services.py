from books.models import Book, Holding, CoLoan, LoanSignal

def build_candidates(user, seed_isbn13=None, limit=5):
    """
    미니스펙 Phase 4: 추천 후보 생성 함수 (데이터 기반)
    LLM의 최종 limit 파라미터를 인자로 받지만, 이 함수 내부적으로는 30~50권의 후보를 생성하여 반환합니다.
    """
    candidate_limit = 50
    
    try:
        primary_library = user.profile.primary_library
    except Exception:
        primary_library = None
        
    if not primary_library:
        return []

    def gather_candidates(require_loan_available=True):
        candidates_dict = {}
        
        def add_candidate(book, signal_text):
            if len(candidates_dict) >= candidate_limit:
                return
            if book.isbn13 not in candidates_dict:
                # 사용자의 주 도서관 소장 여부 확인
                holding = Holding.objects.filter(library=primary_library, book=book).first()
                if holding and holding.has_book:
                    if require_loan_available and not holding.loan_available:
                        return
                    candidates_dict[book.isbn13] = {
                        "isbn13": book.isbn13,
                        "title": book.title,
                        "author": book.author,
                        "kdc_code": book.kdc_code,
                        "signal": signal_text,
                        "library_name": primary_library.name
                    }

        if seed_isbn13:
            # 1. Seed 도서 기반 (함께대출 CoLoan)
            coloans = CoLoan.objects.filter(book__isbn13=seed_isbn13).order_by('-score').select_related('co_book')
            for col in coloans:
                add_candidate(col.co_book, "선택하신 도서와 함께 많이 대출된 책입니다.")
                
            # 2. Seed 도서 기반 (같은 KDC 카테고리의 인기대출)
            seed_book = Book.objects.filter(isbn13=seed_isbn13).first()
            if seed_book and seed_book.kdc_code:
                kdc_prefix = str(seed_book.kdc_code)[:1]
                signals = LoanSignal.objects.filter(book__kdc_code__startswith=kdc_prefix).order_by('-value').select_related('book')
                for sig in signals:
                    add_candidate(sig.book, "비슷한 주제 분야의 인기 대출 도서입니다.")
        else:
            # 1. 관심사 기반 (프로필에 등록된 KDC 카테고리의 인기대출)
            interests = user.profile.interests.all()
            if interests.exists():
                for interest in interests:
                    signals = LoanSignal.objects.filter(book__kdc_code__startswith=interest.kdc_prefix).order_by('-value').select_related('book')
                    for sig in signals:
                        add_candidate(sig.book, f"관심사 '{interest.name}' 관련 인기 대출 도서입니다.")
            
        # 후보가 부족할 경우 (30권 미만), 도서관 전체 인기대출로 채우기
        if len(candidates_dict) < 30:
            signals = LoanSignal.objects.all().order_by('-value').select_related('book')
            for sig in signals:
                add_candidate(sig.book, "도서관 전체 인기 대출 도서입니다.")
                
        return list(candidates_dict.values())

    # 1차 시도: '지금 대출가능' (loan_available=True) 인 도서만 필터링
    candidate_list = gather_candidates(require_loan_available=True)
    
    # 2차 시도: 만약 가용 도서가 0권이라면 '소장 있음(대출중 포함)' 으로 한 단계 조건 완화
    if len(candidate_list) == 0:
        candidate_list = gather_candidates(require_loan_available=False)
        
    # 최종 리스트에 식별 번호(n) 부여 (1번부터 시작)
    for idx, cand in enumerate(candidate_list, 1):
        cand['n'] = idx
        
    return candidate_list
