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
    def __init__(self, user=None, timestamp=None, **values):
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

    @staticmethod
    def firstEffectiveDate(purchase_date):
        pionersDay = '2016-04-28'
        waitDays = gkwh.waitingDays
        if str(purchase_date) < pionersDay:
            waitDays -= 30
        waitDelta = timedelta(days=waitDays)
        return purchase_date + waitDelta

    def pay(self, date, amount, iban, move_line_id):

        log = log_charged(dict(
            create_date=self._timestamp,
            user=self._user,
            amount=int(amount),
            iban=iban or u"None",
            move_line_id=move_line_id,
            ))
        self._changed.update(
            log=log+self._prev.log,
            paid_amount = self._prev.paid_amount + amount,
            )

        if amount != self._prev.nominal_amount:
            # TODO: Concrete Exception class
            raise Exception("Wrong payment")

        if self._prev.paid_amount:
            # TODO: Concrete Exception class
            raise Exception("Already paid")

        self._changed.update(
            purchase_date = date,
            # TODO: bissextile years
            first_effective_date = self.firstEffectiveDate(date),
            # TODO: Setting also this one
            #last_effective_date = date + timedelta(years=25),
            )

    def unpay(self, amount, move_line_id):
        log = log_refunded(dict(
            create_date=self._timestamp,
            user=self._user,
            move_line_id=move_line_id,
            ))

        self._changed.update(
            purchase_date = False,
            first_effective_date = False,
            last_effective_date = False,
            paid_amount = self._prev.paid_amount-amount,
            log=log+self._prev.log,
        )

    def divest(self, data, amount, move_line_id):
        log = (
            u'[{create_date} {user}] '
            u'DIVESTED: Desinversió total [{move_line_id}]\n'
            .format(
                create_date=self._timestamp,
                user=self._user,
                move_line_id=move_line_id,
            ))
        self._changed.update(
            last_effective_date = data,
            active = self._prev.first_effective_date and data>=self._prev.first_effective_date,
            paid_amount = self._prev.paid_amount-amount,
            log=log+self._prev.log,
        )

    def emitTransfer(self, data, amount, to_name, to_partner_name, move_line_id):
        log = (
            u'[{create_date} {user}] '
            u'DIVESTEDBYTRANSFER: Traspas cap a {to_partner_name} amb codi {to_name} [{move_line_id}]\n'
            .format(
                create_date=self._timestamp,
                user=self._user,
                move_line_id=move_line_id,
                to_partner_name = to_partner_name,
                to_name = to_name,
            ))
        self._changed.update(
            last_effective_date = data,
            active = self._prev.first_effective_date and data>=self._prev.first_effective_date,
            paid_amount = self._prev.paid_amount-amount,
            log=log+self._prev.log,
        )



# vim: et ts=4 sw=4
