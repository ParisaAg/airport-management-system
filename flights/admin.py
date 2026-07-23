from django.contrib import admin
from .models import Flight

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):

    list_display = (
        'flight_number',
        'airline',
        'origin',
        'destination',
        'departure_time',
        'status',
    )

    search_fields = (
        'flight_number',
        'airline__name',
        'origin__name',
        'destination__name',
    )

    list_filter = (
        'status',
        'airline',
        'origin',
        'destination',
    )

    date_hierarchy = 'departure_time'