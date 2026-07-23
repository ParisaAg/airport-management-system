from django.contrib import admin
from .models import AircraftType, Aircraft


@admin.register(AircraftType)
class AircraftTypeAdmin(admin.ModelAdmin):
    list_display = ('manufacturer','model','passenger_capacity','range_km',)
    search_fields = ('manufacturer','model',)
    list_filter = ('manufacturer',)



@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ('registration_number','airline','aircraft_type','status','manufacture_year', )
    search_fields = ('registration_number','airline__name','aircraft_type__model',)
    list_filter = ('status','airline','aircraft_type',)