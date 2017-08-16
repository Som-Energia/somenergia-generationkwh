# -*- coding: utf-8 -*-
'''State tracker for investments'''

from yamlns import namespace as ns
from .isodates import isodate
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import generationkwh.investmentmodel as gkwh
from decimal import Decimal
from decorator import decorator


@decorator
def action(f, self, *args, **kwds):
    result = f(self, *args, **kwds)
    self._changed.update(result)
    return result

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
        'amortized_amount',
        'active',
        'first_effective_date',
        'last_effective_date',
        'order_date',
        'purchase_date',
        'log',
        ]

    def _log(self, message, **kwds):
        return (
            u'[{create_date} {user}] '.format(
                create_date=self._timestamp,
                user=self._user,
            )
            + message.format(**kwds)
            + self._prev.get('log', '')
            )

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

    def erpChanges(self):
        changes = ns(self.changed())
        if 'nominal_amount' in changes:
            changes.update(
                nshares=changes.nominal_amount//gkwh.shareValue,
            )
        changes.pop('paid_amount',None)
        return changes

    def values(self):
        return ns(self._prev, **self._changed)

    @action
    def order(self, name, date, ip, amount, iban):
        """
        Creates a new investment from the info retrived
        from the investment form.
        """
        log = self._log(
            u"FORMFILLED: Formulari omplert des de la IP {ip}, Quantitat: {amount} €, IBAN: {iban}\n",
            ip=ip,
            amount=int(amount),
            iban=iban or None,
        )

        return ns(
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
        waitDelta = relativedelta(days=waitDays)
        return purchase_date + waitDelta

    @action
    def pay(self, date, amount, iban, move_line_id):
        """
        A payment invoice has been generated and
        a payment order has been sent to the bank,
        so the investment is considered paid
        unless later a refund is received from the bank.

        Effective period is set accordantly to the
        investment model.
        """
        log = self._log(
            u"PAID: "
            u"Pagament de {amount} € remesat al compte {iban} "
            u"[{move_line_id}]\n",
            amount=int(amount),
            iban=iban or u"None",
            move_line_id=move_line_id,
            )

        return self._pay(date, amount, log)

    @action
    def repay(self, date, amount, move_line_id):
        """
        A previously refunded payment has been paid
        by a bank transfer or another mean.
        """
        log = self._log(
            u'REPAID: '
            u'Pagament de {amount} € rebut per transferència bancària '
            u'[{move_line_id}]\n',
            amount=amount,
            move_line_id=move_line_id,
            )
        self._changed.update(active = True)
        return self._pay(date, amount, log)

    def _pay(self, date, amount, log):
        paid_amount = self._prev.paid_amount + amount
        self._changed.update(
            log=log,
            paid_amount = paid_amount,
            )

        if amount != self._prev.nominal_amount:
            # TODO: Concrete Exception class
            raise Exception("Wrong payment")

        if self._prev.paid_amount:
            # TODO: Concrete Exception class
            raise Exception("Already paid")
        return ns(
            log=log,
            paid_amount = paid_amount,
            purchase_date = date,
            # TODO: bissextile years
            first_effective_date = self.firstEffectiveDate(date),
            # TODO: Setting also this one
            last_effective_date = date + relativedelta(years=gkwh.expirationYears),
            )

    @action
    def unpay(self, amount, move_line_id):
        """
        A previous payment has been returned by the bank
        so the investment is set as unpaid.
        """
        log = self._log(
            u'REFUNDED: '
            u'Devolució del pagament remesat de {amount} € '
            u'[{move_line_id}]\n',
            amount = amount,
            move_line_id = move_line_id,
            )

        return ns(
            purchase_date = None,
            first_effective_date = None,
            last_effective_date = None,
            paid_amount = self._prev.paid_amount-amount,
            log = log,
        )

    @action
    def divest(self, date, amount, move_line_id):
        """
        Returns the full loan to the investor after being paid.
        If the loan has been never effective deactivates it.
        """
        log = self._log(
            u'DIVESTED: Desinversió total [{move_line_id}]\n',
            move_line_id=move_line_id,
            )
        paid_amount = self._prev.paid_amount-amount
        if paid_amount:
            raise Exception(
                u"Paid amount after divestment should be 0 but was {} €"
                .format(paid_amount))
        return ns(
            last_effective_date = date,
            active = bool(self._prev.first_effective_date) and date>=self._prev.first_effective_date,
            paid_amount = paid_amount,
            log=log,
        )

    @action
    def emitTransfer(self, date, amount, to_name, to_partner_name, move_line_id):
        """
        Performs the changes required after having transferred
        the investment to a different person.

        Before you have to create the target investment
        and call receiveTransfer on it passing this 
        investment as parameter.
        """
        log = self._log(
            u'DIVESTEDBYTRANSFER: '
            u'Traspas cap a {to_partner_name} amb codi {to_name} '
            u'[{move_line_id}]\n',
            move_line_id=move_line_id,
            to_partner_name = to_partner_name,
            to_name = to_name,
            )
        return ns(
            last_effective_date = date,
            active = bool(self._prev.first_effective_date) and date>=self._prev.first_effective_date,
            paid_amount = self._prev.paid_amount-amount,
            log=log,
        )

    @action
    def receiveTransfer(self, name, date, amount, origin, origin_partner_name, move_line_id):
        """
        Initializes the investment as being transfer
        from a different person.

        Origin is the original investment as it was.
        Don't forget to call emitTransfer on origin,
        after call this method.
        """
        old = origin.values()
        log = self._log( 
            u'CREATEDBYTRANSFER: '
            u'Creada per traspàs de {old.name} '
            u'a nom de {origin_partner_name} '
            u'[{move_line_id}]\n'
            .format(
                move_line_id=move_line_id,
                origin_partner_name = origin_partner_name.decode('utf-8'),
                old = old
            ))

        first_effective_date = old.first_effective_date
        if date >= first_effective_date:
            first_effective_date = date + timedelta(days=1)
        return ns(
            old,
            name = name,
            active = True,
            nominal_amount = amount,
            paid_amount = amount,
            first_effective_date = first_effective_date,
            log=log,
            )

    @action
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

        log = self._log(
            u"PACT: Pacte amb l'inversor. {changes} "
            u"Motiu: {note}\n",
            changes=", ".join("{}: {}".format(*x) for x in  sorted(kwds.items())),
            note=comment,
        )

        return ns(kwds, log=log)

    @action
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
        log = self._log(
            u'CORRECTED: Quantitat canviada abans del pagament '
            u'de {oldamount} € a {newamount} €\n',
            oldamount = from_amount,
            newamount = to_amount,
            )
        return ns(
            nominal_amount=to_amount,
            log=log,
        )

    @action
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
                "Partial divestment can be only applied to paid investments, "
                "try 'correct'")

        remaining=self._prev.nominal_amount-amount
        log = self._log(
            u'PARTIAL: Desinversió parcial de {amount} €, '
            u'en queden {remaining} € [{move_line_id}]\n',
            remaining=remaining,
            move_line_id=move_line_id,
            amount=-amount,
            )

        return ns(
            nominal_amount=remaining,
            paid_amount=self._prev.paid_amount-amount,
            log=log,
        )

    @action
    def cancel(self):
        """
        Marks an unpaid investments as discarded.
        Usually a refunded investment once the investor
        refuses to pay it or cannot be contacted.
        """
        if self._prev.paid_amount:
            raise Exception(
                "Only unpaid investments can be cancelled")

        if self._prev.purchase_date:
            raise Exception(
                "Only unpaid investments can be cancelled")

        log = self._log(
            u'CANCEL: La inversió ha estat cancel·lada\n'
            )
        return ns(
            active=False,
            log=log,
            )

    @action
    def amortize(self, date, to_be_amortized):
        """
        Annotates an amortization for the given amount at the given date
        """
        return ns(
            amortized_amount = to_be_amortized + self._prev.amortized_amount,
            log = self._log(
                u'AMORTIZATION: Generada amortització '
                u'de {to_be_amortized:.02f} € pel {date}\n',
                    date = date,
                    to_be_amortized = to_be_amortized,
                ),
            )



# vim: et ts=4 sw=4
