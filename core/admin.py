from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import Bid, Notification, Project, Rating, User

admin.site.register(User, UserAdmin)
admin.site.register(Project)
admin.site.register(Bid)
admin.site.register(Rating)
admin.site.register(Notification)
