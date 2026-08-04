from django import forms

from .models import Airline


class AirlineForm(forms.ModelForm):
    class Meta:
        model = Airline

        fields = [
            "name",
            "iata_code",
            "icao_code",
            "country",
            "website",
            "contact_email",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Iran Air",
                }
            ),
            "iata_code": forms.TextInput(
                attrs={
                    "class": "form-control code-input",
                    "placeholder": "IR",
                    "maxlength": 2,
                }
            ),
            "icao_code": forms.TextInput(
                attrs={
                    "class": "form-control code-input",
                    "placeholder": "IRA",
                    "maxlength": 3,
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Iran",
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.com",
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "operations@example.com",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-checkbox",
                }
            ),
        }

    def clean_iata_code(self):
        code = self.cleaned_data["iata_code"].upper()

        if len(code) != 2 or not code.isalnum():
            raise forms.ValidationError(
                "IATA code must contain exactly "
                "2 letters or numbers."
            )

        return code

    def clean_icao_code(self):
        code = self.cleaned_data["icao_code"].upper()

        if len(code) != 3 or not code.isalnum():
            raise forms.ValidationError(
                "ICAO code must contain exactly "
                "3 letters or numbers."
            )

        return code