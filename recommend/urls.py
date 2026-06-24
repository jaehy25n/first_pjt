from django.urls import path
from .views import RecommendationView, DiscoverView

urlpatterns = [
    path('recommendations', RecommendationView.as_view(), name='recommendations'),
    path('discover', DiscoverView.as_view(), name='discover'),
]
