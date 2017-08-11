# -*- coding: utf-8 -*- 
'''State tracker for investments'''

from yamlns import namespace as ns
from .isodates import isodate
from datetime import timedelta
from generationkwh.investmentlogs import (
    log_formfilled,
    log_corrected,
    log_charged,
    log_refunded,
    log_banktransferred,
)
import generationkwh.investmentmodel as gkwh

class InvestmentState(ns):
    def __init__(self, user=None, timestamp=None, values={}):
        self._prev=ns(values)
        self._changed=ns()
        self._user = user
        self._timestamp = timestamp

    def changed(self):
        return self._changed

    def order(self, date, ip, amount, iban):
        log = log_formfilled(dict(
            create_date=self._timestamp,
            user=self._user,
            ip=ip,
            amount=int(amount),
            iban=iban or None,
        ))

        self._changed.update(
            order_date = date,
            purchase_date = False,
            first_effective_date = False,
            last_effective_date = False,
            active = True,
            nominal_amount = amount,
            paid_amount = 0.0,
            log = log,
        )

    def pay(self, date, amount, iban):
        self._changed.update(
            purchase_date = date,
            # TODO: bissextile years
            # TODO: pioners are just 11 months
            first_effective_date = date + timedelta(days=gkwh.waitingDays),
            # TODO: Setting also this one
            #last_effective_date = date + timedelta(years=25),
            paid_amount = amount,
            )


# vim: et ts=4 sw=4
