from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    # STORY URLS
    path('stories/', views.story_list, name='story_list'),
    path('stories/create/', views.story_create, name='story_create'),
    path('stories/<int:pk>/', views.story_detail, name='story_detail'),
    path('stories/<int:pk>/edit/', views.story_edit, name='story_edit'),
    path('stories/<int:pk>/publish/', views.story_publish, name='story_publish'),
    path('stories/<int:pk>/unpublish/', views.story_unpublish, name='story_unpublish'),
    path('stories/<int:pk>/delete/', views.story_delete, name='story_delete'),
    
    # VACANCY URLS
    path('vacancy/create/', views.vacancy_create, name='vacancy_create'),
    path('vacancies/', views.vacancy_list, name='vacancy_list'),
    path('vacancy/edit/<int:pk>/', views.vacancy_edit, name='vacancy_edit'),
    path('vacancy/<int:pk>/toggle-active/', views.vacancy_toggle_active, name='vacancy_toggle_active'),
    path('vacancy/<int:pk>/toggle-featured/', views.vacancy_toggle_featured, name='vacancy_toggle_featured'),
    path('vacancy/<int:pk>/delete/', views.vacancy_delete, name='vacancy_delete'),
    path('attachment/<int:pk>/delete/', views.attachment_delete, name='attachment_delete'),


    # NOTICE URLS
    path('notices/', views.notice_list, name='notice_list'),
    path('notices/create/', views.notice_create, name='notice_create'),
    path('notices/<int:pk>/', views.notice_detail, name='notice_detail'),
    path('notices/<int:pk>/edit/', views.notice_edit, name='notice_edit'),
    path('notices/<int:pk>/activate/', views.notice_activate, name='notice_activate'),
    path('notices/<int:pk>/deactivate/', views.notice_deactivate, name='notice_deactivate'),
    path('notices/<int:pk>/mark-important/', views.notice_mark_important, name='notice_mark_important'),
    path('notices/<int:pk>/unmark-important/', views.notice_unmark_important, name='notice_unmark_important'),
    path('notices/<int:pk>/delete/', views.notice_delete, name='notice_delete'),
    path('notice/<int:pk>/toggle-active/', views.notice_toggle_active, name='notice_toggle_active'),
    path('notice/<int:pk>/toggle-important/', views.notice_toggle_important, name='notice_toggle_important'),
    
    
    # CATEGORY URLS
    path('category/create/ajax/', views.category_create_ajax, name='category_create_ajax'),

    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # ATTACHMENT URLS
    path('attachments/upload/', views.quick_attachment_upload, name='attachment_upload'),
    path('attachments/bulk/', views.bulk_attachment_upload, name='bulk_attachment_upload'),
    path('attachments/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
    path('attachments/reorder/', views.reorder_attachments, name='reorder_attachments'),
    
    # DASHBOARD & USER CONTENT URLS
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my-content/', views.my_content, name='my_content'),
]