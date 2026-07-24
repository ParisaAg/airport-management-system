from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = ('user','title','notification_type','is_read','created_at',)
    search_fields = ('title','message','user__username',)
    list_filter = ('notification_type','is_read',)
    date_hierarchy = 'created_at'