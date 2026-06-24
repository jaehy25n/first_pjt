from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .services import build_candidates
from .similarity import similar_books
from .llm import select_with_reasons
from django.db.models import Prefetch
from books.models import Book, Holding, LoanSignal
from books.serializers import BookCardSerializer
from books.availability import refresh_holdings, badge_map

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

        # 3단계: 보여줄 최종 N권만 정보나루 live 가용성 갱신 → 배지 재부착 (⑦c, D33)
        libraries = list(profile.libraries.all()) or ([profile.primary_library] if profile.primary_library else [])
        if libraries:
            isbns = [it['isbn13'] for it in items]
            refresh_holdings(isbns, libraries)
            badges = badge_map(isbns, libraries)
            for it in items:
                it['availability'] = badges.get(it['isbn13'])

        # 정상 반환
        return Response({
            "generated_at": timezone.now().isoformat(),
            "run_id": None,
            "items": items
        })

class DiscoverView(APIView):
    """홈 '취향 발견' + 온보딩 표지픽의 반복정제 엔진 (D30·D35). stateless:
    picks(누적 선택)·seen(이미 본 것)을 받아 picks 없으면 인기순 장르 흩뿌리기,
    있으면 고른 책들의 임베딩 이웃을 돌려준다. 전체 카탈로그 대상(도서관 무관, D35),
    가용성은 게이트가 아니라 배지(선택 도서관 있으면 부착, 없으면 null · D33). 데이터-only."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        picks = request.data.get('picks') or []
        seen = set(request.data.get('seen') or [])
        try:
            libraries = list(request.user.profile.libraries.all())
        except Exception:
            libraries = []
        # 도서관 미선택도 허용 — 취향 ⊥ 도서관(D35). 가용성은 배지(D33).
        exclude = seen | set(picks)

        if picks:
            # 고른 책들과 내용이 비슷한 책 (전체 카탈로그 임베딩 최근접, 본 것 제외)
            ranked = similar_books(picks, exclude=exclude, limit=80)
            cand = [i for i, _, _ in ranked]
        else:
            # 장르 흩뿌리기 — 전체 카탈로그를 인기순(popular+bestseller)으로 깔고
            # KDC 버킷당 2권 캡으로 다양성 한 스푼 (D35: 라운드1 무명책 방지)
            pop = {}
            for book_id, value in (LoanSignal.objects
                                   .filter(scope__in=['popular', 'bestseller'])
                                   .values_list('book_id', 'value')):
                pop[book_id] = pop.get(book_id, 0.0) + (value or 0.0)
            pool = list(
                Book.objects.filter(cover_url__gt='')
                .exclude(isbn13__in=exclude)
                .values_list('isbn13', 'kdc_code')
            )
            pool.sort(key=lambda t: pop.get(t[0], 0.0), reverse=True)
            cand, per_bucket = [], {}
            for isbn, kdc in pool:
                b = (kdc or '0')[:1]
                if per_bucket.get(b, 0) >= 2:
                    continue
                per_bucket[b] = per_bucket.get(b, 0) + 1
                cand.append(isbn)
                if len(cand) >= 12:
                    break

        # 표지 있는 책만(시각 피커, D35) + 선택 도서관 배지 prefetch
        books = Book.objects.filter(isbn13__in=cand, cover_url__gt='').prefetch_related(
            Prefetch('holdings', queryset=Holding.objects.filter(library__in=libraries).select_related('library'), to_attr='user_holding')
        )
        bmap = {b.isbn13: b for b in books}
        ordered = [bmap[i] for i in cand if i in bmap][:12]  # 랭킹 순서 유지
        data = BookCardSerializer(ordered, many=True, context={'libraries': libraries}).data
        return Response({"books": data, "empty": not data})
