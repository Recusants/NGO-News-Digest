# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Story URLs
    # path('stories/<int:pk>/delete/', views.StoryDeleteView.as_view(), name='story_delete'),
    # path('stories/<int:pk>/publish/', views.story_publish, name='story_publish'),
    # path('stories/<int:pk>/unpublish/', views.story_unpublish, name='story_unpublish'),
    # path('stories/create/', views.story_create, name='story_create'),
    # path('stories/<int:pk>/edit/', views.story_edit, name='story_edit'),
    # path('stories/cbv/create/', views.StoryCreateView.as_view(), name='story_create_cbv'),
    # path('stories/cbv/<int:pk>/edit/', views.StoryUpdateView.as_view(), name='story_edit_cbv'),
    # path('stories/', views.StoryListView.as_view(), name='story_list'),
    # path('vacancies/', views.VacancyListView.as_view(), name='vacancy_list'),
    
    # Vacancy URLs
    path('vacancies/<int:pk>/delete/', views.VacancyDeleteView.as_view(), name='vacancy_delete'),
    path('vacancies/<int:pk>/activate/', views.vacancy_activate, name='vacancy_activate'),
    path('vacancies/<int:pk>/deactivate/', views.vacancy_deactivate, name='vacancy_deactivate'),
    path('vacancies/<int:pk>/feature/', views.vacancy_feature, name='vacancy_feature'),
    path('vacancies/<int:pk>/unfeature/', views.vacancy_unfeature, name='vacancy_unfeature'),
    path('vacancies/create/', views.vacancy_create, name='vacancy_create'),
    path('vacancies/<int:pk>/edit/', views.vacancy_edit, name='vacancy_edit'),
    path('vacancies/cbv/create/', views.VacancyCreateView.as_view(), name='vacancy_create_cbv'),
    path('vacancies/cbv/<int:pk>/edit/', views.VacancyUpdateView.as_view(), name='vacancy_edit_cbv'),
    
    # Notice URLs
    path('notices/<int:pk>/delete/', views.NoticeDeleteView.as_view(), name='notice_delete'),
    path('notices/<int:pk>/activate/', views.notice_activate, name='notice_activate'),
    path('notices/<int:pk>/deactivate/', views.notice_deactivate, name='notice_deactivate'),
    path('notices/<int:pk>/mark-important/', views.notice_mark_important, name='notice_mark_important'),
    path('notices/<int:pk>/unmark-important/', views.notice_unmark_important, name='notice_unmark_important'),
    path('notices/create/', views.notice_create, name='notice_create'),
    path('notices/<int:pk>/edit/', views.notice_edit, name='notice_edit'),
    path('notices/cbv/create/', views.NoticeCreateView.as_view(), name='notice_create_cbv'),
    path('notices/cbv/<int:pk>/edit/', views.NoticeUpdateView.as_view(), name='notice_edit_cbv'),
    path('notices/', views.NoticeListView.as_view(), name='notice_list'),

    
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/cbv/create/', views.CategoryCreateView.as_view(), name='category_create_cbv'),
    path('categories/cbv/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit_cbv'),
    
    # Attachment URLs
    path('attachments/upload/', views.quick_attachment_upload, name='attachment_upload'),
    path('attachments/bulk/', views.bulk_attachment_upload, name='bulk_attachment_upload'),
    path('attachments/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
    path('attachments/reorder/', views.reorder_attachments, name='reorder_attachments'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my-content/', views.my_content, name='my_content'),


]