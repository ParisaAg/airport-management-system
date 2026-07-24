from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('AIRPORT_MANAGER', 'Airport Manager'),
        ('AIRLINE_OPERATOR', 'Airline Operator'),
        ('GROUND_STAFF', 'Ground Staff'),
        ('SECURITY_OFFICER', 'Security Officer'),
        ('PASSENGER_SERVICE', 'Passenger Service'),
    )

    role = models.CharField(max_length=30,choices=ROLE_CHOICES,default='GROUND_STAFF')
    phone = models.CharField(max_length=15,blank=True,null=True)
    airline = models.ForeignKey('airlines.Airline',on_delete=models.SET_NULL,null=True,blank=True,related_name='operators',verbose_name='Airline')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.username