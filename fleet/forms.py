from django import forms
from .models import AircraftType, Aircraft


class AircraftTypeForm(forms.ModelForm):

    class Meta:

        model = AircraftType

        fields = [
            "manufacturer",
            "model",
            "passenger_capacity",
            "range_km",
        ]