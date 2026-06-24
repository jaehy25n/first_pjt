import math

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Prefetch, Q
from .models import Library, Book, Holding
from .serializers import LibrarySearchSerializer, BookCardSerializer, BookDetailSerializer, HoldingSerializer
from .availability import refresh_holdings, libs_for_book, book_usage
from accounts.models import Profile

class LibraryListView(APIView):
    def get(self, request):
        queryset = Library.objects.all()
        q = request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(name__icontains=q)
        serializer = LibrarySearchSerializer(queryset, many=True)
        return Response(serializer.data)

class BookPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class BookListView(ListAPIView):
    serializer_class = BookCardSerializer
    pagination_class = BookPagination

    def get_queryset(self):
        queryset = Book.objects.all().order_by('-pub_year', 'title')
        q = self.request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(author__icontains=q))

        # 선택 도서관들(union) 소장 prefetch (D29)
        if self.request.user.is_authenticated:
            try:
                libraries = list(self.request.user.profile.libraries.all())
                if libraries:
                    holding_prefetch = Prefetch(
                        'holdings',
                        queryset=Holding.objects.filter(library__in=libraries).select_related('library'),
                        to_attr='user_holding'
                    )
                    queryset = queryset.prefetch_related(holding_prefetch)
            except Profile.DoesNotExist:
                pass

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            try:
                context['libraries'] = list(self.request.user.profile.libraries.all())
            except Profile.DoesNotExist:
                pass
        return context

class BookDetailView(RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookDetailSerializer
    lookup_field = 'isbn13'

class BookAvailabilityView(APIView):
    def get(self, request, isbn13):
        # 내 선택 도서관만 정보나루로 live 갱신 (⑦c, D33 — 보여줄 책 1권 × 내 도서관)
        if request.user.is_authenticated:
            try:
                libraries = list(request.user.profile.libraries.all())
            except Exception:
                libraries = []
            if libraries:
                refresh_holdings([isbn13], libraries)
        holdings = Holding.objects.filter(book__isbn13=isbn13).select_related('library')
        serializer = HoldingSerializer(holdings, many=True)
        return Response(serializer.data)


class BookSeoulLibrariesView(APIView):
    """이 책을 소장한 서울 도서관 목록 (libSrchByBook, region=11).
    D33③ — '서울 어디서 빌리나' 목록만(인기책=소장관 수십 → 전수 bookExist 금지). 실패 시 빈 목록."""
    def get(self, request, isbn13):
        libs = libs_for_book(isbn13)
        return Response({"count": len(libs), "libraries": libs})


class BookUsageView(APIView):
    """책 이용분석 — 연관 키워드 + 월별 대출 추이 (usageAnalysisList lazy 1콜). ⑧, D33 정보나루 B."""
    def get(self, request, isbn13):
        return Response(book_usage(isbn13))


class LibraryNearbyView(APIView):
    """내 위치(lat,lng) 기준 가까운 도서관 N개 — Haversine 거리정렬 (D34 Tier1). 외부 API 없음."""
    def get(self, request):
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response({"detail": "lat, lng 쿼리 파라미터가 필요합니다."}, status=400)
        try:
            n = min(50, max(1, int(request.query_params.get('n', 10))))
        except (TypeError, ValueError):
            n = 10

        def haversine(la1, lo1, la2, lo2):
            R = 6371.0  # km
            p1, p2 = math.radians(la1), math.radians(la2)
            dphi = math.radians(la2 - la1)
            dlmb = math.radians(lo2 - lo1)
            a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
            return 2 * R * math.asin(math.sqrt(a))

        out = []
        for lib in Library.objects.filter(latitude__isnull=False, longitude__isnull=False):
            out.append({
                "lib_code": lib.lib_code,
                "name": lib.name,
                "address": lib.address,
                "latitude": lib.latitude,
                "longitude": lib.longitude,
                "distance_km": round(haversine(lat, lng, lib.latitude, lib.longitude), 2),
            })
        out.sort(key=lambda x: x["distance_km"])
        return Response({"count": min(n, len(out)), "libraries": out[:n]})
