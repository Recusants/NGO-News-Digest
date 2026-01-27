from django.contrib import admin

from .models import *

admin.site.register(BlogPost)
admin.site.register(Category)
admin.site.register(Vacancy)
admin.site.register(Notice)