from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .services import build_candidates
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
