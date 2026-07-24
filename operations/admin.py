from django.contrib import admin
from .models import OperationType,GroundOperation
from accounts.permissions import has_role



@admin.register(OperationType)
class OperationTypeAdmin(admin.ModelAdmin):

    list_display = ('name','is_active','created_at',)

    search_fields = ('name',)

    list_filter = ('is_active',)


@admin.register(GroundOperation)
class GroundOperationAdmin(admin.ModelAdmin):

    list_display = ('flight','operation_type','assigned_staff','status','start_time','end_time',)
    search_fields = ('flight__flight_number','operation_type__name','assigned_staff__username',)

    list_filter = ('status','operation_type',)

    date_hierarchy = 'start_time'

    def has_view_permission(self, request, obj=None):

        return has_role(
            request.user,
            [
                'ADMIN',
                'AIRPORT_MANAGER',
                'GROUND_STAFF'
            ]
        )


    def has_add_permission(self, request):

        return has_role(
            request.user,
            [
                'ADMIN',
                'AIRPORT_MANAGER',
                'GROUND_STAFF'
            ]
        )


    def has_change_permission(self, request, obj=None):

        return has_role(
            request.user,
            [
                'ADMIN',
                'AIRPORT_MANAGER',
                'GROUND_STAFF'
            ]
        )


    def has_delete_permission(self, request, obj=None):

        return has_role(
            request.user,
            [
                'ADMIN'
            ]
        )