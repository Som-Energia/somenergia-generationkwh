# -*- coding: utf-8 -*-
'''State tracker for investments'''

from yamlns import namespace as ns
from . import investmentmodel as gkwh
from .isodates import isodate
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from decorator import decorator

def forceUnicode(text):
    try: unicode
    except NameError: # python 3
        if type(text) is bytes:
            return text.decode('utf8')
    else: # python 2
        if type(text) is str:
            return text.decode('utf8')
    return text

try: xrange
except NameError:
    xrange=range


@decorator
def action(f, self, *args, **kwds):
    result = f(self, *args, **kwds)
    self._changed.update(result)
    self._vals.update(result)
    return result

class InvestmentStateError(Exception):
    pass

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
        'nominal_amount', # nshares * 100
        'amortized_amount',
        'draft',
        'active',
        'signed_date',
        'first_effective_date',
        'last_effective_date',
        'order_date',
        'purchase_date',
        'log',
        'actions_log',
        'last_interest_paid_date',
        ]

    def __init__(self, user=None, timestamp=None, **values):
        self._checkAttribs(**values)
        if 'purchase_date' in values and 'nominal_amount' in values:
            values.setdefault('paid_amount',
                values['nominal_amount'] if values['purchase_date'] else 0.0)
        values = ns(values)
        self._prev=ns(values)
        self._vals=ns(values)
        self._changed=ns()
        self._user = forceUnicode(user)
        self._timestamp = timestamp

    def __getattr__(self, name):
        if name in self.allowedParams:
            return self._vals[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        """
        Forbid directly setting the attributes.
        Do it by returning a dictionary in an @action
        """
        if name in self.allowedParams:
            raise AttributeError(name)
        return super(InvestmentState, self).__setattr__(name, value)

    def _log(self, message, **kwds):
        return (
            u'[{create_date} {user}] '.format(
                create_date=self._timestamp,
                user=self._user,
            )
            + message.format(**kwds)
            + self._vals.get('log', '')
            )

    def _checkAttribs(self, **kwds):
        for key in kwds:
            if key in self.allowedParams: continue
            raise InvestmentStateError(
                "Investments have no '{}' attribute".format(key))

    def addAction(self, **kwds):
        from yaml.parser import ParserError

        yaml = 'actions: []'
        if 'actions_log' in self._vals:
            yaml = self.actions_log
        try:
            actions = ns.loads(yaml)
        except ParserError as error:
            actions = ns(actions=[ns(
                content = yaml,
                type='unparseable',
            )])
        if type(actions) != ns:
            actions = ns(actions=[ns(
                content = yaml,
                type='badcontent',
            )])
        if 'actions' not in actions:
            actions = ns(actions=[ns(
                content = yaml,
                type='badroot',
            )])
        if type(actions.actions) != list:
            actions = ns(actions=[ns(
                content = yaml,
                type='badcontent',
            )])
        action = ns()
        if 'type' in kwds:
            action.update(type=kwds['type'])
        action.update(timestamp=str(self._timestamp))
        action.update(user=self._user)
        action.update(kwds)
        actions.actions.append(action)
        return actions.dump()

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
        return ns(self._vals, **self._changed)

    @staticmethod
    def firstEffectiveDate(purchase_date, waitDays=None):
        # TODO: consider bissextile years for waitDays
        if waitDays is None:
            waitDays = gkwh.waitingDays

        pionersDay = '2016-04-28'
        if str(purchase_date) < pionersDay:
            waitDays -= 30
        waitDelta = relativedelta(days=waitDays)
        return purchase_date + waitDelta

        pionersDay = '2016-04-28'
        pionersPrize = 0
        if str(purchase_date) < pionersDay:
            pionersPrize = 30
        waitDelta = relativedelta(years=gkwh.waitYears, days=-pionersPrize)
        return purchase_date + waitDelta

    @staticmethod
    def lastEffectiveDate(purchase_date, expirationYears=None):
        if expirationYears is None:
            expirationYears = gkwh.expirationYears
        elif expirationYears == 0:
            return None
        return purchase_date + relativedelta(years=expirationYears)

    @staticmethod
    def hasEffectivePeriod(first_date, last_date):
        if not first_date: return False # never started
        if not last_date: return True # started but no end
        return first_date<=last_date # not crossed dates
    
    @action
    def order(self, name, date, ip, amount, iban):
        """
        Creates a new investment from the info retrived
        from the investment form.
        """
        log = self._log(
            u"ORDER: Formulari omplert des de la IP {ip},"
            u" Quantitat: {amount} €, IBAN: {iban}\n",
            ip=ip,
            amount=int(amount),
            iban=iban or None,
        )
        actions = self.addAction(
            type = 'order',
            amount = amount,
            iban = iban or None,
            ip = ip,
        )
        return ns(
            name = name,
            order_date = date,
            purchase_date = None,
            first_effective_date = None,
            last_effective_date = None,
            amortized_amount = Decimal("0.0"),
            active = True,
            nominal_amount = amount,
            paid_amount = Decimal("0.0"),
            log = log,
            actions_log = actions,
            draft = True,
        )

    @action
    def sign(self, signed_date):
        """
        Sign a new investment an specific date.
        """
        log = self._log(
            u"SIGN: Inversió signada amb data {date}\n",
            date=signed_date,
        )
        actions = self.addAction(
            type = 'sign',
            date = signed_date,
        )
        return ns(
            signed_date = signed_date,
            log = log,
        )

    @action
    def invoice(self):
        # TODO: Check that signed_date is not None
        if not self.draft:
            raise InvestmentStateError("Already invoiced")

        return ns(
            draft=False,
            log = self._log("INVOICED: Facturada i remesada\n"),
            actions_log = self.addAction(
                type = 'invoice',
            ))

    def pay(self, date, amount, move_line_id):
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
            u"Pagament de {amount} € efectuat "
            u"[{move_line_id}]\n",
            amount=int(amount),
            move_line_id=move_line_id,
            )

        if self.draft:
            # TODO: Concrete Exception class
            raise InvestmentStateError("Not invoiced yet")

        paid_amount = self.paid_amount + amount

        # TODO: Is this still useful?? Remove it!!
        self._changed.update(
            log=log,
            paid_amount = paid_amount,
            )

        if amount != self.nominal_amount:
            # TODO: Concrete Exception class
            raise InvestmentStateError(
                "Wrong payment, expected {expected}, given {given}"
                .format(
                    expected=self.nominal_amount,
                    given=amount,
                ))

        if self.paid_amount:
            # TODO: Concrete Exception class
            raise InvestmentStateError("Already paid")

        return log, paid_amount

    @action
    def unpay(self, amount, move_line_id):
        """
        A previous payment has been returned by the bank
        so the investment is set as unpaid.
        """
        amount = abs(amount)
        log = self._log(
            u'UNPAID: '
            u'Devolució del pagament de {amount} € '
            u'[{move_line_id}]\n',
            amount = amount,
            move_line_id = move_line_id,
            )

        if self.draft:
            raise InvestmentStateError("Not invoiced yet")

        # TODO: also purchase date
        if not self.paid_amount:
            raise InvestmentStateError("No pending amount to unpay")

        if amount != self.paid_amount:
            raise InvestmentStateError(
                "Unpaying wrong amount, was {given} expected {expected}"
                .format(
                    given=amount,
                    expected=self.paid_amount,
                ))

        return ns(
            purchase_date = None,
            first_effective_date = None,
            last_effective_date = None,
            paid_amount = self.paid_amount-amount,
            log = log,
            actions_log = self.addAction(
                type = 'unpay',
                amount = amount,
                move_line_id = move_line_id,
            ),
        )

    @action
    def divest(self, date, amount, move_line_id):
        """
        Returns the full loan to the investor after being paid.
        If the loan has been never effective deactivates it.
        """
        # TODO: Consider amortization
        # TODO: What about penalties
        log = self._log(
            u'DIVESTED: Desinversió total, tornats {amount} € [{move_line_id}]\n',
            move_line_id=move_line_id,
            amount = amount,
            )
        amortized_amount = self.amortized_amount + amount
        if self.nominal_amount != amortized_amount:
            raise InvestmentStateError(
                u"Divesting wrong amount, tried {amount} €, unamortized {should} €"
                .format(
                    amount = amount,
                    should = self.nominal_amount - self.amortized_amount,
                )) # TODO format

        paid_amount = self.paid_amount-amount-self.amortized_amount
        if paid_amount:
            raise InvestmentStateError(
                u"Paid amount after divestment should be 0 but was {} €"
                .format(paid_amount))
        return ns(
            last_effective_date = date,
            active = self.hasEffectivePeriod(self.first_effective_date, date),
            paid_amount = paid_amount,
            amortized_amount = self.amortized_amount + amount,
            log=log,
            actions_log = self.addAction(
                type = 'divest',
                amount = amount,
                move_line_id = move_line_id,
                date = date,
            ),
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
        if not self.purchase_date:
            raise InvestmentStateError("Only paid investments can be transferred")
        return ns(
            last_effective_date = date,
            active = self.hasEffectivePeriod(self.first_effective_date, date),
            paid_amount = self.paid_amount-amount,
            amortized_amount = self.nominal_amount,
            log=log,
            actions_log = self.addAction(
                type = 'transferout',
                amount = amount,
                move_line_id = move_line_id,
                date = date,
                toinvestment = to_name,
                topartner = to_partner_name,
            ),
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
                origin_partner_name = forceUnicode(origin_partner_name),
                old = old,
            ))

        if not old.purchase_date:
            raise InvestmentStateError("Only paid investments can be transferred")

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
            actions_log=self.addAction(
                type = 'transferin',
                frominvestment = old.name,
                frompartner = origin_partner_name,
                date = date,
                move_line_id = move_line_id,
            ))

    @action
    def pact(self, date, comment, **kwds):
        """
        A pact enables changing any attribute in a
        way not considered by the rest of the actions.
        A comment explaining the pact is required.
        """
        for param in kwds:
            if param in self.allowedParams: continue
            raise InvestmentStateError(
                "Bad parameter changed in pact '{}'"
                .format(param))

        log = self._log(
            u"PACT: Pacte amb l'inversor. {changes} "
            u"Motiu: {note}\n",
            changes=", ".join("{}: {}".format(*x) for x in  sorted(kwds.items())),
            note=comment,
        )

        return ns(kwds,
            log=log,
            actions_log=self.addAction(
                type = 'pact',
                comment = comment,
                date = date,
                **kwds
                ),
            )

    @action
    def correct(self, from_amount, to_amount):
        """
        Correct the nominal value before we issue an
        invoice.
        THIS ACTION IS JUST FOR MIGRATION.
        """
        if self.nominal_amount != from_amount:
            raise InvestmentStateError(
                "Correction not matching the 'from' amount")
        # TODO: Not enough, also if it has unpaid invoices
        if self.purchase_date:
            raise InvestmentStateError("Correction can not be done with paid investments")
        log = self._log(
            u'CORRECTED: Quantitat canviada abans del pagament '
            u'de {oldamount} € a {newamount} €\n',
            oldamount = from_amount,
            newamount = to_amount,
            )
        return ns(
            nominal_amount=to_amount,
            log=log,
            actions_log=self.addAction(
                type = 'correct',
                oldamount = from_amount,
                newamount = to_amount,
                ),
        )

    @action
    def partial(self, amount, move_line_id):
        """
        This action is only available for migrated investments.
        Partial divest changes the nominal value of the action
        once it is already paid.
        THIS ACTION IS JUST FOR MIGRATION.
        In modern investments you should split it to generate
        two brand new investments and then fully divest one of them.
        """
        if not self.purchase_date:
            raise InvestmentStateError(
                "Partial divestment can be only applied to paid investments, "
                "try 'correct'")

        remaining=self.nominal_amount-amount
        log = self._log(
            u'PARTIAL: Desinversió parcial de {amount} €, '
            u'en queden {remaining} € [{move_line_id}]\n',
            remaining=remaining,
            move_line_id=move_line_id,
            amount=-amount,
            )

        return ns(
            nominal_amount=remaining,
            paid_amount=self.paid_amount-amount,
            log=log,
            actions_log = self.addAction(
                type = 'partial',
                amount = amount,
                move_line_id = move_line_id,
            ),
        )

    @action
    def cancel(self):
        """
        Marks an uninvoiced investment as discarded.
        Usually a refunded investment once the investor
        refuses to pay it or cannot be contacted.
        """
        # TODO: if invoiced but still unpaid cannot be cancelled either

        if not self.active:
            raise InvestmentStateError(
                "Inactive investments can not be cancelled")

        if self.purchase_date:
            raise InvestmentStateError(
                "Only unpaid investments can be cancelled")

        log = self._log(
            u'CANCEL: La inversió ha estat cancel·lada\n'
            )
        return ns(
            active=False,
            purchase_date = None,
            first_effective_date = None,
            last_effective_date = None,
            paid_amount = 0,
            log=log,
            actions_log = self.addAction(
                type = 'cancel',
                ),
            )

    @action
    def amortize(self, date, to_be_amortized):
        """
        Annotates an amortization for the given amount at the given date
        """
        if not self.purchase_date:
            raise InvestmentStateError(u"Amortizing an unpaid investment")
        return ns(
            amortized_amount = to_be_amortized + self.amortized_amount,
            log = self._log(
                u'AMORTIZATION: Generada amortització '
                u'de {to_be_amortized:.02f} € pel {date}\n',
                    date = date,
                    to_be_amortized = to_be_amortized,
                ),
            actions_log = self.addAction(
                type = 'amortize',
                date=date,
                amount=to_be_amortized,
                ),
            )

    def pendingAmortizations(self, current_date):

        if not self.purchase_date: return []
        years = gkwh.expirationYears
        yearlyAmount = self.nominal_amount/years
        total_amortizations = years-1
        return [
            (
                amortization_number,
                total_amortizations,
                str(amortization_date),
                # to be amortized
                (2 if amortization_number is total_amortizations else 1) * yearlyAmount,
            )
            for amortization_number, amortization_date in (
                (i, self.purchase_date + relativedelta(years=i+1))
                for i in xrange(1,years)
                )
            if amortization_date <= current_date
            and amortization_number * yearlyAmount > self.amortized_amount
            ]


    @action
    def interest(self, date, to_be_interized):
        """
        Annotates interest for the given amount at the given date
        """
        if not self.purchase_date:
            raise InvestmentStateError(u"Interest an unpaid investment")
        return ns(
            log = self._log(
                u'INTEREST: Generada factura d\'interessos '
                u'de {to_be_interized:.02f} € pel {last_interest_paid_date}\n',
                    last_interest_paid_date = date,
                    to_be_interized = to_be_interized,
                ),
            actions_log = self.addAction(
                type = 'interest',
                last_interest_paid_date=date,
                amount=to_be_interized,
                ),
            last_interest_paid_date=date,
            )

    @action
    def migrate(self, oldVersion, newVersion):
        """
        Change investment state to migrate
        """
        return ns(
            log = self._log(
                u"MIGRATED: "
                u"Migració de la versió {oldVersion} a {newVersion}\n",
                oldVersion=oldVersion,
                newVersion=newVersion,
            ),
            actions_log = self.addAction(
                type = 'migrate',
                oldversion = oldVersion,
                newversion = newVersion,
            )
        )

class AportacionsState(InvestmentState):
    #TODO: Refactor unduo concrete class, not necessary anymore
    """
    AportacionsState child of InvestmentState
    """
    @action
    def pay(self, date, amount, move_line_id, waitDays=None, expirationYears=None):
        log, paid_amount = super(AportacionsState, self).pay(date, amount, move_line_id)

        return ns(
            log=log,
            paid_amount = paid_amount,
            purchase_date = date,
            first_effective_date = self.firstEffectiveDate(date, waitDays),
            last_effective_date = self.lastEffectiveDate(date, expirationYears),
            actions_log = self.addAction(
                type = 'pay',
                amount = paid_amount,
                move_line_id = move_line_id,
                ),
            )

class GenerationkwhState(InvestmentState):
    #TODO: Refactor unduo concrete class, not necessary anymore
    """
    GenerationkwhState child of InvestmentState
    """
    def __init__(self, user=None, timestamp=None, **values):
        super(GenerationkwhState, self).__init__(user, timestamp, **values)

    @action
    def pay(self, date, amount, move_line_id, waitDays=None, expirationYears=None):
        log, paid_amount = super(GenerationkwhState, self).pay(date, amount, move_line_id)

        return ns(
            log=log,
            paid_amount = paid_amount,
            purchase_date = date,
            first_effective_date = self.firstEffectiveDate(date, waitDays),
            last_effective_date = self.lastEffectiveDate(date, expirationYears),
            actions_log = self.addAction(
                type = 'pay',
                amount = paid_amount,
                move_line_id = move_line_id,
                ),
            )

# vim: et ts=4 sw=4
