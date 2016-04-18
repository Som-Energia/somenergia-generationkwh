# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields
from mongodb_backend.mongodb2 import mdbpool

from generationkwh.dealer import Dealer
from generationkwh.sharescurve import MemberSharesCurve
from generationkwh.rightspershare import RightsPerShare
from generationkwh.memberrightscurve import MemberRightsCurve
from generationkwh.memberrightsusage import MemberRightsUsage
from generationkwh.fareperiodcurve import FarePeriodCurve
from generationkwh.usagetracker import UsageTracker
from plantmeter.mongotimecurve import toLocal
from yamlns import namespace as ns

import datetime
from dateutil.relativedelta import relativedelta
import netsvc

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
def isodate(date):
    return date and datetime.datetime.strptime(date, '%Y-%m-%d')
def localisodate(date):
    return date and toLocal(datetime.datetime.strptime(date, '%Y-%m-%d'))

# Data providers

class ErpWrapper(object):

    def __init__(self, erp, cursor, uid, context=None):
        self.erp = erp
        self.cursor = cursor
        self.uid = uid
        self.context = context

class RemainderProvider(ErpWrapper):
    def get(self):
        remainders=self.erp.pool('generationkwh.remainders')
        return remainders.last(self.cursor,self.uid, context=self.context)
    def set(self,remainders):
        remainders=self.erp.pool('generationkwh.remainders')
        remainders.add(self.cursor,self.uid,remainders, context=self.context)

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

        return [
            (
                c['member_id'][0],
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

class HolidaysProvider(ErpWrapper):

    def get(self, start, stop):
        Holidays = self.erp.pool.get('giscedata.dfestius')
        ids = Holidays.search(self.cursor, self.uid, [
            ('name', '>=', start),
            ('name', '<=', stop),
            ], 0,None,'name desc',self.context)
        return [
            isodate(h['name'])
            for h in Holidays.read(self.cursor, self.uid,
                ids, ['name'], self.context)
            ]

# Models

class GenerationkWhTestHelper(osv.osv):
    """
        Helper model that enables accessing data providers
        from tests written with erppeek.
    """

    _name = 'generationkwh.testhelper'
    _auto = False

    def holidays(self, cursor, uid,
            start, stop,
            context=None):
        holidaysProvider = HolidaysProvider(self, cursor, uid, context)
        return holidaysProvider.get(start, stop)

    def setup_rights_per_share(self, cursor, uid,
            nshares, startDate, data,
            context=None):
        rightsPerShare = RightsPerShare(mdbpool.get_db())
        rightsPerShare.updateRightsPerShare(nshares, localisodate(startDate), data)

    def clear_mongo_collections(self, cursor, uid, collections, context=None):
        for collection in collections:
            mdbpool.get_db().drop_collection(collection)



    def trace_rigths_compilation(self, cursor, uid,
            member, start, stop, fare, period,
            context=None):
        """
            Helper function to show data related to computation of available
            rights.
        """
        print "Dropping results for", member, start, stop, fare, period
    
        investment = InvestmentProvider(self, cursor, uid, context)
        memberActiveShares = MemberSharesCurve(investment)
        rightsPerShare = RightsPerShare(mdbpool.get_db())

        generatedRights = MemberRightsCurve(
            activeShares=memberActiveShares,
            rightsPerShare=rightsPerShare,
            eager=True,
            )
        rightsUsage = MemberRightsUsage(mdbpool.get_db())
        holidays = HolidaysProvider(self, cursor, uid, context)
        farePeriod = FarePeriodCurve(holidays)

        print 'investment', investment.shareContracts(
            start=localisodate(start),
            end=localisodate(stop),
            member=2)
        print 'active', memberActiveShares.hourly(
            localisodate(start),
            localisodate(stop),
            member)
        for nshares in set(memberActiveShares.hourly(
            localisodate(start),
            localisodate(stop),
            member)):
            print 'rightsPerShare', nshares, rightsPerShare.rightsPerShare(nshares,
                localisodate(start),
                localisodate(stop),
                )
        print 'rights', generatedRights.rights_kwh(member,
            localisodate(start),
            localisodate(stop),
            )

        print 'periodmask', farePeriod.periodMask(
            fare, period,
            localisodate(start),
            localisodate(stop),
            )

    def usagetracker_available_kwh(self, cursor, uid,
            member, start, stop, fare, period,
            context=None):

        GenerationkWhDealer = self.pool.get('generationkwh.dealer')
        usageTracker = GenerationkWhDealer._createTracker(cursor, uid, context)
        result = usageTracker.available_kwh(
            member,
            localisodate(start),
            localisodate(stop),
            fare,
            period
            )
        return result


GenerationkWhTestHelper()

class GenerationkWhRemainders(osv.osv):
    """
    Remainders, in Wh, after dividing the aggregated
    production of the plants into a hourly curve of
    available kWh for a member with a given number of
    shares.
    """

    _name = "generationkwh.remainders"
    _columns = dict(
        n_shares=fields.integer(
            required=True,
            help="Number of shares"
        ),
        target_day=fields.date(
            required=True,
            help="Day after the last day computed. The one to carry the remainder on."
        ),
        remainder_wh=fields.integer(
            required=True,
            help="Remainder in Wh"
        )
    )

    _sql_constraints = [(
        'unique_n_shares_target_day', 'unique(n_shares,target_day)',
            'Only one remainder of last date computed and number of shares '
            'is allowed'
        )]

    def last(self, cr, uid, context=None):
        cr.execute("""
            SELECT o.n_shares,o.target_day,o.remainder_wh
                FROM generationkwh_remainders AS o
                LEFT JOIN generationkwh_remainders AS b
                    ON o.n_shares=b.n_shares
                    AND o.target_day < b.target_day
                WHERE b.target_day IS NULL
            """)
        result = [
            (
                n_shares,
                target_day,
                remainder_wh,
            ) for n_shares, target_day, remainder_wh in cr.fetchall()
        ]
        return result

    def add(self, cr, uid, remainders, context=None):
        for n,pointsDate,remainder in remainders:
            same_date_n_id=self.search(cr, uid, [
                ('n_shares','=',n),
                ('target_day','=', pointsDate),
            ], context=context)
            if same_date_n_id:
                self.unlink(
                    cr, uid,
                    same_date_n_id, context=context
                )
            self.create(cr,uid,{
                'n_shares': n,
                'target_day': pointsDate,
                'remainder_wh': remainder
            }, context=context)

    def clean(self,cr,uid,context=None):
        ids=self.search(cr,uid, [], context=context)
        self.unlink(cr,uid,ids)

GenerationkWhRemainders()


class GenerationkWhAssignments(osv.osv):

    _name = 'generationkwh.assignments'

    _columns = dict(
        active=fields.boolean(
            "Active",
            default=True,
            ),
        contract_id=fields.many2one(
            'giscedata.polissa',
            'Contract',
            required=True,
            help="Contract which gets rights to use generated kWh",
            ),
        member_id=fields.many2one(
            'res.partner',
            'Member',
            required=True,
            help="Member who bought Generation kWh shares and assigns them",
            ),
        priority=fields.integer(
            'Priority',
            required=True,
            help="Assignment precedence. "
                "This assignment won't use rights generated on dates that have not "
                "been invoiced yet by assignments of the same member having higher priority "
                "(lower the value, higher the priority).",
            ),
        end_date=fields.date(
            'Expiration date',
            help="Date at which the rule is no longer active",
            ),
        )
    _defaults = dict(
        active=lambda *a: 1,
        )

    def add(self, cr, uid, assignments, context=None):
        for active, contract_id, member_id, priority in assignments:
            same_polissa_member = self.search(cr, uid, [
                ('contract_id', '=', contract_id),
                ('member_id', '=', member_id),
            ], context = context)
            if same_polissa_member:
                self.write(cr,uid,
                    same_polissa_member,
                    dict(
                        active=False,
                        end_date=str(datetime.date.today()),
                    ),
                    context=context,
                )
            self.create(cr, uid, {
                'active': active,
                'contract_id': contract_id,
                'member_id': member_id,
                'priority': priority,
            }, context=context)

    def dropAll(self, cr, uid, context=None):
        """Remove all records"""
        ids = self.search(cr, uid, [
            '|',
            ('active', '=', False),
            ('active', '=', True),
            ],context=context)
        for a in self.browse(cr, uid, ids, context=context):
            a.unlink()

    def expire(self, cr, ids, context=None):
        ""


GenerationkWhAssignments()


class GenerationkWhInvestment(osv.osv):

    _name = 'generationkwh.investment'

    _columns = dict(
        member_id=fields.many2one(
            'res.partner',
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
        )

    def active_investments(self, cursor, uid,
            member, start, end,
            context=None):

        provider = InvestmentProvider(self, cursor, uid, context)
        return provider.shareContractsTuple(member, start, end)


    def create_investments_from_accounting(self, cursor, uid,
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
        Partner = self.pool.get('res.partner')

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
            partnerid = line.partner_id.id
            if not partnerid:
                # Handle cases with no partner_id
                membercode = int(line.account_id.code[4:])
                partnerid = Partner.search(cursor, uid, [
                    ('ref', 'ilike', '%'+str(membercode).zfill(6))
                    ])[0]
            activation = None
            deactivation = None
            if waitingDays is not None:
                activation = str(
                    isodate(line.date_created)
                    +relativedelta(days=waitingDays))

                if expirationYears is not None:
                    deactivation = str(
                        isodatetime(activation)
                        +relativedelta(years=expirationYears))

            self.create(cursor, uid, dict(
                member_id=partnerid,
                nshares=(line.credit-line.debit)//100,
                purchase_date=line.date_created,
                activation_date=activation,
                deactivation_date=deactivation,
                ))

    def create_investments_from_paymentlines(self, cursor, uid,
            start, stop, waitingDays, expirationYears,
            context=None):
        tail = 0,None,None,context

        criteria = [('name','like','GKWH')]
        if stop: criteria.append(('create_date', '<=', str(stop)))
        if start: criteria.append(('create_date', '>=', str(start)))

        PaymentLine = self.pool.get('payment.line')
        paymentlineids = PaymentLine.search(cursor, uid, criteria,*tail)
        for payment in PaymentLine.browse(cursor, uid, paymentlineids, context):
            activation = None
            deactivation = None
            if waitingDays is not None:
                activation = str(
                    isodatetime(payment.create_date)
                    +relativedelta(days=waitingDays))

                if expirationYears is not None:
                    deactivation = str(
                        isodatetime(activation)
                        +relativedelta(years=expirationYears))

            self.create(cursor, uid, dict(
                member_id=payment.partner_id.id,
                nshares=-payment.amount_currency//100,
                purchase_date=payment.create_date,
                activation_date=activation,
                deactivation_date=deactivation,
                ))

GenerationkWhInvestment()


class GenerationkWhDealer(osv.osv):

    _name = 'generationkwh.dealer'
    _auto = False

    def is_active(self, cursor, uid,
                  contract_id, start_date, end_date,
                  context=None):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        dealer = self._createDealer(cursor, uid, context)

        return dealer.is_active(
            contract_id, start_date, end_date)

    def get_available_kwh(self, cursor, uid,
                          contract_id, start_date, end_date, fare, period,
                          context=None):
        """ Returns generationkwh [kWh] available for contract_id during the
            date interval, fare and period"""
        dealer = self._createDealer(cursor, uid, context)

        return dealer.get_available_kwh(
            contract_id, start_date, end_date, fare, period)

    def use_kwh(self, cursor, uid,
                contract_id, start_date, end_date, fare, period, kwh,
                context=None):
        """Marks the indicated kwh as used, if available, for the contract,
           date interval, fare and period and returns the ones efectively used.
        """
        logger = netsvc.Logger()
        dealer = self._createDealer(cursor, uid, context)

        res = dealer.use_kwh(
            contract_id, start_date, end_date, fare, period, kwh)

        txt_vals = dict(
            contract=contract_id,
            period=period,
            start=start_date,
            end=end_date,
        )
        txt =''
        for line in res:
            txt_vals.update(dict(
                kwh=line['kwh'],
                member=line['member_id'],
            ))
            txt = (u'{kwh} Generation kwh of member {member} to {contract} '
                   u'for period {period} between {start} and {end}').format(
                **txt_vals
            )
            logger.notifyChannel('gkwh_dealer USE', netsvc.LOG_INFO, txt)

        return res

    def refund_kwh(self, cursor, uid,
                   contract_id, start_date, end_date, fare, period, kwh,
                   partner_id, context=None):
        """Refunds the indicated kwh, marking them as available again, for the
           contract, date interval, fare and period and returns the ones
           efectively used.
        """
        logger = netsvc.Logger()
        dealer = self._createDealer(cursor, uid, context)

        txt_vals = dict(
            contract=contract_id,
            period=period,
            start=start_date,
            end=end_date,
            member=partner_id,
            kwh=kwh
        )
        txt = (u'{kwh} Generation kwh of member {member} to {contract} '
               u'for period {period} between {start} and {end}').format(
            **txt_vals
        )
        logger.notifyChannel('gkwh_dealer REFUND', netsvc.LOG_INFO, txt)
        res = dealer.refund_kwh(
            contract_id, start_date, end_date, fare, period, kwh, partner_id)
        return res

    def _createTracker(self, cursor, uid, context):

        investments = InvestmentProvider(self, cursor, uid, context)
        memberActiveShares = MemberSharesCurve(investments)
        rightsPerShare = RightsPerShare(mdbpool.get_db())

        generatedRights = MemberRightsCurve(
            activeShares=memberActiveShares,
            rightsPerShare=rightsPerShare,
            eager=True,
            )

        rightsUsage = MemberRightsUsage(mdbpool.get_db())

        holidays = HolidaysProvider(self, cursor, uid, context)
        farePeriod = FarePeriodCurve(holidays)

        return UsageTracker(generatedRights, rightsUsage, farePeriod)

    def _createDealer(self, cursor, uid, context):

        usageTracker = self._createTracker(cursor, uid, context)
        # TODO: Feed the dealer with data sources
        return Dealer(usageTracker)

GenerationkWhDealer()


class GenerationkWhInvoiceLineOwner(osv.osv):
    """ Class with the relation between generation invoice line and rights owner
    """

    _name = 'generationkwh.invoice.line.owner'

    def name_get(self, cursor, uid, ids, context=None):
        """GkWH name"""
        res = []
        glo_vals = self.read(cursor, uid, ids, ['factura_line_id'])
        for glo in glo_vals:
            res.append((glo['id'], glo['factura_line_id'][1]))

        return res

    def _ff_invoice_number(self, cursor, uid, ids, field_name, arg,
                           context=None ):
        """Invoice Number"""
        if not ids:
            return []
        res = dict([(i, False) for i in ids])
        f_obj = self.pool.get('giscedata.facturacio.factura')

        glo_vals = self.read(cursor, uid, ids, ['factura_id'])
        inv_ids = [g['factura_id'][0] for g in glo_vals]
        inv_vals = f_obj.read(cursor, uid, inv_ids, ['number'])
        inv_dict = dict([(i['id'], i['number']) for i in inv_vals])
        for glo_val in glo_vals:
            glo_id = glo_val['id']
            glo_number = inv_dict[glo_val['factura_id'][0]]
            res.update({glo_id: glo_number})

        return res

    _columns = {
        'factura_id': fields.many2one(
            'giscedata.facturacio.factura', 'Factura', required=True,
            readonly=True
        ),
        'factura_number': fields.function(
            _ff_invoice_number, string='Num. Factura', method=True, type='char',
            size='64',
        ),
        'factura_line_id': fields.many2one(
            'giscedata.facturacio.factura.linia', 'Línia de factura',
            required=True, readonly=True
        ),
        'owner_id': fields.many2one(
            'res.partner', 'Soci Generation', required=True, readonly=True
        ),
    }

GenerationkWhInvoiceLineOwner()

# vim: ts=4 sw=4 et
