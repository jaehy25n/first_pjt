from django.urls import path
from . import views

urlpatterns = [
    path('libraries/', views.LibraryListView.as_view(), name='library_list'),
    path('books/', views.BookListView.as_view(), name='book_list'),
]
