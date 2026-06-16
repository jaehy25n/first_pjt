from django.contrib import admin
from .models import Library, Book, Holding

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('lib_code', 'name', 'region')
    search_fields = ('name', 'lib_code')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('isbn13', 'title', 'author', 'publisher', 'kdc_code')
    search_fields = ('title', 'author', 'isbn13')

@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('library', 'book', 'has_book', 'loan_available', 'snapshot_at')
    list_filter = ('has_book', 'loan_available', 'library')
    search_fields = ('book__title', 'book__isbn13')
