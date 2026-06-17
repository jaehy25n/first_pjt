from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .services import build_candidates
from .llm import select_with_reasons

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
