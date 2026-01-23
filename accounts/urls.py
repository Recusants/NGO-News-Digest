from django.urls import path
from .import views


urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # User Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('saved-stories/', views.saved_stories_view, name='saved_stories'),
    path('save-story/<int:story_id>/', views.save_story_view, name='save_story'),
    
    
    path('about', views.about_page, name='about_page'),
    path('contact/', views.contact_page, name='contact_page'),
    path('team/<str:username>/', views.team_member_detail, name='team_member_detail'),
    
    # Management (staff only)
    path('admin/site-info/', views.manage_site_info, name='manage_site_info'),
    path('admin/team/', views.manage_team, name='manage_team'),
    path('admin/team/add/', views.add_team_member, name='add_team_member'),
    path('admin/team/<int:user_id>/edit/', views.edit_team_member, name='edit_team_member'),
    path('admin/team/<int:user_id>/delete/', views.delete_team_member, name='delete_team_member'),
]