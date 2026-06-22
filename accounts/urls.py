from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/onboarding/', views.ProfileOnboardingView.as_view(), name='profile_onboarding'),
    path('interests/', views.InterestListView.as_view(), name='interest_list'),
    path('onboarding/starter-books', views.StarterBooksView.as_view(), name='onboarding_starter_books'),
    path('onboarding/taste', views.TasteOnboardingView.as_view(), name='onboarding_taste'),
    path('library', views.LibraryLogView.as_view(), name='library_log'),
    path('library/log', views.LibraryLogCreateView.as_view(), name='library_log_create'),
    path('library/toggle-wish', views.LibraryToggleWishView.as_view(), name='library_toggle_wish'),
]
