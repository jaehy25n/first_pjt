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
        # We assume primary_library is passed in context to avoid N+1 profile queries
        library = self.context.get('primary_library')
        if not library:
            return None
            
        # We assume holdings are prefetched to 'user_holding'
        user_holdings = getattr(obj, 'user_holding', [])
        if not user_holdings:
            status = 'none'
        else:
            holding = user_holdings[0]
            if not holding.has_book:
                status = 'none'
            elif holding.loan_available:
                status = 'available'
            else:
                status = 'loaned'
                
        return {
            "lib_code": library.lib_code,
            "library_name": library.name,
            "status": status
        }
