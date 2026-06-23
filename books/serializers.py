from rest_framework import serializers
from .models import Library, Book, Holding
from accounts.models import Profile

class LibrarySearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = ['lib_code', 'name', 'region']

class BookCardSerializer(serializers.ModelSerializer):
    availability = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['isbn13', 'title', 'author', 'kdc_code', 'cover_url', 'availability']

    def get_availability(self, obj):
        # 선택 도서관들(union) 기준. 단일 primary_library만 줘도 하위호환 (D29)
        libraries = self.context.get('libraries')
        if not libraries:
            single = self.context.get('primary_library')
            libraries = [single] if single else []
        if not libraries:
            return None

        # holdings는 user_holding으로 prefetch됨(선택 도서관들로 필터·select_related('library'))
        user_holdings = getattr(obj, 'user_holding', [])
        owned = [h for h in user_holdings if h.has_book]
        available = [h for h in owned if h.loan_available]

        if available:
            status, chosen = 'available', available[0].library  # 빌릴 수 있는 곳 우선
        elif owned:
            status, chosen = 'loaned', owned[0].library
        else:
            status, chosen = 'none', libraries[0]

        return {
            "lib_code": chosen.lib_code,
            "library_name": chosen.name,
            "status": status
        }

class HoldingSerializer(serializers.ModelSerializer):
    lib_code = serializers.CharField(source='library.lib_code', read_only=True)
    library_name = serializers.CharField(source='library.name', read_only=True)

    class Meta:
        model = Holding
        fields = ['lib_code', 'library_name', 'has_book', 'loan_available', 'snapshot_at']

class BookDetailSerializer(serializers.ModelSerializer):
    holdings = HoldingSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = [
            'isbn13', 'title', 'author', 'publisher', 'pub_year', 
            'kdc_code', 'cover_url', 'description', 'page_count', 'holdings'
        ]
