# -*- coding: utf-8 -*-

from osv import osv, fields
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from tools.translate import _
from mongodb_backend.mongodb2 import mdbpool

from generationkwh.sharescurve import MemberSharesCurve
from generationkwh.rightspershare import RightsPerShare
from generationkwh.memberrightscurve import MemberRightsCurve
from generationkwh.memberrightsusage import MemberRightsUsage
from generationkwh.usagetracker import UsageTracker
from generationkwh.fareperiodcurve import FarePeriodCurve
from .remainder import RemainderProvider
from .investment import InvestmentProvider
from .holidays import HolidaysProvider


class ResPartner(osv.osv):

    _name = 'res.partner'
    _inherit = 'res.partner'

    def www_generationkwh_investments(self, cursor, uid, id, context=None):
        """
        Returns the list of investments type Generationkwh
        """
        Investment =self.pool.get('generationkwh.investment')
        Dealer =self.pool.get('generationkwh.dealer')
        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: # Not a member
            return []
        return Investment.list(cursor, uid, idmap[id], 'genkwh', context=context)

    def www_aportacions_investments(self, cursor, uid, id, context=None):
        """
        Returns the list of investments type Aportacions
        """
        Investment =self.pool.get('generationkwh.investment')
        Dealer =self.pool.get('generationkwh.dealer')
        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: # Not a member
            return []
        return Investment.list(cursor, uid, idmap[id], 'apo', context=context)

    def www_generationkwh_assignments(self, cursor, uid, id, context=None):
        Dealer =self.pool.get('generationkwh.dealer')
        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: return [] # Not a member

        Assignments =self.pool.get('generationkwh.assignment')
        assignment_ids = Assignments.search(cursor, uid, [
            ('member_id', '=', idmap[id]),
            ('end_date', '=', False),
            ])
        def process(x):
            x['contract_name'] = x['contract_id'][1]
            x['contract_id'] = x['contract_id'][0]
            x['member_name'] = x['member_id'][1]
            x['member_id'] = x['member_id'][0]
            x['annual_use_kwh'] = x.pop('cups_anual_use')
            x['contract_address'] = x.pop('cups_direction')
            del x['end_date']
            return x

        return sorted([
            process(x)
            for x in Assignments.read(cursor, uid, assignment_ids, [])
        ], key=lambda x: (x['priority'],x['id']))


    def www_set_generationkwh_assignment_order(self, cursor, uid, id, sorted_assignment_ids, context=None):
        Dealer = self.pool.get('generationkwh.dealer')
        Assignments = self.pool.get('generationkwh.assignment')

        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: return [] # Not a member

        # Check if all assignments are owner by the partner
        assignments = Assignments.read(cursor, uid, sorted_assignment_ids, [])
        for partner in Dealer.get_partners_by_members(
                cursor, uid, [assignment["member_id"][0] for assignment in assignments]):
            if partner[1] != id:
                raise Exception("There are different member_ids")

        # Check that all assignments are ordered at once
        actual_assignment_ids = Assignments.search(cursor, uid, [
            ('member_id', '=', idmap[id]),
            ('end_date', '=', False),
        ])
        if (
            len(actual_assignment_ids) != len(sorted_assignment_ids)
            or set(actual_assignment_ids) != set(sorted_assignment_ids)
        ):
            raise Exception("You need to order all the assignments at once")

        for order, assignment_id in enumerate(sorted_assignment_ids):
            Assignments.write(cursor, uid, [assignment_id], {'priority': order})

        return self.www_generationkwh_assignments(cursor, uid, id, context)


    def www_hourly_remaining_generationkwh(self, cursor, uid, partner_id, context=None):
        Dealer = self.pool.get('generationkwh.dealer')

        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [partner_id]))
        if not idmap: return [] # Not a member
        member_id = idmap[partner_id]

        end_date = date.today()
        start_date = end_date - relativedelta(years=1)

        rightsPerShare = RightsPerShare(mdbpool.get_db())
        rightsUsage = MemberRightsUsage(mdbpool.get_db())
        investment = InvestmentProvider(self, cursor, uid, context)
        memberActiveShares = MemberSharesCurve(investment)
        remainders = RemainderProvider(self, cursor, uid, context)
        generatedRights = MemberRightsCurve(
            activeShares=memberActiveShares,
            rightsPerShare=rightsPerShare,
            remainders=remainders,
            eager=True,
        )

        rights = generatedRights.rights_kwh(member_id, start_date, end_date)
        usage = rightsUsage.usage(member_id, start_date, end_date)

        remaining = UsageTracker.convert_usage_date_quantity(enumerate((
            produced - used
            for produced, used
            in zip(rights, usage)
        )), start_date)

        return remaining


ResPartner()

# vim: et sw=4 ts=4
