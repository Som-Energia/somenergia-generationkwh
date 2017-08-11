# -*- coding: utf-8 -*- 
'''State tracker for investments'''

from yamlns import namespace as ns
from .isodates import isodate
from generationkwh.investmentlogs import (
    log_formfilled,
    log_corrected,
    log_charged,
    log_refunded,
    log_banktransferred,
)


class InvestmentState(ns):
    def __init__(self, user=None, timestamp=None):
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
            iban=iban or u"None",
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


# vim: et ts=4 sw=4   
