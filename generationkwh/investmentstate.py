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
from decimal import Decimal

class InvestmentState(object):
    allowedParams = [
        'name',
        'paid_amount',
        'nominal_amount',
        'active',
        'first_effective_date',
        'last_effective_date',
        'order_date',
        'purchase_date',
        'log',
        ]

    def _checkAttribs(self, **kwds):
        for key in kwds:
            if key in self.allowedParams: continue
            raise Exception(
                "Investments have no '{}' attribute".format(key))

    def __init__(self, user=None, timestamp=None, **values):
        self._checkAttribs(**values)
        self._prev=ns(values)
        self._changed=ns()
        self._user = user.decode('utf-8')
        self._timestamp = timestamp

    def changed(self):
        self._checkAttribs(**self._changed)
        return self._changed

    def values(self):
        return ns(self._prev, **self._changed)


    def order(self, name, date, ip, amount, iban):
        log = log_formfilled(dict(
            create_date=self._timestamp,
            user=self._user,
            ip=ip,
            amount=int(amount),
            iban=iban or None,
        ))

        self._changed.update(
            name = name,
            order_date = date,
            purchase_date = None,
            first_effective_date = None,
            last_effective_date = None,
            active = True,
            nominal_amount = amount,
            paid_amount = Decimal("0.0"),
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

        return self._pay(date, amount, log)

    def repay(self, date, amount, move_line_id):
        log = log_banktransferred(dict(
            create_date=self._timestamp,
            user=self._user,
            move_line_id=move_line_id,
            ))
        self._changed.update(active = True)
        return self._pay(date, amount, log)

    def _pay(self, date, amount, log):
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
            create_date = self._timestamp,
            user = self._user,
            amount = amount,
            move_line_id = move_line_id,
            ))

        self._changed.update(
            purchase_date = None,
            first_effective_date = None,
            last_effective_date = None,
            paid_amount = self._prev.paid_amount-amount,
            log = log+self._prev.log,
        )

    def divest(self, date, amount, move_line_id):
        log = (
            u'[{create_date} {user}] '
            u'DIVESTED: Desinversió total [{move_line_id}]\n'
            .format(
                create_date=self._timestamp,
                user=self._user,
                move_line_id=move_line_id,
            ))
        self._changed.update(
            last_effective_date = date,
            active = bool(self._prev.first_effective_date and date>=self._prev.first_effective_date),
            paid_amount = self._prev.paid_amount-amount,
            log=log+self._prev.log,
        )

    def emitTransfer(self, date, amount, to_name, to_partner_name, move_line_id):
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
            last_effective_date = date,
            active = bool(self._prev.first_effective_date and date>=self._prev.first_effective_date),
            paid_amount = self._prev.paid_amount-amount,
            log=log+self._prev.log,
        )

    def receiveTransfer(self, name, date, amount, origin, origin_partner_name, move_line_id):
        old = origin.values()
        log = ( 
            u'[{create_date} {user}] '
            u'CREATEDBYTRANSFER: Creada per traspàs de '
            u'{old.name} a nom de {origin_partner_name} [{move_line_id}]\n'
            .format(
                create_date=self._timestamp,
                user=self._user,
                move_line_id=move_line_id,
                origin_partner_name = origin_partner_name.decode('utf-8'),
                old = old
            ))

        return self.receiveTransfer_old(
            name=name,
            date=date,
            amount=amount,
            from_name = old.name,
            log = log,
            from_order_date = old.order_date,
            from_purchase_date = old.purchase_date,
            from_first_effective_date = old.first_effective_date,
            from_last_effective_date = old.last_effective_date,
            )

    def receiveTransfer_old(self, name, date, amount, log, from_name,
        from_order_date, from_purchase_date, from_first_effective_date, from_last_effective_date
        ):
        first_effective_date = date + timedelta(days=1)
        if first_effective_date < from_first_effective_date:
            first_effective_date = from_first_effective_date
        self._changed.update(
            name = name,
            active = True,
            nominal_amount = amount,
            paid_amount = amount,
            order_date = from_order_date,
            purchase_date = from_purchase_date,
            first_effective_date = first_effective_date,
            last_effective_date = from_last_effective_date,
            log=log,
            )

    def pact(self, date, comment, **kwds):
        for param in kwds:
            if param in self.allowedParams: continue
            raise Exception(
                "Bad parameter changed in pact '{}'"
                .format(param))

        log = (
            u"[{create_date} {user}] "
            u"PACT: Pacte amb l'inversor. {changes} "
            u"Motiu: {note}\n"
            .format(
            create_date=self._timestamp,
            user=self._user,
            changes=", ".join("{}: {}".format(*x) for x in  sorted(kwds.items())),
            note=comment,
        ))

        self._changed.update(kwds,
            log=log+self._prev.log
        )

    def correct(self, from_amount, to_amount):
        if self._prev.nominal_amount != from_amount:
            raise Exception(
                "Correction not matching the 'from' amount")
        # Not enough, also if it has unpaid invoices
        if self._prev.paid_amount:
            raise Exception("Correction can not be done with paid investments")
        log = log_corrected(dict(
            create_date=self._timestamp,
            user=self._user,
            oldamount = from_amount,
            newamount = to_amount,
            ))
        self._changed.update(
            nominal_amount=to_amount,
            log=log+self._prev.log,
        )

    def partial(self, amount, move_line_id):
        if not self._prev.paid_amount:
            raise Exception(
                "Partial divestment can be only applied to paid investments, try 'correct'")

        remaining=self._prev.nominal_amount-amount
        log =(
            u'[{create_date} {user}] '
            u'PARTIAL: Desinversió parcial de {amount} €, en queden {remaining} € [{move_line_id}]\n'
            .format(
            create_date=self._timestamp,
            user=self._user,
            remaining=remaining,
            move_line_id=move_line_id,
            amount=-amount,
            ))

        self._changed.update(
            nominal_amount=remaining,
            paid_amount=self._prev.paid_amount-amount,
            log=log+self._prev.log,
        )






# vim: et ts=4 sw=4
