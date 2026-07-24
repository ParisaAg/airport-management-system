from django import forms
from .models import Airline



class AirlineForm(forms.ModelForm):

    class Meta:

        model = Airline

        fields = ["name","iata_code","icao_code","country","website","contact_email","is_active",]