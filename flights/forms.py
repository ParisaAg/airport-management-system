from django import forms
from django.db.models import Q

from airports.models import Gate
from fleet.models import Aircraft

from .models import Flight, GateAssignment


class FlightForm(forms.ModelForm):
    class Meta:
        model = Flight

        fields = [
            "flight_number",
            "airline",
            "aircraft",
            "origin",
            "destination",
            "departure_time",
            "arrival_time",
        ]

        widgets = {
            "flight_number": forms.TextInput(
                attrs={
                    "class": "form-control code-input",
                    "placeholder": "e.g. IR720",
                }
            ),
            "airline": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "aircraft": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "origin": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "destination": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "departure_time": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
            ),
            "arrival_time": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["departure_time"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        self.fields["arrival_time"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        aircraft_filter = Q(status="ACTIVE")

        if self.instance and self.instance.pk:
            aircraft_filter |= Q(
                pk=self.instance.aircraft_id
            )

        self.fields["aircraft"].queryset = (
            Aircraft.objects
            .select_related(
                "airline",
                "aircraft_type",
            )
            .filter(aircraft_filter)
            .order_by("registration_number")
        )

        if (
            user
            and user.role == "AIRLINE_OPERATOR"
        ):
            if user.airline_id:
                self.fields["airline"].queryset = (
                    self.fields["airline"]
                    .queryset
                    .filter(pk=user.airline_id)
                )

                self.fields["airline"].initial = (
                    user.airline_id
                )

                self.fields["airline"].widget = (
                    forms.HiddenInput()
                )

                operator_aircraft_filter = Q(
                    airline_id=user.airline_id,
                    status="ACTIVE",
                )

                if self.instance and self.instance.pk:
                    operator_aircraft_filter |= Q(
                        pk=self.instance.aircraft_id,
                    )

                self.fields["aircraft"].queryset = (
                    Aircraft.objects
                    .select_related(
                        "airline",
                        "aircraft_type",
                    )
                    .filter(operator_aircraft_filter)
                    .order_by("registration_number")
                )
            else:
                self.fields["airline"].queryset = (
                    self.fields["airline"]
                    .queryset
                    .none()
                )

                self.fields["aircraft"].queryset = (
                    Aircraft.objects.none()
                )

    def clean_flight_number(self):
        flight_number = self.cleaned_data[
            "flight_number"
        ]

        return flight_number.upper()

    def clean(self):
        cleaned_data = super().clean()

        airline = cleaned_data.get("airline")
        aircraft = cleaned_data.get("aircraft")

        if (
            airline
            and aircraft
            and aircraft.airline_id != airline.id
        ):
            self.add_error(
                "aircraft",
                (
                    "The selected aircraft does not "
                    "belong to this airline."
                ),
            )

        return cleaned_data


class GateAssignmentForm(forms.ModelForm):
    class Meta:
        model = GateAssignment

        fields = [
            "gate",
            "notes",
        ]

        widgets = {
            "gate": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Optional gate assignment notes..."
                    ),
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["gate"].queryset = (
            Gate.objects
            .select_related(
                "terminal",
                "terminal__airport",
            )
            .filter(is_active=True)
            .order_by(
                "terminal__code",
                "code",
            )
        )