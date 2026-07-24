from django.conf import settings
from django.db import models


class PassengerRequest(models.Model):

    REQUEST_TYPE_CHOICES = (
        ('WHEELCHAIR', 'Wheelchair Assistance'),
        ('LOST_FOUND', 'Lost and Found'),
        ('SPECIAL_ASSISTANCE', 'Special Assistance'),
        ('COMPLAINT', 'Complaint'),
        ('OTHER', 'Other'),
    )


    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    )


    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    flight = models.ForeignKey('flights.Flight',on_delete=models.PROTECT,related_name='passenger_requests',verbose_name='Flight')
    passenger_name = models.CharField(max_length=100,verbose_name='Passenger Name')
    request_type = models.CharField(max_length=30,choices=REQUEST_TYPE_CHOICES,verbose_name='Request Type')
    priority = models.CharField(max_length=20,choices=PRIORITY_CHOICES,default='LOW',verbose_name='Priority')
    description = models.TextField(verbose_name='Description')
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='OPEN',verbose_name='Status')
    assigned_staff = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='passenger_requests',verbose_name='Assigned Staff')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Passenger Request'
        verbose_name_plural = 'Passenger Requests'
        ordering = ['-created_at']


    def __str__(self):
        return f"{self.passenger_name} - {self.request_type}"