from django.urls import path
from . import views

urlpatterns = [
    path('blog/create/', views.blog_create, name='blog_create'),
    path('blog/<int:pk>/edit/', views.blog_edit, name='blog_edit'),


    path('', views.management_page, name='management_page'),
    path('management_page', views.management_page, name='management_page'),
    path('management_story_list_page', views.management_story_list_page, name='management_story_list_page'),
    path('management_stories', views.management_stories, name='management_stories'),
]