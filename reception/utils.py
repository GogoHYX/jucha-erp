from .models import *
from django.utils import timezone


def available_maids():
    am = Maid.objects.filter(available=True)
    return [(m.id, m.cos_name) for m in am]


def available_places():
    ap = Place.objects.filter(available=True)
    return [(p.id, p.name) for p in ap]


def start_serves(data):
    time = timezone.now()
    serves = Serves(start=time, end=time, active=True)
    serves.save()
    for maid in data['maids']:
        serves_maid = ServesMaids(serves=serves.id, start=time, end=time, maid=maid)
        serves_maid.save()
    place = data['place']
    serves_place = ServesPlaces(serves=serves, place=place, start=time, end=time)
    serves_place.save()