from datetime import date

from django import forms
from django.db.models import Q

from .models import Aircraft, AircraftType


class AircraftTypeForm(forms.ModelForm):
    class Meta:
        model = AircraftType

        fields = [
            "manufacturer",
            "model",
            "passenger_capacity",
            "range_km",
            "is_active",
        ]

        widgets = {
            "manufacturer": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Airbus",
                }
            ),
            "model": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. A320-200",
                }
            ),
            "passenger_capacity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 1000,
                }
            ),
            "range_km": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 100,
                    "max": 25000,
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-checkbox",
                }
            ),
        }

    def clean_passenger_capacity(self):
        capacity = self.cleaned_data[
            "passenger_capacity"
        ]

        if not 1 <= capacity <= 1000:
            raise forms.ValidationError(
                "Passenger capacity must be "
                "between 1 and 1000."
            )

        return capacity

    def clean_range_km(self):
        aircraft_range = self.cleaned_data[
            "range_km"
        ]

        if not 100 <= aircraft_range <= 25000:
            raise forms.ValidationError(
                "Aircraft range must be between "
                "100 and 25,000 kilometers."
            )

        return aircraft_range


class AircraftForm(forms.ModelForm):
    class Meta:
        model = Aircraft

        fields = [
            "airline",
            "aircraft_type",
            "registration_number",
            "serial_number",
            "manufacture_year",
        ]

        widgets = {
            "airline": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "aircraft_type": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "registration_number": forms.TextInput(
                attrs={
                    "class": "form-control code-input",
                    "placeholder": "e.g. EP-ABC",
                }
            ),
            "serial_number": forms.TextInput(
                attrs={
                    "class": "form-control code-input",
                    "placeholder": "Manufacturer serial number",
                }
            ),
            "manufacture_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1903,
                    "max": date.today().year + 1,
                    "placeholder": "e.g. 2020",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        airline_filter = Q(is_active=True)
        aircraft_type_filter = Q(is_active=True)

        if self.instance and self.instance.pk:
            airline_filter |= Q(
                pk=self.instance.airline_id
            )

            aircraft_type_filter |= Q(
                pk=self.instance.aircraft_type_id
            )

        self.fields["airline"].queryset = (
            self.fields["airline"]
            .queryset
            .filter(airline_filter)
            .order_by("name")
        )

        self.fields["aircraft_type"].queryset = (
            self.fields["aircraft_type"]
            .queryset
            .filter(aircraft_type_filter)
            .order_by("manufacturer", "model")
        )

    def clean_registration_number(self):
        registration_number = self.cleaned_data[
            "registration_number"
        ]

        return registration_number.upper()

    def clean_serial_number(self):
        serial_number = self.cleaned_data.get(
            "serial_number"
        )

        if serial_number:
            return serial_number.upper()

        return serial_number

    def clean_manufacture_year(self):
        manufacture_year = self.cleaned_data.get(
            "manufacture_year"
        )

        if manufacture_year is None:
            return manufacture_year

        maximum_year = date.today().year + 1

        if not 1903 <= manufacture_year <= maximum_year:
            raise forms.ValidationError(
                (
                    "Manufacture year must be between "
                    f"1903 and {maximum_year}."
                )
            )

        return manufacture_year