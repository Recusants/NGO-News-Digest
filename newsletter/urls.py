from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/', include('accounts.urls')),
    
    path('', include('publisher.urls')),
    path('publisher/', include('publisher.urls')),
    path('subscriptions/', include('subscriptions.urls')),
]



