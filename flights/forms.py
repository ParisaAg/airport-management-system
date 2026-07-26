from django import forms
from .models import Flight
from fleet.models import Aircraft
from .models import Flight, GateAssignment




class FlightForm(forms.ModelForm):

    class Meta:

        model = Flight

        fields = ['flight_number','airline','aircraft','origin','destination','departure_time','arrival_time','status',]
        widgets = {

            'departure_time': forms.DateTimeInput(attrs={'type':'datetime-local'}),
            'arrival_time': forms.DateTimeInput(
                attrs={'type':'datetime-local'}
            ),

        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user and user.role == "AIRLINE_OPERATOR":

            self.fields['airline'].queryset = (self.fields['airline'].queryset.filter(id=user.airline.id)
            )

            self.fields['aircraft'].queryset = (
                Aircraft.objects
                .filter(
                    airline=user.airline
                )
            )



class GateAssignmentForm(forms.ModelForm):

    class Meta:

        model = GateAssignment

        fields = [
            "gate",
            "notes",
        ]