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
