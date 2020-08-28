from .models import *
from django.utils import timezone

HALF_HOUR_THRESHOLD_IN_SECONDS = 600


def ongoing_serves():
    ongoing = Serves.objects.filter(active=True)
    return ongoing


def available_maids():
    am = Maid.objects.filter(available=True)
    return am


def available_places():
    ap = Place.objects.filter(available=True)
    return [(p.id, p.name) for p in ap]


def start_serves(data):
    time = timezone.now()
    serves = Serves(start=time, end=time, active=True)
    serves.save()
    for maid in data['maids']:
        serves_maid = ServesMaids(serves=serves, start=time, end=time, maid=maid)
        serves_maid.activate()

    pid = data['place']
    serves_place = ServesPlaces(serves=serves, place_id=pid, start=time, end=time)
    serves_place.activate()


def change_status(data):
    time = data['time']
    serves = Serves.objects.get(id=data['serves_id'])
    if data['maids_out']:
        for sm in data['maids_out']:
            sm.end = time
            sm.deactivate()

    if data['maids_in']:
        for maid in data['maids_in']:
            serves_maid = ServesMaids(serves=serves, maid=maid, start=time, end=time)
            serves_maid.activate()

    if data['place']:
        serves_place = serves.servesplaces_set.get(active=True)
        serves_place.end = time
        serves_place.deactivate()

        pid = data['place']
        serves_place = ServesPlaces(serves=serves, place_id=pid, start=time, end=time)
        serves_place.activate()


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


def expense_detail(serves_id, update=True):
    serves = Serves.objects.get(pk=serves_id)
    sm = serves.servesmaids_set.all()
    sp = serves.servesplaces_set.all()
    si = serves.servesitems_set.all()
    time = timezone.now()
    serves.end = time
    serves.save()

    maid_detail = []
    for m in sm:
        d = {}
        if m.active and update:
            m.end = time
            m.save()
        hour = valid_hour(m.start, m.end)
        price = m.price
        total = price * hour
        d['name'] = m.maid.cos_name
        d['price'] = price
        d['start'] = show_time(m.start)
        d['end'] = show_time(time)
        d['hour'] = hour
        d['total'] = total
        maid_detail.append(d)

    place_detail = []
    for p in sp:
        d = {}
        if p.active and update:
            p.end = time
            p.save()
        hour = valid_hour(p.start, p.end)
        price = p.price
        total = price * hour
        d['name'] = p.place.name
        d['price'] = price
        d['start'] = show_time(p.start)
        d['end'] = show_time(time)
        d['hour'] = hour
        d['total'] = total
        place_detail.append(d)

    item_detail = []
    for i in si:
        d = {}
        price = i.price
        quantity = i.quantity
        total = price * quantity
        d['name'] = i.item.name
        d['price'] = price
        d['quantity'] = quantity
        d['total'] = total
        item_detail.append(d)

    maid_total = sum([i['total'] for i in maid_detail])
    place_total = sum([i['total'] for i in place_detail])
    item_total = sum([i['total'] for i in item_detail])

    total = maid_total + place_total + item_total

    result = {
        'maid_total': maid_total,
        'place_total': place_total,
        'item_total': item_total,
        'maid_detail': maid_detail,
        'place_detail': place_detail,
        'item_detail': item_detail,
        'total': total,
    }
    return result


def generate_charge(data):
    bill = Bill()
    if data['is_serves']:
        charge = ServesCharge(total=data['total'], note=data['note'], bill_id=bill.id,
                              serves_id=data['serves_id'], manual=data['manual'])
    else:
        charge = DepositCharge(total=data['total'], note=data['note'], bill_id=bill.id,
                               card_id=data['card_id'], deposit_amount=data['deposit_amount'])
    charge.save()
    return charge


def use_voucher(data):
    bill = Bill.objects.get(pk=data['bill_id'])
    if data['voucher_id']:
        bill.voucher = Voucher.objects.get(pk=data['voucher_id'])
        if data['meituan']:
            bill.voucher.meituan = True
            bill.voucher.swift_number = data['voucher_swift_number']


def check_balance(charge, is_serves=True):
    if is_serves:
        unpaid = charge.total + charge.manual
    else:
        unpaid = charge.total

    return unpaid - charge.bill.total


def cash_back_and_credit(data):
    pass





