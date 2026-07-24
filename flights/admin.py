from urllib import request

from django.contrib import admin
from .models import Flight, GateAssignment
from accounts.permissions import has_role

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):

    list_display = ('flight_number','airline','origin','destination','departure_time','status',)
    search_fields = ('flight_number','airline__name','origin__name','destination__name',)
    list_filter = ('status','airline','origin','destination',)
    date_hierarchy = 'departure_time'
    def has_view_permission(self, request, obj=None):

        return has_role(
            request.user,
            [
                'ADMIN',
                'AIRPORT_MANAGER',
                'AIRLINE_OPERATOR'
            ]
        )


    def has_add_permission(self, request):

        return has_role(
            request.user,
            [
                'ADMIN',
                'AIRPORT_MANAGER'
            ]
        )
    def get_queryset(self, request):

        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if request.user.role == 'AIRLINE_OPERATOR':

            return qs.filter(
                airline=request.user.airline
            )

        return qs

    def has_change_permission(self, request, obj=None):

        return has_role(
            request.user,
            [
                'ADMIN',
                'AIRPORT_MANAGER',
                'AIRLINE_OPERATOR'
            ]
        )


    def has_delete_permission(self, request, obj=None):

        return has_role(
            request.user,
            [
                'ADMIN'
            ]
        )
    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if (
            db_field.name == "airline"
            and request.user.role == "AIRLINE_OPERATOR"
        ):

            kwargs["queryset"] = request.user.airline.__class__.objects.filter(
                id=request.user.airline.id
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs
        )

@admin.register(GateAssignment)
class GateAssignmentAdmin(admin.ModelAdmin):

    list_display = ('flight','gate','status','assigned_time','released_time',)
    search_fields = ('flight__flight_number','gate__code',)
    list_filter = ('status','gate',)
    date_hierarchy = 'assigned_time'