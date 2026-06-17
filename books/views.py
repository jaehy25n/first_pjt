from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Prefetch, Q
from .models import Library, Book, Holding
from .serializers import LibrarySearchSerializer, BookCardSerializer
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

        # Prefetch holdings for the user's primary library
        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.profile
                library = profile.primary_library
                if library:
                    holding_prefetch = Prefetch(
                        'holdings',
                        queryset=Holding.objects.filter(library=library),
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
                context['primary_library'] = self.request.user.profile.primary_library
            except Profile.DoesNotExist:
                pass
        return context
