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
    """
    InvestmentState keeps the state of an investment
    during the different available actions.

    Designed with db use in mind. You can feed
    just the required attributes for the actions
    and you can get just the changed attributes
    after the actions.
    """

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
        """
        Creates a new investment from the info retrived
        from the investment form.
        """
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
        """
        A payment invoice has been generated and
        a payment order has been sent to the bank,
        so the investment is considered paid
        unless later a refund is received from the bank.

        Effective period is set accordantly to the
        investment model.
        """
        log = log_charged(dict(
            create_date=self._timestamp,
            user=self._user,
            amount=int(amount),
            iban=iban or u"None",
            move_line_id=move_line_id,
            ))

        return self._pay(date, amount, log)

    def repay(self, date, amount, move_line_id):
        """
        A previously refunded payment has been paid
        by a bank transfer or another mean.
        """
        log = log_banktransferred(dict(
            create_date=self._timestamp,
            user=self._user,
            amount=amount,
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
        """
        A previous payment has been returned by the bank
        so the investment is set as unpaid.
        """
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
        """
        Returns the full loan to the investor after being paid.
        If the loan has been never effective deactivates it.
        """
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
        if self._changed.paid_amount:
            raise Exception(
                u"Paid amount after divestment should be 0 but was {} €"
                .format(self._changed.paid_amount))

    def emitTransfer(self, date, amount, to_name, to_partner_name, move_line_id):
        """
        Performs the changes required after having transferred
        the investment to a different person.

        Before you have to create the target investment
        and call receiveTransfer on it passing this 
        investment as parameter.
        """
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
            active = bool(self._prev.first_effective_date) and date>=self._prev.first_effective_date,
            paid_amount = self._prev.paid_amount-amount,
            log=log+self._prev.log,
        )

    def receiveTransfer(self, name, date, amount, origin, origin_partner_name, move_line_id):
        """
        Initializes the investment as being transfer
        from a different person.

        Origin is the original investment as it was.
        Don't forget to call emitTransfer on origin,
        after call this method.
        """
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

        first_effective_date = old.first_effective_date
        if date >= first_effective_date:
            first_effective_date = date + timedelta(days=1)
        self._changed.update(
            old,
            name = name,
            active = True,
            nominal_amount = amount,
            paid_amount = amount,
            first_effective_date = first_effective_date,
            log=log,
            )

    def pact(self, date, comment, **kwds):
        """
        A pact enables changing any attribute in a
        way not considered by the rest of the actions.
        A comment explaining the pact is required.
        """
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
        """
        Correct the nominal value before we issue an
        invoice.
        """
        if self._prev.nominal_amount != from_amount:
            raise Exception(
                "Correction not matching the 'from' amount")
        # TODO: Not enough, also if it has unpaid invoices
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
        """
        This action is only available for migrated investments.
        Partial divest changes the nominal value of the action
        once it is already paid.
        In modern investments you should split it to generate
        two brand new investments and then fully divest one of them.
        """
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

    def cancel(self):
        """
        Marks an unpaid investments as discarded.
        Usually a refunded investment once the investor
        refuses to pay it or cannot be contacted.
        """
        if self._prev.purchase_date:
            raise Exception(
                "Only unpaid investments can be cancelled")

        log = (
            u'[{create_date} {user}] '
            u'CANCEL: La inversió ha estat cancel·lada\n'
            .format(
            create_date=self._timestamp,
            user=self._user,
            ))
        self._changed.update(
            active=False,
            log=log+self._prev.log,
            )



# vim: et ts=4 sw=4
