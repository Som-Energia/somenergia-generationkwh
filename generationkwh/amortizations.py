# -*- coding:utf8 -*-

from plantmeter.isodates import isodate
from dateutil.relativedelta import relativedelta

def previousAmortizationDate(purchase_date, current_date):

    firstAmortization = '2003-01-01'
    if isodate(current_date) >= isodate(firstAmortization):
        return firstAmortization

    return None

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
