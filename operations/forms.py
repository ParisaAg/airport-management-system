from django import forms
from django.contrib.auth import get_user_model

from .models import GroundOperation, OperationType


User = get_user_model()


class OperationTypeForm(forms.ModelForm):
    class Meta:
        model = OperationType

        fields = [
            "name",
            "description",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Refueling",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Describe this operation type..."
                    ),
                    "rows": 4,
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-checkbox",
                }
            ),
        }


class GroundOperationForm(forms.ModelForm):
    class Meta:
        model = GroundOperation

        fields = [
            "flight",
            "operation_type",
            "assigned_staff",
            "notes",
        ]

        widgets = {
            "flight": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "operation_type": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "assigned_staff": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Optional operational notes..."
                    ),
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["assigned_staff"].queryset = (
            User.objects
            .filter(
                role="GROUND_STAFF",
                is_active=True,
            )
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )

        self.fields["operation_type"].queryset = (
            OperationType.objects
            .filter(is_active=True)
            .order_by("name")
        )