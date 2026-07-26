from django import forms
from .models import OperationType, GroundOperation



class OperationTypeForm(forms.ModelForm):
    class Meta:
        model = OperationType
        fields = ["name","description","is_active",]