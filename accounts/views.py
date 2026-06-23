from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Profile, Interest, ReadingLog, BookPreference
from books.models import Library, Book, Holding, LoanSignal
from .serializers import ProfileSerializer
from books.serializers import BookCardSerializer
from django.db.models import Prefetch

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

class ProfileOnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        interest_ids = request.data.get('interest_ids')
        primary_library_code = request.data.get('primary_library_code')
        
        if interest_ids is not None:
            interests = Interest.objects.filter(id__in=interest_ids)
            profile.interests.set(interests)
            
        if primary_library_code is not None:
            try:
                library = Library.objects.get(lib_code=primary_library_code)
                profile.primary_library = library
            except Library.DoesNotExist:
                # If the library doesn't exist, we can ignore or return 400. 
                # For robustness, we just ignore invalid codes in this MVP.
                pass
                
        profile.save()
        
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

class InterestListView(APIView):
    def get(self, request):
        interests = Interest.objects.all()
        # You'll also need to import InterestSerializer from .serializers
        from .serializers import InterestSerializer
        serializer = InterestSerializer(interests, many=True)
        return Response(serializer.data)

class LibraryLogView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        logs = ReadingLog.objects.filter(user=request.user).select_related('book')
        
        # 선택 도서관들(union) 기준 가용성 (D29)
        try:
            libraries = list(request.user.profile.libraries.all())
        except Exception:
            libraries = []

        if libraries:
            prefetch = Prefetch('book__holdings', queryset=Holding.objects.filter(library__in=libraries).select_related('library'), to_attr='user_holding')
            logs = logs.prefetch_related(prefetch)

        reading = []
        finished = []

        context = {'libraries': libraries}

        for log in logs:
            card_data = BookCardSerializer(log.book, context=context).data
            if log.status == 'reading':
                reading.append(card_data)
            elif log.status == 'finished':
                card_data['rating'] = log.rating
                card_data['finished_at'] = log.created.isoformat()
                finished.append(card_data)

        # 좋아요(=구 찜) 묶음은 BookPreference(like)에서 (D28)
        like_prefs = BookPreference.objects.filter(user=request.user, sentiment='like').select_related('book')
        if libraries:
            like_prefs = like_prefs.prefetch_related(
                Prefetch('book__holdings', queryset=Holding.objects.filter(library__in=libraries).select_related('library'), to_attr='user_holding')
            )
        liked = [BookCardSerializer(p.book, context=context).data for p in like_prefs]

        return Response({
            "liked": liked,
            "reading": reading,
            "finished": finished
        })
        
class LibraryLogCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        isbn13 = request.data.get('isbn13')
        status = request.data.get('status')
        rating = request.data.get('rating')
        
        if not isbn13 or not status:
            return Response({"detail": "isbn13 and status are required"}, status=400)
            
        try:
            book = Book.objects.get(isbn13=isbn13)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=404)
            
        if status in ('none', 'clear'):
            ReadingLog.objects.filter(user=request.user, book=book).delete()
            return Response({"isbn13": book.isbn13, "status": "none", "rating": None})

        log, created = ReadingLog.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={'status': status, 'rating': rating}
        )
        
        return Response({
            "isbn13": book.isbn13,
            "status": log.status,
            "rating": log.rating
        })

class LibraryToggleLikeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        isbn13 = request.data.get('isbn13')
        if not isbn13:
            return Response({"detail": "isbn13 is required"}, status=400)
            
        try:
            book = Book.objects.get(isbn13=isbn13)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=404)
            
        # 좋아요 토글 = BookPreference(like). 찜→좋아요 통합 (D28)
        pref = BookPreference.objects.filter(user=request.user, book=book).first()
        if pref and pref.sentiment == 'like':
            pref.delete()
            liked = False
        else:
            BookPreference.objects.update_or_create(
                user=request.user, book=book, defaults={'sentiment': 'like'}
            )
            liked = True

        return Response({
            "isbn13": book.isbn13,
            "liked": liked
        })


KDC_LABELS = {
    '0': '총류', '1': '철학', '2': '종교', '3': '사회과학', '4': '자연과학',
    '5': '기술과학', '6': '예술', '7': '언어', '8': '문학', '9': '역사',
}


class StarterBooksView(APIView):
    """온보딩 '표지픽'용 스타터셋.
    인기대출(LoanSignal scope='popular') 중 대상 도서관 소장 + 표지 있는 책을
    KDC 대분류(0~9)로 버킷팅해, 버킷별 인기순 1권씩 반환(주제 골고루).
    ?round=N : reshuffle(버킷별 N번째, 0부터). 외부 API 없이 DB만 사용."""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            round_idx = max(0, int(request.query_params.get('round', 0)))
        except (TypeError, ValueError):
            round_idx = 0

        # 인기 점수 (scope='popular') — 먼저 `python manage.py load_popularity` 실행 필요
        pop = dict(
            LoanSignal.objects.filter(scope='popular')
            .values_list('book_id', 'value')
        )
        if not pop:
            return Response({
                "round": round_idx, "count": 0, "books": [],
                "hint": "인기 데이터가 없습니다. 먼저 `python manage.py load_popularity`를 실행하세요.",
            })

        # 대상 도서관에 소장(has_book=True)된 책
        held = set(
            Holding.objects.filter(has_book=True)
            .values_list('book_id', flat=True)
        )
        eligible_ids = set(pop.keys()) & held

        books = (
            Book.objects
            .filter(isbn13__in=eligible_ids)
            .exclude(cover_url='')
            .exclude(kdc_code='')
        )

        # KDC 대분류(첫 자리)로 버킷팅 → 버킷별 인기순 정렬
        buckets = {}
        for b in books:
            digit = (b.kdc_code or '').strip()[:1]
            if digit not in KDC_LABELS:
                continue
            buckets.setdefault(digit, []).append(b)
        for digit in buckets:
            buckets[digit].sort(key=lambda bk: pop.get(bk.isbn13, 0), reverse=True)

        # round_idx 번째를 KDC 순서대로 한 권씩
        result = []
        for digit in sorted(buckets.keys()):
            lst = buckets[digit]
            if round_idx < len(lst):
                b = lst[round_idx]
                result.append({
                    "isbn13": b.isbn13,
                    "title": b.title,
                    "author": b.author,
                    "kdc_code": b.kdc_code,
                    "kdc_label": KDC_LABELS[digit],
                    "cover_url": b.cover_url,
                })

        return Response({"round": round_idx, "count": len(result), "books": result})


class TasteOnboardingView(APIView):
    """온보딩 '표지픽' 취향 저장 (D18 · 취향과 읽음 분리).
        body: {liked:[isbn], disliked:[isbn], topics:[...]}
    liked/disliked → BookPreference(취향 신호, 읽음 여부와 무관).
    topics → Profile.reading_goal. (좋아요는 toggle-like, 읽음은 내서재 완독으로 별도 관리 — D28.) 로그인 필요."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        liked = request.data.get('liked') or []
        disliked = request.data.get('disliked') or []
        topics = request.data.get('topics') or []

        # DB에 실제 존재하는 ISBN만 (오타/환각 차단)
        def existing(isbns):
            return list(
                Book.objects.filter(isbn13__in=isbns).values_list('isbn13', flat=True)
            )

        valid_liked = existing(liked)
        valid_disliked = existing(disliked)

        created = updated = 0

        def upsert(isbns, sentiment):
            nonlocal created, updated
            for isbn in isbns:
                _, was_created = BookPreference.objects.update_or_create(
                    user=user, book_id=isbn,
                    defaults={'sentiment': sentiment},
                )
                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        # 같은 책이 양쪽에 있으면 마지막(좋음)이 이김
        upsert(valid_disliked, 'dislike')
        upsert(valid_liked, 'like')

        # topics → Profile.reading_goal (R 단계에서 KDC 매핑에 활용)
        if topics:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.reading_goal = ", ".join(
                str(t).strip() for t in topics if str(t).strip()
            )[:200]
            profile.save(update_fields=['reading_goal'])

        return Response({
            "saved": {
                "liked": len(valid_liked),
                "disliked": len(valid_disliked),
                "topics": len(topics),
            },
            "prefs_created": created,
            "prefs_updated": updated,
        })
