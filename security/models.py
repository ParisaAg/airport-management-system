from django.conf import settings
from django.db import models


class SecurityReport(models.Model):

    REPORT_TYPE_CHOICES = (
        ('PASSENGER', 'Passenger Issue'),
        ('BAGGAGE', 'Baggage Issue'),
        ('AIRCRAFT', 'Aircraft Security'),
        ('ACCESS', 'Access Control'),
        ('OTHER', 'Other'),
    )

    SEVERITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    )


    flight = models.ForeignKey(
        'flights.Flight',
        on_delete=models.PROTECT,
        related_name='security_reports',
        verbose_name='Flight'
    )

    officer = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='security_reports',verbose_name='Security Officer')
    report_type = models.CharField(max_length=20,choices=REPORT_TYPE_CHOICES,verbose_name='Report Type')
    severity = models.CharField( max_length=20, choices=SEVERITY_CHOICES,default='LOW',verbose_name='Severity')
    description = models.TextField(verbose_name='Description')
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='OPEN',verbose_name='Status')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = 'Security Report'
        verbose_name_plural = 'Security Reports'
        ordering = ['-created_at']


    def __str__(self):
        return f"{self.flight.flight_number} - {self.report_type}"