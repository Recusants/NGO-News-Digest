from django.urls import path
from . import views

urlpatterns = [
    # html
    path('', views.home, name='home'),

    path('about_page', views.about_page, name='about_page'),
    
    path('contact_page', views.contact_page, name='contact_page'),

    path('story_page/<int:pk>', views.story_page, name='story_page'),
    path('stories_page', views.stories_page, name='stories_page'),
    # path('story/<int:pk>', views.story, name='story'),

    path('stories', views.stories, name='stories'),
    path('get_latest_stories', views.get_latest_stories, name='get_latest_stories'),
    path('get_top_stories', views.get_top_stories, name='get_top_stories'),
    path('get_editors_pick_stories', views.get_editors_pick_stories, name='get_editors_pick_stories'),

    path('upload/', views.upload_blog_post, name='upload_blog_post'),
    path('success/', views.success_view, name='success_page'),


    path('vacancies_page', views.vacancies_page, name='vacancies_page'),
    path('vacancies/', views.vacancy_list, name='vacancy_list'),
    path('vacancies/<int:pk>/', views.vacancy_detail, name='vacancy_detail'),
    path('vacancies/upload/', views.upload_vacancy, name='upload_vacancy'),
    path('api/vacancies/', views.get_vacancies, name='get_vacancies'),
    path('api/vacancies/upload/', views.ajax_upload_vacancy, name='ajax_upload_vacancy'),
    
    # Notices
    path('notices_page', views.notices_page, name='notices_page'),
    path('notices/', views.notice_list, name='notice_list'),
    path('notices/<int:pk>/', views.notice_detail, name='notice_detail'),
    path('notices/upload/', views.upload_notice, name='upload_notice'),
    path('api/notices/', views.get_notices, name='get_notices'),
    path('api/notices/upload/', views.ajax_upload_notice, name='ajax_upload_notice'),

    path('editors_page', views.editors_page, name='editors_page'),
]