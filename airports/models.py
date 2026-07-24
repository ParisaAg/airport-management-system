from django.db import models


class Airport(models.Model):

    name = models.CharField(
        max_length=150
    )

    icao_code = models.CharField(
        max_length=4,
        unique=True
    )

    iata_code = models.CharField(
        max_length=3,
        unique=True
    )

    country = models.CharField(
        max_length=100
    )

    city = models.CharField(
        max_length=100
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


    def __str__(self):
        return f"{self.name} ({self.iata_code})"
    




class Terminal(models.Model):

    airport = models.ForeignKey(Airport,on_delete=models.CASCADE,related_name='terminals')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10,unique=True)
    description = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.airport.name} - {self.name}"
    

class Gate(models.Model):
    terminal = models.ForeignKey(Terminal,on_delete=models.PROTECT,related_name='gates',verbose_name='Terminal')
    name = models.CharField(max_length=50,verbose_name='Gate Name')

    code = models.CharField(max_length=20,unique=True,db_index=True,verbose_name='Gate Code')
    is_active = models.BooleanField(default=True,verbose_name='Active Status')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = 'Gate'
        verbose_name_plural = 'Gates'
        ordering = ['code']


    def __str__(self):
        return f"{self.terminal.airport.name} - {self.code}"
