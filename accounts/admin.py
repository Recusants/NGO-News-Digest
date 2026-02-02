from django.contrib import admin

from .models import *

admin.site.register(User)
admin.site.register(SiteInfo)
admin.site.register(Subscriber)
admin.site.register(TeamMember)
