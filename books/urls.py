from django.urls import path
from . import views

urlpatterns = [
    path('libraries/', views.LibraryListView.as_view(), name='library_list'),
]
