from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/onboarding/', views.ProfileOnboardingView.as_view(), name='profile_onboarding'),
]
