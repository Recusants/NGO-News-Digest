from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('login_page/', views.login_page, name='login_page'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('ajax_send_reset_email/', views.ajax_send_reset_email, name='ajax_send_reset_email'),

    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Team Member URLs
    path('team-members/', views.team_member_list, name='team_member_list'),
    path('team-members/create/', views.team_member_create, name='team_member_create'),
    path('team-members/<int:pk>/edit/', views.team_member_edit, name='team_member_edit'),
    path('team-members/<int:pk>/delete/', views.team_member_delete, name='team_member_delete'),
    path('team-members/<int:pk>/toggle-active/', views.team_member_toggle_active, name='team_member_toggle_active'),
    
    # Site Settings URLs
    path('site-settings/', views.site_settings, name='site_settings'),


    # Subscriber URLs
    path('subscribers/', views.subscriber_list, name='subscriber_list'),
    path('subscribers/<int:pk>/delete/', views.subscriber_delete, name='subscriber_delete'),
    path('subscribers/<int:pk>/toggle-active/', views.subscriber_toggle_active, name='subscriber_toggle_active'),
    path('subscribers/<int:pk>/verify/', views.subscriber_verify, name='subscriber_verify'),
    path('subscribers/<int:pk>/unsubscribe/', views.subscriber_unsubscribe, name='subscriber_unsubscribe'),
    path('subscribers/bulk-delete/', views.bulk_delete_subscribers, name='bulk_delete_subscribers'),

    path('subscribers/export-csv/', views.export_subscribers_csv, name='export_subscribers_csv'),


    
    # Django's built-in password reset views
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='management/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='management/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='management/password_reset_complete.html'
    ), name='password_reset_complete'),


     # Vacancy URLs
    path('vacancies/', views.vacancy_list, name='vacancy_list'),
    path('vacancies/create/', views.vacancy_create, name='vacancy_create'),
    path('vacancies/<int:pk>/edit/', views.vacancy_edit, name='vacancy_edit'),
    path('vacancies/<int:pk>/delete/', views.vacancy_delete, name='vacancy_delete'),
    path('vacancies/<int:pk>/toggle-active/', views.vacancy_toggle_active, name='vacancy_toggle_active'),
    
    # Notice URLs
    path('notices/', views.notice_list, name='notice_list'),
    path('notices/create/', views.notice_create, name='notice_create'),
    path('notices/<int:pk>/edit/', views.notice_edit, name='notice_edit'),
    path('notices/<int:pk>/delete/', views.notice_delete, name='notice_delete'),
    path('notices/<int:pk>/toggle-active/', views.notice_toggle_active, name='notice_toggle_active'),

    
    path('blog/create/', views.blog_create, name='blog_create'),
    path('blog/<int:pk>/edit/', views.blog_edit, name='blog_edit'),


    path('', views.management_page, name='management_page'),
    path('management_page', views.management_page, name='management_page'),
    path('management_story_list_page', views.management_story_list_page, name='management_story_list_page'),
    path('management_stories', views.management_stories, name='management_stories'),
]