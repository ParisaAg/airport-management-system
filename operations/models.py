from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class OperationType(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Operation Name"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active Status"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


    class Meta:
        verbose_name = "Operation Type"
        verbose_name_plural = "Operation Types"
        ordering = ["name"]


    def __str__(self):
        return self.name
    

class GroundOperation(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    flight = models.ForeignKey('flights.Flight',on_delete=models.PROTECT,related_name='ground_operations',verbose_name='Flight')
    operation_type = models.ForeignKey(OperationType,on_delete=models.PROTECT,related_name='operations',verbose_name='Operation Type')
    assigned_staff = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='assigned_operations',verbose_name='Assigned Staff')
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='PENDING',verbose_name='Status')
    start_time = models.DateTimeField(blank=True,null=True,verbose_name='Start Time')

    end_time = models.DateTimeField(blank=True,null=True,verbose_name='End Time')
    notes = models.TextField(blank=True,null=True,verbose_name='Notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ground Operation'
        verbose_name_plural = 'Ground Operations'
        ordering = ['-created_at']
    def clean(self):
        super().clean()

        if self.start_time and self.end_time:
            if self.end_time < self.start_time:
                raise ValidationError(
                    "End time must be after start time."
                )

        if self.status == 'COMPLETED' and not self.end_time:
            raise ValidationError(
                "Completed operations must have an end time."
            )

    def __str__(self):
        return f"{self.flight.flight_number} - {self.operation_type.name}"