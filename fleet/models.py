from django.db import models
from airlines.models import Airline


class AircraftType(models.Model):

    manufacturer = models.CharField(max_length=100,verbose_name="Manufacturer")
    model = models.CharField(max_length=100,verbose_name="Aircraft Model")
    passenger_capacity = models.PositiveIntegerField(verbose_name="Passenger Capacity")
    range_km = models.PositiveIntegerField(verbose_name="Range (KM)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Aircraft Type"
        verbose_name_plural = "Aircraft Types"
        ordering = ["manufacturer", "model"]

    def __str__(self):
        return f"{self.manufacturer} {self.model}"
    



class Aircraft(models.Model):

    STATUS_CHOICES = (('ACTIVE', 'Active'),('MAINTENANCE', 'Maintenance'),('RETIRED', 'Retired'),)
    airline = models.ForeignKey(Airline,on_delete=models.PROTECT,related_name='aircrafts',verbose_name='Airline')
    aircraft_type = models.ForeignKey('AircraftType',on_delete=models.PROTECT,related_name='aircrafts',verbose_name='Aircraft Type')
    registration_number = models.CharField(max_length=20,unique=True,db_index=True,verbose_name='Registration Number')
    serial_number = models.CharField(max_length=50,unique=True,blank=True,null=True,verbose_name='Serial Number')
    manufacture_year = models.PositiveIntegerField(blank=True,null=True,verbose_name='Manufacture Year')
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='ACTIVE',verbose_name='Status')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Aircraft'
        verbose_name_plural = 'Aircrafts'
        ordering = ['registration_number']

    def __str__(self):
        return f"{self.registration_number} - {self.aircraft_type}"