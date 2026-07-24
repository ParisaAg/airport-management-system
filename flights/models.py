from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
class Flight(models.Model):

    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('BOARDING', 'Boarding'),
        ('DEPARTED', 'Departed'),
        ('ARRIVED', 'Arrived'),
        ('DELAYED', 'Delayed'),
        ('CANCELLED', 'Cancelled'),
        )
    flight_number = models.CharField(max_length=10,unique=True,db_index=True,verbose_name="Flight Number")
    airline = models.ForeignKey('airlines.Airline',on_delete=models.PROTECT,related_name='flights',verbose_name="Airline")
    aircraft = models.ForeignKey('fleet.Aircraft',on_delete=models.PROTECT,related_name='flights',verbose_name="Aircraft")
    origin = models.ForeignKey('airports.Airport',on_delete=models.PROTECT,related_name='departing_flights',verbose_name="Origin Airport")
    destination = models.ForeignKey('airports.Airport',on_delete=models.PROTECT, related_name='arriving_flights', verbose_name="Destination Airport")
    departure_time = models.DateTimeField(verbose_name="Departure Time")
    arrival_time = models.DateTimeField(verbose_name="Arrival Time")
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='SCHEDULED',verbose_name="Flight Status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Flight"
        verbose_name_plural = "Flights"
        ordering = ['departure_time']

    def clean(self):
        super().clean()

        if self.origin == self.destination:
            raise ValidationError(
                "Origin airport and destination airport cannot be the same."
            )

        if self.arrival_time <= self.departure_time:
            raise ValidationError(
                "Arrival time must be after departure time."
            )
    def __str__(self):
        return f"{self.flight_number} - {self.origin.iata_code} to {self.destination.iata_code}"
    

class GateAssignment(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('RELEASED', 'Released'),
        ('CANCELLED', 'Cancelled'),
    )

    flight = models.ForeignKey(Flight,on_delete=models.PROTECT,related_name='gate_assignments',verbose_name='Flight')
    gate = models.ForeignKey('airports.Gate',on_delete=models.PROTECT,related_name='assignments',verbose_name='Gate')
    assigned_time = models.DateTimeField(auto_now_add=True,verbose_name='Assigned Time')
    released_time = models.DateTimeField(blank=True,null=True,verbose_name='Released Time')
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='ACTIVE',verbose_name='Status')
    notes = models.TextField(blank=True,null=True,verbose_name='Notes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Gate Assignment'
        verbose_name_plural = 'Gate Assignments'
        ordering = ['-assigned_time']
    def clean(self):
        super().clean()

        if self.released_time and self.assigned_time:

            if self.released_time < self.assigned_time:
                raise ValidationError(
                    "Released time cannot be before assigned time."
                )

        if self.status == 'RELEASED' and not self.released_time:
            raise ValidationError(
                "Released assignments must have a released time."
            )

        conflicts = GateAssignment.objects.filter(
            gate=self.gate,
            status='ACTIVE'
        ).exclude(
            id=self.id
        )

        if conflicts.exists():
            raise ValidationError(
                "This gate already has an active flight assignment."
            )
    def __str__(self):
        return f"{self.flight.flight_number} - {self.gate.code}"