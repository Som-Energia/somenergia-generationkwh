# -*- coding:utf8 -*-

from plantmeter.isodates import isodate
from dateutil.relativedelta import relativedelta
import generationkwh.investmentmodel as gkwh

def previousAmortizationDate(purchase_date, current_date):

    pending = pendingAmortizations(purchase_date, current_date, 100, 0)
    if not pending: return None
    return pending[-1][2]

def pendingAmortization(purchase_date, current_date, investment_amount, amortized_amount):

    pending = pendingAmortizations(purchase_date, current_date, investment_amount, amortized_amount)
    if not pending: return 0
    return sum(x[-1] for x in pending)

def currentAmortizationNumber(purchase_date, current_date):

    pending = pendingAmortizations(purchase_date, current_date, 100, 0)
    if not pending: return None
    return pending[-1][0]

def totalAmortizationNumber():
    return gkwh.expirationYears - 1

def pendingAmortizations(purchase_date, current_date, investment_amount, amortized_amount):
    if not purchase_date: return []
    years = gkwh.expirationYears
    yearlyAmount = investment_amount/years
    total_amortizations = years-1
    return [
        (
            amortization_number,
            total_amortizations,
            amortization_date,
            # to be amortized
            (2 if amortization_number is total_amortizations else 1) * yearlyAmount,
        )
        for amortization_number, amortization_date in (
            (i, str(isodate(purchase_date) + relativedelta(years=i+1)))
            for i in xrange(1,years) 
            )
        if amortization_date <= current_date
        and amortization_number * yearlyAmount > amortized_amount
        ]




# vim: et ts=4 sw=4
