# -*- coding: utf-8 -*-

from osv import osv, fields
from .erpwrapper import ErpWrapper
from plantmeter.mongotimecurve import toLocal
from dateutil.relativedelta import relativedelta
import datetime
from yamlns import namespace as ns
from generationkwh.isodates import localisodate, naiveisodate, naiveisodatetime

class InvestmentProvider(ErpWrapper):

    def shareContractsTuple(self, member=None, start=None, end=None):
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
            ('activation_date','<=',end), # No activation also filtered
            ]
        if start: filters += [
            '&',
            ('activation_date','!=',False),
            '|',
            ('deactivation_date','>=',start),
            ('deactivation_date','=',False),
            ]

        Investment = self.erp.pool.get('generationkwh.investment')
        ids = Investment.search(self.cursor, self.uid, filters)
        contracts = Investment.read(self.cursor, self.uid, ids)

        def membertopartner(member_id):
            Member = self.erp.pool.get('somenergia.soci')

            partner_id = Member.read(
                self.cursor, self.uid, member_id, ['partner_id']
            )['partner_id'][0]
            return partner_id

        return [
            (
                membertopartner(c['member_id'][0]),
                localisodate(c['activation_date']),
                localisodate(c['deactivation_date']),
                c['nshares'],
            )
            for c in sorted(contracts, key=lambda x: x['id'] )
        ]

    def shareContracts(self, member=None, start=None, end=None):
        return [
            ns(
                member=member,
                activationStart=start,
                activationEnd=end,
                shares=shares,
            )
            for member, start, end, shares
            in self.shareContractsTuple(member, start, end)
        ]

class GenerationkWhInvestment(osv.osv):

    _name = 'generationkwh.investment'

    _columns = dict(
        member_id=fields.many2one(
            'somenergia.soci',
            "Inversor",
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
        activation_date=fields.date(
            "Data d'activació",
            help="Dia que les accions començaran a generar drets a kWh",
            ),
        deactivation_date=fields.date(
            "Data de desactivació",
            help="Dia que les accions deixaran de generar drets a kWh",
            ),
        move_line_id=fields.many2one(
            'account.move.line',
            'Línia del moviment contable',
            required=True,
            help="Línia del moviment contable corresponent a la inversió",
            )
        )

    def active_investments(self, cursor, uid,
            member, start, end,
            context=None):

        provider = InvestmentProvider(self, cursor, uid, context)
        return provider.shareContractsTuple(member, start, end)


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

        accountIds = Account.search(cursor, uid, [('code','ilike','163500%')])

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
            memberid = Member.search(cursor, uid, domain)[0]

            activation = None
            deactivation = None
            if waitingDays is not None:
                activation = str(
                    naiveisodate(line.date_created)
                    +relativedelta(days=waitingDays))

                if expirationYears is not None:
                    deactivation = str(
                        naiveisodatetime(activation)
                        +relativedelta(years=expirationYears))

            self.create(cursor, uid, dict(
                member_id=memberid,
                nshares=(line.credit-line.debit)//100,
                purchase_date=line.date_created,
                activation_date=activation,
                deactivation_date=deactivation,
                move_line_id=line.id,
                ))


GenerationkWhInvestment()

