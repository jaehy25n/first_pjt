from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, Interest, ReadingLog

admin.site.register(User, UserAdmin)
admin.site.register(Profile)
admin.site.register(Interest)

@admin.register(ReadingLog)
class ReadingLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'rating', 'created')
    list_filter = ('status',)
    search_fields = ('user__username', 'book__title')
