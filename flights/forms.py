from django import forms
from django.db.models import Q
from .models import Flight, GateAssignment
from airports.models import Gate
from fleet.models import Aircraft
from .models import Flight, GateAssignment
from .services import available_flight_status_choices

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


class FlightStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        label="New Status",
        choices=(),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    delay_minutes = forms.IntegerField(
        label="Delay Duration",
        required=False,
        min_value=1,
        max_value=1440,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Delay in minutes",
                "min": 1,
                "max": 1440,
            }
        ),
        help_text=(
            "Required when marking a flight as delayed."
        ),
    )

    reason = forms.CharField(
        label="Operational Reason",
        required=False,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": (
                    "Explain the operational reason "
                    "for this update..."
                ),
                "rows": 4,
            }
        ),
    )

    def __init__(
        self,
        *args,
        flight,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.flight = flight

        self.fields["status"].choices = [
            ("","Select next status"),*available_flight_status_choices(flight.status,),
        ]

    def clean_reason(self):
        reason = self.cleaned_data.get(
            "reason",
            "",
        ).strip()

        return reason

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get("status")
        delay_minutes = cleaned_data.get(
            "delay_minutes"
        )
        reason = cleaned_data.get(
            "reason",
            "",
        )

        if status == "DELAYED":
            if not delay_minutes:
                self.add_error(
                    "delay_minutes",
                    (
                        "Delay duration is required "
                        "for delayed flights."
                    ),
                )

            if not reason:
                self.add_error(
                    "reason",
                    (
                        "A delay reason is required "
                        "for delayed flights."
                    ),
                )

        if (
            status == "CANCELLED"
            and not reason
        ):
            self.add_error(
                "reason",
                (
                    "A cancellation reason is required "
                    "for cancelled flights."
                ),
            )

        return cleaned_data