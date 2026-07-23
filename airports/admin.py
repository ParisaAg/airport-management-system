from django.contrib import admin
from .models import Airport, Terminal


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):

    list_display = ('name','iata_code','icao_code','city','country',)

    search_fields = ('name','iata_code','icao_code','city',)


@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):

    list_display = ('name', 'code', 'airport',)
    search_fields = ('name','code','airport__name',)