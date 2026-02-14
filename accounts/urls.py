from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # AJAX
    path('send-reset-code/', views.send_reset_code, name='send_reset_code'),
    path('verify-reset-code/', views.verify_reset_code, name='verify_reset_code'),



    # User Management (Admin only)
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    
    # Profile (All authenticated users)
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/team/', views.team_profile_edit, name='team_profile_edit'),

]
