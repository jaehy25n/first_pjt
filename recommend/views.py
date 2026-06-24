import random

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .services import build_candidates
from .similarity import similar_books
from .llm import select_with_reasons
from django.db.models import Prefetch
from books.models import Library, Book, Holding
from books.serializers import BookCardSerializer

class RecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        seed_isbn13 = request.data.get('seed_isbn13')
        
        try:
            limit = int(request.data.get('limit', 5))
        except ValueError:
            limit = 5

        user = request.user
        try:
            profile = user.profile
        except Exception:
            return Response({"detail": "User has no profile. Please set up your profile first."}, status=400)

        # 1단계: DB에서 후보 생성
        candidates = build_candidates(user, seed_isbn13=seed_isbn13, limit=limit)
        
        # 2단계: LLM으로 최종 선별
        items = select_with_reasons(candidates, profile, limit=limit, seed_isbn13=seed_isbn13)
        
        # 결과가 0건인 경우
        if not items:
            return Response({
                "items": [],
                "empty": True,
                "hint": "관심사를 넓히거나 도서관을 추가해 보세요"
            })
            
        # 정상 반환
        return Response({
            "generated_at": timezone.now().isoformat(),
            "run_id": None,
            "items": items
        })

class DiscoverView(APIView):
    """홈 '반복정제 발견' (D30). stateless: picks(누적 선택)·seen(이미 본 것)을 받아
    picks 없으면 장르 흩뿌리기, 있으면 고른 책들의 임베딩 이웃을 돌려준다. 데이터-only."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        picks = request.data.get('picks') or []
        seen = set(request.data.get('seen') or [])
        try:
            libraries = list(request.user.profile.libraries.all())
        except Exception:
            libraries = []
        if not libraries:
            return Response({"books": [], "empty": True, "hint": "먼저 온보딩에서 도서관을 선택해 주세요"})

        owned = set(Holding.objects.filter(library__in=libraries, has_book=True).values_list('book_id', flat=True))
        exclude = seen | set(picks)

        if picks:
            # 고른 책들과 내용이 비슷한 책 (임베딩 최근접, 본 것 제외)
            ranked = similar_books(picks, exclude=exclude, limit=80)
            isbns = [i for i, _, _ in ranked if i in owned][:12]
        else:
            # 장르 흩뿌리기 — KDC 버킷당 최대 2권으로 다양하게
            pool = list(
                Book.objects.filter(isbn13__in=owned, cover_url__gt='')
                .exclude(isbn13__in=exclude)
                .values_list('isbn13', 'kdc_code')
            )
            random.shuffle(pool)
            isbns, per_bucket = [], {}
            for isbn, kdc in pool:
                b = (kdc or '0')[:1]
                if per_bucket.get(b, 0) >= 2:
                    continue
                per_bucket[b] = per_bucket.get(b, 0) + 1
                isbns.append(isbn)
                if len(isbns) >= 12:
                    break

        books = Book.objects.filter(isbn13__in=isbns).prefetch_related(
            Prefetch('holdings', queryset=Holding.objects.filter(library__in=libraries).select_related('library'), to_attr='user_holding')
        )
        bmap = {b.isbn13: b for b in books}
        ordered = [bmap[i] for i in isbns if i in bmap]  # 랭킹 순서 유지
        data = BookCardSerializer(ordered, many=True, context={'libraries': libraries}).data
        return Response({"books": data})


class LibraryVisitView(APIView):
    def get(self, request):
        lib_code = request.query_params.get('lib_code')
        if not lib_code:
            return Response({"detail": "lib_code 파라미터가 필요합니다."}, status=400)
            
        try:
            library = Library.objects.get(lib_code=lib_code)
        except Library.DoesNotExist:
            return Response({"detail": "도서관을 찾을 수 없습니다."}, status=404)
            
        # 해당 도서관에 소장되어 있고(has_book) 지금 대출가능한(loan_available) 책 20권을 가져옴
        books = Book.objects.filter(
            holdings__library=library,
            holdings__loan_available=True
        ).prefetch_related(
            Prefetch('holdings', queryset=Holding.objects.filter(library=library), to_attr='user_holding')
        ).distinct()[:20]
        
        serializer = BookCardSerializer(books, many=True, context={'primary_library': library})
        return Response(serializer.data)
