# -*- coding:utf8 -*-

from plantmeter.isodates import isodate
from dateutil.relativedelta import relativedelta
import generationkwh.investmentmodel as gkwh

def previousAmortizationDate(purchase_date, current_date):

    years = relativedelta(
        isodate(current_date),
        isodate(purchase_date),
        ).years

    if years <= gkwh.waitYears:
        return None

    firstAmortization = (
        isodate(purchase_date)
        + relativedelta(years = min(years,gkwh.expirationYears)
        ))

    return str(firstAmortization)


def pendingAmortization(purchase_date, current_date, investment_amount, amortized_amount):


    years = relativedelta(
        isodate(current_date),
        isodate(purchase_date),
        ).years

    yearly_amortitzation = investment_amount / gkwh.expirationYears

    if years <= gkwh.waitYears:
        return 0

    if years >= gkwh.expirationYears:
        return investment_amount - amortized_amount

    toAmortize = (years-1)*yearly_amortitzation - amortized_amount
    return max(0, toAmortize)

def currentAmortizationNumber(purchase_date, current_date):

    years = relativedelta(
        isodate(current_date),
        isodate(purchase_date),
        ).years
    if years < 2:
        return None

    return min(gkwh.expirationYears, years ) - 1

def totalAmortizationNumber():
    return gkwh.expirationYears - 1

# vim: et ts=4 sw=4
