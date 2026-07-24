from django.contrib import admin
from .models import SecurityReport
from accounts.permissions import has_role


@admin.register(SecurityReport)
class SecurityReportAdmin(admin.ModelAdmin):

    list_display = ('flight','officer','report_type','severity','status','created_at',)
    search_fields = ('flight__flight_number','officer__username','description',)
    list_filter = ('report_type','severity','status',)
    date_hierarchy = 'created_at'


    def has_view_permission(self, request, obj=None):

        return has_role(
            request.user,
            [
                'ADMIN',
                'SECURITY_OFFICER',
                'AIRPORT_MANAGER'
            ]
        )


    def has_add_permission(self, request):

        return has_role(
            request.user,
            [
                'ADMIN',
                'SECURITY_OFFICER'
            ]
        )


    def has_delete_permission(self, request, obj=None):

        return has_role(
            request.user,
            [
                'ADMIN'
            ]
        )