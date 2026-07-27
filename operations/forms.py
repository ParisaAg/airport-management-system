from django import forms
from .models import OperationType, GroundOperation

from django.contrib.auth import get_user_model

class OperationTypeForm(forms.ModelForm):
    class Meta:
        model = OperationType
        fields = ["name","description","is_active",]

User = get_user_model()

class GroundOperationForm(forms.ModelForm):

    class Meta:

        model = GroundOperation

        fields = ["flight","operation_type","assigned_staff","status","start_time","end_time","notes",]
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}),
        }