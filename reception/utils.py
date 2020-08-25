from .models import *
from django.utils import timezone

MAID_PRICE = 90

def ongoing_serves():
    ongoing = Serves.objects.filter(active=True)
    return ongoing


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
    for mid in data['maids']:
        serves_maid = ServesMaids(serves=serves.id, start=time, end=time, maid=mid)
        serves_maid.save()
        maid = Maid.objects.get(pk=mid)
        maid.available = False
        maid.save()

    pid = data['place']
    serves_place = ServesPlaces(serves=serves, place=pid, start=time, end=time)
    serves_place.save()
    place = Place.objects.get(pk=pid)
    place.available = False
    place.save()


def change_status(data):
    time = data['time']
    serves = Serves.objects.get(id=data['serves_id'])
    for mid in data['out_mid']:
        serves_maid = ServesMaids.objects.get(serves=serves.id, maid=mid, active=True)
        serves_maid.end = time
        serves_maid.active = False
        serves_maid.save()

        maid = Maid.objects.get(pk=mid)
        maid.available = True
        maid.save()

    for mid in data['in_mid']:
        serves_maid = ServesMaids(serves=serves.id, maid=mid, start=time, end=time)
        serves_maid.save()

        maid = Maid.objects.get(pk=mid)
        maid.available = False
        maid.save()

    for pid in data['out_place']:
        serves_place = ServesPlaces.objects.get(place=pid, serves=serves.id, active=True)
        serves_place.end = time
        serves_place.active = False
        serves_place.save()

        place = Place.objects.get(pk=pid)
        place.available = True
        place.save()

    for pid in data['in_place']:
        serves_place = ServesPlaces(serves=serves.id, place=pid, start=time, end=time)
        serves_place.save()

        place = Place.objects.get(pk=pid)
        place.available = False
        place.save()


def end_serves(data):
    time = data['time']
    serves = Serves.objects.get(data['serves_id'])
    serves.end = time
    serves.active = False
    if data['customer']:
        serves.customer = data['customer']
    serves.save()
    for sm in serves.servesmaids_set.filter(active=True):
        sm.end = time
        sm.active = False
        sm.save()
        maid = Maid.objects.get(pk=sm.maid)
        maid.available = True
        maid.save()

    sp = serves.servesplaces_set.get(active=True)
    sp.end = time
    sp.active = False
    sp.save()
    place = Place.objects.get(pk=sp.place)
    place.available = True
    place.save()


def add_item(data):
    sid = data['serves_id']
    serves = Serves.objects.get(pk=sid)


def calculate_expense(data):
    serves = Serves.objects.get(pk=data['serves_id'])
    sm = serves.servesmaids_set.all()
    sp = serves.servesplaces_set.all()
    si = serves.servesitems_set.all()

    maid_expense = 0
    for m in sm:
        delta = m.end - m.start
        maid_expense += MAID_PRICE
    place_expense = 0
    item_expense = 0
