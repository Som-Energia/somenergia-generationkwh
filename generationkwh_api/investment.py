# -*- coding: utf-8 -*-

from osv import osv, fields
from .erpwrapper import ErpWrapper
from plantmeter.mongotimecurve import toLocal
from dateutil.relativedelta import relativedelta
import datetime
from yamlns import namespace as ns
from generationkwh.isodates import isodate, naiveisodate, naiveisodatetime

# TODO: This function is duplicated in other sources
def _sqlfromfile(sqlname):
    from tools import config
    import os
    sqlfile = os.path.join(
        config['addons_path'], 'generationkwh_api',
            'sql', sqlname+'.sql')
    with open(sqlfile) as f:
        return f.read()

class GenerationkWhInvestment(osv.osv):

    _name = 'generationkwh.investment'
    _order = 'purchase_date DESC'

    _columns = dict(
        member_id=fields.many2one(
            'somenergia.soci',
            "Inversor",
            select=True,
            required=True,
            help="Inversor que ha comprat les accions",
            ),
        nshares=fields.integer(
            "Nombre d'accions",
            required=True,
            help="Nombre d'accions comprades",
            ),
        purchase_date=fields.date(
            "Data de compra",
            required=True,
            help="Quin dia es varen comprar les accions",
            ),
        first_effective_date=fields.date(
            "Primera data a la que és fa efectiva",
            help="Dia que les accions començaran a generar drets a kWh",
            ),
        last_effective_date=fields.date(
            "Darrera data a la que és efectiva",
            help="Darrer dia que les accions generaran drets a kWh",
            ),
        move_line_id=fields.many2one(
            'account.move.line',
            'Línia del moviment contable',
            required=True,
            select=True,
            help="Línia del moviment contable corresponent a la inversió",
            ),
        active=fields.boolean(
            "Activa",
            required=True,
            help="Permet activar o desactivar la inversió",
            )
        )

    _defaults = dict(
        active=lambda *a: True,
    )

    def effective_investments_tuple(self, cursor, uid,
            member=None, start=None, end=None,
            context=None):
        """
            List active investments between start and end, both included,
            for the member of for any member if member is None.
            If start is not specified, it lists activated before end.
            If end is not specified, it list activated and not deactivated
            before start.
            If neither start or end are specified all investments are listed
            active or not.
        """
        filters = []
        if member: filters.append( ('member_id','=',member) )
        if end: filters += [
            ('first_effective_date','<=',end), # No activation also filtered
            ]
        if start: filters += [
            '&',
            ('first_effective_date','!=',False),
            '|',
            ('last_effective_date','>=',start),
            ('last_effective_date','=',False),
            ]

        ids = self.search(cursor, uid, filters)
        contracts = self.read(cursor, uid, ids)

        def membertopartner(member_id):
            Member = self.pool.get('somenergia.soci')

            partner_id = Member.read(
                cursor, uid, member_id, ['partner_id']
            )['partner_id'][0]
            return partner_id

        return [
            (
                c['member_id'][0],
                c['first_effective_date'] and str(c['first_effective_date']),
                c['last_effective_date'] and str(c['last_effective_date']),
                c['nshares'],
            )
            for c in sorted(contracts, key=lambda x: x['id'] )
        ]

    def effective_investments(self, cursor, uid,
            member, start, end,
            context=None):

        return [
            ns(
                member=member,
                firstEffectiveDate=first and isodate(first),
                lastEffectiveDate=last and isodate(last),
                shares=shares,
            )
            for member, first, last, shares
            in self.effective_investments_tuple(cursor, uid, member, start, end, context)
        ]

    def effective_for_member(self, cursor, uid,
            member_id, first_date, last_date,
            context=None):

        return len(self.effective_investments_tuple(cursor, uid,
            member_id, first_date, last_date, context))>0

    def create_for_member(self, cursor, uid,
            member_id, start, stop, waitingDays, expirationYears,
            context=None):
        """
            Takes accounting information and generates GenkWh investments
            purchased among start and stop dates for the indicated member.
            If waitingDays is not None, activation date is set those
            days after the purchase date.
            If expirationYears is not None, expiration date is set, those
            years after the activation date.
        """

        Account = self.pool.get('account.account')
        MoveLine = self.pool.get('account.move.line')
        Member = self.pool.get('somenergia.soci')
        generationAccountPrefix = '163500'

        memberCode = Member.read(cursor, uid, member_id, ['ref'])
        accountCode = generationAccountPrefix + memberCode['ref'][1:]

        accountIds = Account.search(cursor, uid, [
            ('code','=',accountCode),
            ])

        criteria = [('account_id','in',accountIds)]
        if stop: criteria.append(('date_created', '<=', str(stop)))
        if start: criteria.append(('date_created', '>=', str(start)))

        movelinesids = MoveLine.search(
            cursor, uid, criteria,
            order='date_created asc, id asc',
            context=context
            )

        for line in MoveLine.browse(cursor, uid, movelinesids, context):
            # Filter out already converted move lines
            if self.search(cursor, uid,
                [('move_line_id','=',line.id)],
                context=context,
                ):
                continue

            activation = None
            lastDateEffective = None
            if waitingDays is not None:
                activation = str(
                    isodate(line.date_created)
                    +relativedelta(days=waitingDays))

                if expirationYears is not None:
                    lastDateEffective = str(
                        isodate(activation)
                        +relativedelta(years=expirationYears))

            self.create(cursor, uid, dict(
                member_id=member_id,
                nshares=(line.credit-line.debit)//100,
                purchase_date=line.date_created,
                first_effective_date=activation,
                last_effective_date=lastDateEffective,
                move_line_id=line.id,
                ))


    def create_from_accounting(self, cursor, uid,
            start, stop, waitingDays, expirationYears,
            context=None):
        """
            Takes accounting information and generates GenkWh investments
            purchased among start and stop dates.
            If waitingDays is not None, activation date is set those
            days after the purchase date.
            If expirationYears is not None, expiration date is set, those
            years after the activation date.
            TODO: Confirm that the expiration is relative to the activation
            instead the purchase.
        """

        Account = self.pool.get('account.account')
        MoveLine = self.pool.get('account.move.line')
        Member = self.pool.get('somenergia.soci')
        generationAccountPrefix = '163500%'

        accountIds = Account.search(cursor, uid, [
            ('code','ilike',generationAccountPrefix),
            ])

        criteria = [('account_id','in',accountIds)]
        if stop: criteria.append(('date_created', '<=', str(stop)))
        if start: criteria.append(('date_created', '>=', str(start)))

        movelinesids = MoveLine.search(
            cursor, uid, criteria,
            order='date_created asc, id asc',
            context=context
            )

        for line in MoveLine.browse(cursor, uid, movelinesids, context):
            # Filter out already converted move lines
            if self.search(cursor, uid,
                [('move_line_id','=',line.id)],
                context=context,
                ):
                continue

            partnerid = line.partner_id.id
            if not partnerid:
                # Handle cases with no partner_id
                membercode = int(line.account_id.code[4:])
                domain = [('ref', 'ilike', '%'+str(membercode).zfill(6))]
            else:
                domain = [('partner_id', '=', partnerid)]

            # partner to member conversion
            # ctx = dict(context)
            # ctx.update({'active_test': False})
            memberid = Member.search(cursor, uid, domain, context=context)[0]

            activation = None
            lastDateEffective = None
            if waitingDays is not None:
                activation = str(
                    isodate(line.date_created)
                    +relativedelta(days=waitingDays))

                if expirationYears is not None:
                    lastDateEffective = str(
                        isodate(activation)
                        +relativedelta(years=expirationYears))

            self.create(cursor, uid, dict(
                member_id=memberid,
                nshares=(line.credit-line.debit)//100,
                purchase_date=line.date_created,
                first_effective_date=activation,
                last_effective_date=lastDateEffective,
                move_line_id=line.id,
                ))

    def _create_from_accounting(self, cursor, uid,
            start, stop, waitingDays, expirationYears,
            context=None):
        """
            Takes accounting information and generates GenkWh investments
            purchased among start and stop dates.
            If waitingDays is not None, activation date is set those
            days after the purchase date.
            If expirationYears is not None, expiration date is set, those
            years after the activation date.
            TODO: Confirm that the expiration is relative to the activation
            instead the purchase.
        """

        query = _sqlfromfile('investment_from_accounting')
        cursor.execute(query, dict(
            start = start,
            stop = stop,
            waitingDays = waitingDays,
            expirationYears = expirationYears,
            generationAccountPrefix = '163500%',
            ))

        for (
                member_id,
                nshares,
                purchase_date,
                move_line_id,
                first_effective_date,
                last_effective_date, 
            ) in cursor.fetchall():

            self.create(cursor, uid, dict(
                member_id=member_id,
                nshares=nshares,
                purchase_date=purchase_date,
                first_effective_date=first_effective_date,
                last_effective_date=last_effective_date,
                move_line_id=move_line_id,
                ))

    def activate(self, cursor, uid,
            start, stop, waitingDays, expirationYears, force,
            context=None):
        criteria = []
        if not force: criteria.append(('first_effective_date', '=', False))
        if stop: criteria.append(('purchase_date', '<=', str(stop)))
        if start: criteria.append(('purchase_date', '>=', str(start)))

        investments_id = self.search(cursor, uid, criteria, context=context)
        investments = self.read(
            cursor, uid, investments_id, ['purchase_date'], context=context
        )

        for investment in investments:
            first_effective_date = (
                isodate(investment['purchase_date'])
                +relativedelta(days=waitingDays))
            updateDict = dict(
                first_effective_date=str(first_effective_date),
                )
            if expirationYears:
                last_effective_date = (
                    first_effective_date
                    +relativedelta(years=expirationYears))
                updateDict.update(
                    last_effective_date=str(last_effective_date),
                    )
            self.write(
                cursor, uid, investment['id'], updateDict, context=context
            )

class InvestmentProvider(ErpWrapper):

    def effectiveInvestments(self, member=None, start=None, end=None):
        Investment = self.erp.pool.get('generationkwh.investment')
        return Investment.effective_investments( self.cursor, self.uid,
                member, start, end, self.context)

    def effectiveForMember(self, member, first_date, last_date):
        Investment = self.erp.pool.get('generationkwh.investment')
        return Investment.effective_for_member(self.cursor, self.uid,
            member, first_date, last_date, self.context)


GenerationkWhInvestment()

