from django.db import models


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


    def __str__(self):
        return f"{self.flight_number} - {self.origin.iata_code} to {self.destination.iata_code}"