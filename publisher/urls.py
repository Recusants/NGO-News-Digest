from django.urls import path
from . import views

urlpatterns = [

    # ==================== HTML PAGES ====================
    path('', views.home, name='home'),
    path('about/', views.about_page, name='about_page'),
    path('contact_page/', views.contact_page, name='contact_page'),
    path('team_page/', views.team_page, name='team_page'),
    path('team_member_page/<int:pk>', views.team_member_page, name='team_member_page'),
    
    # ==================== STORY PAGES ====================
    path('story_page/<int:pk>/', views.story_page, name='story_page'),
    path('stories_page/', views.stories_page, name='stories_page'),
    
    # ==================== STORY APIS ====================
    path('stories/', views.stories, name='stories'),
    path('get_latest_stories/', views.get_latest_stories, name='get_latest_stories'),
    path('get_top_stories/', views.get_top_stories, name='get_top_stories'),
    path('get_editors_pick_stories/', views.get_editors_pick_stories, name='get_editors_pick_stories'),
    
    # ==================== BLOG POST MANAGEMENT ====================
    path('upload/', views.upload_blog_post, name='upload_blog_post'),
    path('success/', views.success_page, name='success_page'),
    
    # ==================== VACANCIES ====================
    path('vacancies_page/', views.vacancies_page, name='vacancies_page'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('vacancy_page/<int:pk>/', views.vacancy_page, name='vacancy_page'),
    path('vacancies/upload/', views.upload_vacancy, name='upload_vacancy'),
    
    # Vacancy APIs
    path('api/vacancies/', views.get_vacancies, name='get_vacancies'),
    path('api/vacancies/upload/', views.ajax_upload_vacancy, name='ajax_upload_vacancy'),
    
    # ==================== NOTICES ====================
    path('notices_page/', views.notices_page, name='notices_page'),
    path('notices/', views.notices, name='notices'),
    path('notice_page/<int:pk>/', views.notice_page, name='notice_page'),
    path('notices/upload/', views.upload_notice, name='upload_notice'),
    
    # Notice APIs
    path('api/notices/', views.get_notices, name='get_notices'),
    path('api/notices/upload/', views.ajax_upload_notice, name='ajax_upload_notice'),
    
    # ==================== SUBSCRIPTIONS ====================
    path('subscribers/', views.subscriber_list, name='subscriber_list'),
    path('unsubscribe/<str:email>/', views.unsubscribe_link, name='unsubscribe'),


    path('privacy-terms/', views.privacy_terms_page, name='privacy_terms_page'),
    path('privacy-terms/download/', views.download_privacy_terms, name='download_privacy_terms'),
]