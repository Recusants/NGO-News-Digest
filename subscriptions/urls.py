from django.urls import path
from . import views

urlpatterns = [
    # Subscription pages
    path('subscribe/', views.subscribe_page, name='subscribe_page'),
    path('subscribe/action/', views.subscribe, name='subscribe'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('unsubscribe/', views.unsubscribe_page, name='unsubscribe_page'),
    path('unsubscribe/action/', views.unsubscribe, name='unsubscribe'),
    
    # Subscriber management
    path('subscribers/', views.subscriber_list, name='subscriber_list'),
    path('subscribers/export/', views.export_subscribers, name='export_subscribers'),
    path('unsubscribe/link/<str:email>/', views.unsubscribe_link, name='unsubscribe_link'),
    
    # API endpoints
    path('subscriber/details/', views.get_subscriber_details, name='get_subscriber_details'),
    path('subscriber/update/', views.update_subscriber, name='update_subscriber'),
]