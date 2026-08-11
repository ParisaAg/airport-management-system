from django import forms
from django.contrib.auth import get_user_model

from flights.models import Flight

from .models import PassengerRequest


User = get_user_model()


class PassengerRequestForm(
    forms.ModelForm
):
    class Meta:
        model = PassengerRequest

        fields = [
            "flight",
            "passenger_name",
            "booking_reference",
            "request_type",
            "priority",
            "service_location",
            "description",
        ]

        widgets = {
            "flight": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "passenger_name": (
                forms.TextInput(
                    attrs={
                        "class": (
                            "form-control"
                        ),
                        "placeholder": (
                            "Passenger full name"
                        ),
                    }
                )
            ),

            "booking_reference": (
                forms.TextInput(
                    attrs={
                        "class": (
                            "form-control "
                            "code-input"
                        ),
                        "placeholder": (
                            "e.g. ABC123"
                        ),
                    }
                )
            ),

            "request_type": (
                forms.Select(
                    attrs={
                        "class": (
                            "form-control"
                        ),
                    }
                )
            ),

            "priority": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "service_location": (
                forms.TextInput(
                    attrs={
                        "class": (
                            "form-control"
                        ),
                        "placeholder": (
                            "e.g. Terminal 1 / "
                            "Gate A4"
                        ),
                    }
                )
            ),

            "description": (
                forms.Textarea(
                    attrs={
                        "class": (
                            "form-control"
                        ),
                        "rows": 6,
                        "placeholder": (
                            "Describe the passenger "
                            "service requirement..."
                        ),
                    }
                )
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.fields["flight"].queryset = (
            Flight.objects
            .select_related(
                "airline",
                "origin",
                "destination",
            )
            .order_by(
                "-departure_time"
            )
        )

    def clean_booking_reference(
        self,
    ):
        booking_reference = (
            self.cleaned_data.get(
                "booking_reference",
                "",
            )
        )

        return (
            booking_reference
            .strip()
            .upper()
        )

    def clean_passenger_name(
        self,
    ):
        passenger_name = (
            self.cleaned_data[
                "passenger_name"
            ]
        )

        return passenger_name.strip()


class PassengerAssignmentForm(
    forms.Form
):
    staff = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=True,
        label="Passenger Service Staff",
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.fields["staff"].queryset = (
            User.objects.filter(
                role="PASSENGER_SERVICE",
                is_active=True,
            )
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )


class PassengerResolutionForm(
    forms.Form
):
    resolution_notes = (
        forms.CharField(
            required=True,
            label="Resolution Notes",
            widget=forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Describe the service "
                        "provided and final "
                        "resolution..."
                    ),
                }
            ),
        )
    )