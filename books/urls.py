from django.urls import path
from . import views

urlpatterns = [
    path('libraries/', views.LibraryListView.as_view(), name='library_list'),
    path('libraries/nearby/', views.LibraryNearbyView.as_view(), name='library_nearby'),
    path('books/', views.BookListView.as_view(), name='book_list'),
    path('books/<str:isbn13>/', views.BookDetailView.as_view(), name='book_detail'),
    path('books/<str:isbn13>/availability/', views.BookAvailabilityView.as_view(), name='book_availability'),
    path('books/<str:isbn13>/seoul-libraries/', views.BookSeoulLibrariesView.as_view(), name='book_seoul_libraries'),
    path('books/<str:isbn13>/usage/', views.BookUsageView.as_view(), name='book_usage'),
]
