# -*- coding:utf8 -*-

from plantmeter.isodates import isodate
from dateutil.relativedelta import relativedelta

def previousAmortizationDate(purchase_date, current_date):

    years = relativedelta(
        isodate(current_date),
        isodate(purchase_date),
        ).years


    firstAmortization = isodate(purchase_date) + relativedelta(years = 2)

    if years < 2:
        return None

    return str(firstAmortization)


def pendingAmortization(purchase_date, current_date, investment_amount, amortized_amount):


    years = relativedelta(
        isodate(current_date),
        isodate(purchase_date),
        ).years

    yearly_amortitzation = investment_amount / 25

    if years < 2:
        return 0

    if years >= 25:
        return investment_amount - amortized_amount

    toAmortize = (years-1)*yearly_amortitzation - amortized_amount
    return max(0, toAmortize)

# vim: et ts=4 sw=4
