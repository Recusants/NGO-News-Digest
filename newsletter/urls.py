from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include

def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path('sentry-debug/', trigger_error),
    path('admin/', admin.site.urls),

    path('accounts/', include('accounts.urls')),
    
    path('', include('publisher.urls')),
    path('publisher/', include('publisher.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('management/', include('management.urls')),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
