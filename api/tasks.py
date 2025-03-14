from datetime import timedelta
from django.utils.timezone import now
from .models import GodzinyPracy

def automatyczne_zatwierdzanie():
    godziny = GodzinyPracy.objects.filter(zatwierdzone=False)
    for godzina in godziny:
        if now() - godzina.zakonczenie > timedelta(hours=24):
            godzina.zatwierdzone = True
            godzina.save()
