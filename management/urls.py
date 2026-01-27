from django.urls import path
from . import views

urlpatterns = [
    path('', views.management_page, name='management_page'),
    path('management_page', views.management_page, name='management_page'),
    path('create_story', views.create_story, name='create_story_page'),
]