#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import unicode_literals

from genkwh_migratenames import *
import genkwh_migratenames
from pathlib2 import Path


class Migrator:
    def __init__(self, cr):
        self.cases = genkwh_migratenames.cases = ns.load('scripts/migration_aportacions.yaml')
        self.cr = cr

    def cleanUp(self):
        """Clean up inconsistencies in cases so that the rest of
        the migrations goes on painfully
        """
        step("Clean up cases")
        # TODO

    def getAllMovementsLines(self):
        parentAccount = self.cases.get('parentAccount', '1635')
        cachefile = Path('apos_movementlines-{}.yaml'.format(parentAccount))
        if False and cachefile.exists():
            print("loading from cache {}".format(cachefile))
            return ns.load(str(cachefile)).data
        self.cr.execute("""\
            select
                ml.id,
                ml.move_id,
                ml.name as name,
                ml.date_created as date_created,
                ml.credit,
                ml.debit,
                CASE WHEN COALESCE(moveline_partner.id,1) = 1
                    THEN account_partner.ref
                    ELSE moveline_partner.ref
                    END AS partner_ref,
                CASE WHEN COALESCE(moveline_partner.id,1) = 1
                    THEN account_partner.id
                    ELSE moveline_partner.id
                    END AS partner_id,
                CASE WHEN COALESCE(moveline_partner.id,1) = 1
                    THEN account_partner.name
                    ELSE moveline_partner.name
                    END AS partner_name,
                ml.credit-ml.debit as amount,
                account.name as account_name,
                account.code as account_code,
                COALESCE(usr.name, 'Nobody') as username,
                account_partner.id as account_partner_id,
                moveline_partner.id as moveline_partner_id,
                true
            from
                account_move_line as ml
            left join
                account_period as period
            on
                period.id = ml.period_id
            left join
                account_account as account
            on
                ml.account_id=account.id
            left join
                account_account as parent_account
            on
                parent_account.id = account.parent_id
            left join
                res_users as usr
            on
                usr.id = ml.create_uid
            left join
                res_partner as account_partner
            on
                account_partner.ref = ('S' || right(account.code, 6))
            left join
                res_partner as moveline_partner
            on
                ml.partner_id = moveline_partner.id
            where
                parent_account.code = %(parentAccount)s and
                not period.special and
                true
            order by
                partner_id,
                ml.id,
                true
        """, dict(
            parentAccount = parentAccount,
        ))
        result = dbutils.nsList(self.cr)
        ns(data=result).dump(str(cachefile))
        return result

    def listMovementsByPartner(self):
        movements = self.getAllMovementsLines()

        self.movements = {
            movement.id: movement
            for movement in movements
        }
        self.movementsByPartner = {}
        for movement in movements:
            self.movementsByPartner.setdefault(movement.partner_id, []).append(movement)

    def dumpMovementsByPartner(self):
        with Path('apos_movementlines.csv').open('w', encoding='utf8') as output:
            for partner_id in sorted(self.movementsByPartner):
                movements = self.movementsByPartner[partner_id]
                output.write("({partner_id}) {partner_ref} {partner_name}\n".format(**movements[0]))
                for movement in movements:
                    output.write("\t{account_code}\t{date_created}\t{credit: 10f}\t{debit: 10f}\t{id: 10d}\t{name}\n".format(**movement))
        return movements

    def matchPaymentOrders(self):
        ''

    def doSteps(self):
        self.cleanUp()
        self.listMovementsByPartner()
        self.matchPaymentOrders()
        self.dumpMovementsByPartner()
        #main(cr)
        #deleteNullNamedInvestments(cr)
        #showUnusedMovements(cr)
        #displayAllInvestments(cr)

    @staticmethod
    def run():
        with psycopg2.connect(**dbconfig.psycopg) as db:
            with db.cursor() as cr:
                psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, cr)
                with transaction(cr, discarded='--doit' not in sys.argv):
                    m = Migrator(cr)
                    m.doSteps()

Migrator.run()

# vim: et ts=4 sw=4
