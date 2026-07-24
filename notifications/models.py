from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class Notification(models.Model):

    TYPE_CHOICES = (
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('SUCCESS', 'Success'),
        ('ERROR', 'Error'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='notifications',verbose_name='User')

    title = models.CharField(max_length=150,verbose_name='Title')
    message = models.TextField(verbose_name='Message')
    notification_type = models.CharField(max_length=20,choices=TYPE_CHOICES,default='INFO',verbose_name='Notification Type')
    is_read = models.BooleanField(default=False,verbose_name='Read Status')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']


    def __str__(self):
        return f"{self.user.username} - {self.title}"