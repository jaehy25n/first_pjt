from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, Interest, ReadingLog, BookPreference

admin.site.register(User, UserAdmin)
admin.site.register(Profile)
admin.site.register(Interest)

@admin.register(ReadingLog)
class ReadingLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'rating', 'created')
    list_filter = ('status',)
    search_fields = ('user__username', 'book__title')

@admin.register(BookPreference)
class BookPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'sentiment', 'created')
    list_filter = ('sentiment',)
    search_fields = ('user__username', 'book__title')
