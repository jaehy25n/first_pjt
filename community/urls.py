from django.urls import path
from . import views

app_name = 'community'
urlpatterns = [
    path('', views.article_list, name='article_list'),
    path('<int:article_id>/', views.article_detail, name='article_detail'),
    path('<int:article_id>/like/', views.article_like, name='article_like'),
    path('<int:article_id>/comments/', views.comment_create, name='comment_create'),
    path('<int:article_id>/comments/<int:comment_id>/', views.comment_delete, name='comment_delete'),
    path('me/', views.my_articles, name='my_articles'),
]
