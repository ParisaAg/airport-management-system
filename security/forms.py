from django import forms
from django.contrib.auth import (
    get_user_model,
)

from flights.models import Flight

from .models import SecurityReport


User = get_user_model()


class SecurityReportForm(
    forms.ModelForm
):
    class Meta:
        model = SecurityReport

        fields = [
            "flight",
            "report_type",
            "severity",
            "location",
            "officer",
            "description",
        ]

        widgets = {
            "flight": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "report_type": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "severity": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "e.g. Terminal 1 - Gate A03"
                    ),
                }
            ),
            "officer": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Describe the security "
                        "incident clearly..."
                    ),
                }
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

        self.fields[
            "officer"
        ].required = False

        self.fields[
            "officer"
        ].empty_label = (
            "Unassigned"
        )

        self.fields[
            "officer"
        ].queryset = (
            User.objects
            .filter(
                role="SECURITY_OFFICER",
                is_active=True,
            )
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )

        self.fields[
            "flight"
        ].queryset = (
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


class SecurityAssignmentForm(
    forms.Form
):
    officer = (
        forms.ModelChoiceField(
            queryset=User.objects.none(),
            widget=forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            label="Security Officer",
        )
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

        self.fields[
            "officer"
        ].queryset = (
            User.objects
            .filter(
                role="SECURITY_OFFICER",
                is_active=True,
            )
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )


class SecurityResolutionForm(
    forms.Form
):
    resolution_notes = (
        forms.CharField(
            required=True,
            widget=forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Describe how the "
                        "incident was resolved..."
                    ),
                }
            ),
            label="Resolution Notes",
        )
    )