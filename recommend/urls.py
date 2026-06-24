from django.urls import path
from .views import RecommendationView, LibraryVisitView, DiscoverView

urlpatterns = [
    path('recommendations/visit', LibraryVisitView.as_view(), name='recommendation-visit'),
    path('recommendations', RecommendationView.as_view(), name='recommendations'),
    path('discover', DiscoverView.as_view(), name='discover'),
]
