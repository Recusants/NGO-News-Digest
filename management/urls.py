from django.urls import path
from . import views

urlpatterns = [
    path('', views.management_page, name='management_page'),
    path('management_page', views.management_page, name='management_page'),
    path('write_article_page', views.write_article_page, name='write_article_page'),
]