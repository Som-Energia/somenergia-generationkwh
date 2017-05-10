# -*- coding:utf8 -*-

def pendingAmortization(purchase_date, current_date, investment_amount, amortized_amount):
    from plantmeter.isodates import isodate
    from dateutil.relativedelta import relativedelta

    current_date = isodate(current_date)
    purchase_date = isodate(purchase_date)
    years = relativedelta(current_date, purchase_date).years

    if years < 2:
        return 0

    if years >= 25:
        return investment_amount

    return (years-1)*400

# vim: et ts=4 sw=4
