# -*- coding:utf8 -*-

from plantmeter.isodates import isodate
from dateutil.relativedelta import relativedelta
from . import investmentmodel as gkwh

from .investmentstate import InvestmentState


def pendingAmortizations(purchase_date, current_date, investment_amount, amortized_amount):
    
    state = InvestmentState(user='caca', timestamp='',
        purchase_date=purchase_date and isodate(purchase_date),
        nominal_amount=investment_amount,
        amortized_amount=amortized_amount,
        )
    return state.pendingAmortizations(isodate(current_date))



# vim: et ts=4 sw=4
