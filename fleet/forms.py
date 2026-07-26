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


class AircraftForm(forms.ModelForm):

    class Meta:

        model = Aircraft

        fields = ["airline","aircraft_type","registration_number","serial_number","manufacture_year","status",]