from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import timedelta

ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('kierownik', 'Kierownik'),
    ('pracownik', 'Pracownik'),
]

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='pracownik')
    dzial = models.CharField(max_length=50, blank=True, null=True)  # Dział pracownika (dla kierownika)

class GodzinyPracy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rozpoczecie = models.DateTimeField()
    zakonczenie = models.DateTimeField()
    zatwierdzone = models.BooleanField(default=False)

    def czas_pracy(self):
        return round((self.zakonczenie - self.rozpoczecie).total_seconds() / 3600, 1)

class WniosekUrlopowy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data_od = models.DateField()
    data_do = models.DateField()
    zatwierdzone = models.BooleanField(default=False)
