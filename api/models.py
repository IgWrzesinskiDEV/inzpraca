from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from datetime import timedelta

ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('kierownik', 'Kierownik'),
    ('pracownik', 'Pracownik'),
]

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('kierownik', 'Kierownik'),
        ('pracownik', 'Pracownik'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='pracownik')
    dzial = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(null=True, blank=True, unique=True)

    def __str__(self):
        return self.username


class GodzinyPracy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rozpoczecie = models.DateTimeField()
    zakonczenie = models.DateTimeField()
    zatwierdzone = models.BooleanField(default=False)

    def czas_pracy(self):
        return round((self.zakonczenie - self.rozpoczecie).total_seconds() / 3600, 1)


class WniosekUrlopowy(models.Model):
    STATUS_CHOICES = [
        ('oczekuje', 'Oczekuje na zatwierdzenie'),
        ('zatwierdzony', 'Zatwierdzony'),
        ('odrzucony', 'Odrzucony'),
    ]

    pracownik = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wnioski')
    wybrane_dni = models.JSONField(default=list)  # Przechowuje listę dni w formacie ["2025-06-01", "2025-06-15"]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='oczekuje')
    data_utworzenia = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pracownik.username} - {self.status}"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Profil"