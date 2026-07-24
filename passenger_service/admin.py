from django.contrib import admin
from .models import PassengerRequest


@admin.register(PassengerRequest)
class PassengerRequestAdmin(admin.ModelAdmin):

    list_display = (
        'flight',
        'passenger_name',
        'request_type',
        'priority',
        'status',
        'assigned_staff',
        'created_at',
    )

    search_fields = (
        'passenger_name',
        'flight__flight_number',
        'description',
    )

    list_filter = (
        'request_type',
        'priority',
        'status',
    )

    date_hierarchy = 'created_at'