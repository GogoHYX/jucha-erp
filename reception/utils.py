from .models import *
from django.utils import timezone

HALF_HOUR_THRESHOLD_IN_SECONDS = 600


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
        serves_maid = ServesMaids(serves=serves, start=time, end=time, maid_id=mid)
        serves_maid.save()
        maid = Maid.objects.get(pk=mid)
        maid.available = False
        maid.save()

    pid = data['place']
    place = Place.objects.get(pk=pid)
    serves_place = ServesPlaces(serves=serves, place_id=pid, start=time, end=time, price=place.price)
    serves_place.save()
    place.available = False
    place.save()


def change_status(data):
    time = data['time']
    serves = Serves.objects.get(id=data['serves_id'])
    for mid in data['out_mid']:
        serves_maid = ServesMaids.objects.get(serves=serves, maid_id=mid, active=True)
        serves_maid.end = time
        serves_maid.active = False
        serves_maid.save()

        maid = Maid.objects.get(pk=mid)
        maid.available = True
        maid.save()

    for mid in data['in_mid']:
        serves_maid = ServesMaids(serves=serves, maid_id=mid, start=time, end=time)
        serves_maid.save()

        maid = Maid.objects.get(pk=mid)
        maid.available = False
        maid.save()

    for pid in data['out_place']:
        place = Place.objects.get(pk=pid)
        serves_place = ServesPlaces.objects.get(place_id=pid, serves=serves, active=True)
        serves_place.end = time
        serves_place.active = False
        serves_place.save()

        place.available = True
        place.save()

    for pid in data['in_place']:
        place = Place.objects.get(pk=pid)
        serves_place = ServesPlaces(serves=serves, place_id=pid, start=time, end=time, price=place.price)
        serves_place.save()

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
    place = sp.place
    place.available = True
    place.save()


def add_item(data):
    si = ServesItems(item_id=data['item_id'], serves_id=data['serves_id'],
                     quantity=data['quantity'], price=data['price'])
    si.save()


def valid_hour(start, end):
    delta = end - start
    half_hour = delta.seconds // 1800
    second = delta.seconds - half_hour * 1800
    if second > HALF_HOUR_THRESHOLD_IN_SECONDS:
        half_hour += 1
    return half_hour / 2


def calculate_expense(data):
    serves = Serves.objects.get(pk=data['serves_id'])
    sm = serves.servesmaids_set.all()
    sp = serves.servesplaces_set.all()
    si = serves.servesitems_set.all()

    maid_detail = []
    for m in sm:
        hour = valid_hour(m.start, m.end)
        price = m.price
        total = price * hour
        maid_detail.append((m.maid.cos_name, hour, price, total))

    place_detail = []
    for p in sp:
        hour = valid_hour(p.start, p.end)
        price = p.price
        total = price * hour
        place_detail.append((p.place.name, hour, price, total))

    item_detail = []
    for i in si:
        price = i.price
        quantity = i.quantity
        total = price * quantity
        item_detail.append((i.item.name, quantity, price, total))

    maid_total = sum([i[3] for i in maid_detail])
    place_total = sum([i[3] for i in place_detail])
    item_total = sum([i[3] for i in item_detail])

    result = {
        'maid_total': maid_total,
        'place_total': place_total,
        'item_total': item_total,
        'maid_detail': maid_detail,
        'place_detail': place_detail,
        'item_detail': item_detail,
    }
    return result


def generate_charge(data):
    bill = Bill()
    if data['voucher_id']:
        bill.voucher = Voucher.objects.get(data['voucher_id'])
    if data['is_serves']:
        charge = ServesCharge(total=data['total'], note=data['note'], bill_id=bill.id,
                              serves_id=data['serves_id'], manual=data['manual'])
    else:
        charge = DepositCharge(total=data['total'], note=data['note'], bill_id=bill.id,
                              card_id=data['card_id'], deposit_amount=data['deposit_amount'])


def pay(data):
    total_amount = data['total_amount']
    if data['customer']:
        pass

