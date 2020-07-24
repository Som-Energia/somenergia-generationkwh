#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import unicode_literals

from genkwh_migratenames import *
import genkwh_migratenames
from pathlib2 import Path
import re
from consolemsg import out


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

    def getAllInvestments(self):
        emission = self.cases.get('emissionType', 'genkwh')
        cachefile = Path('cached-apos-investments-{}.yaml'.format(emission))
        self.cr.execute("""
            select investment.*
            from
                generationkwh_investment as investment
            left join
                generationkwh_emission as emission
                on investment.emission_id = emission.id
            where
                emission.type = %(emission)s
            order by
                investment.name
            ;
        """, dict(
            emission = emission,
        ))
        result = dbutils.nsList(self.cr)
        ns(data=result).dump(str(cachefile))
        return result

    def getAllMovementsLines(self):
        parentAccount = self.cases.get('parentAccount', '1635')
        cachefile = Path('apos_movementlines-{}.yaml'.format(parentAccount))
        if False and cachefile.exists():
            out("loading from cache {}".format(cachefile))
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

    def peerMoveLine(self, moveline_id):
        parentAccount = '555000000011'
        self.cr.execute("""
            select
                peerline.id,
                account.name,
                account.code
            from account_move_line as moveline
            left join account_move as move
            on move.id = moveline.move_id
            left join account_move_line as peerline
            on move.id = peerline.move_id
            left join account_account as account
            on peerline.account_id = account.id
            where moveline.id = %(moveline_id)s
            and account.code =  %(parent_account)s
            ;
        """, dict(
            moveline_id=moveline_id,
            parent_account=parentAccount,
        ))
        result = dbutils.nsList(self.cr)
        ns(result=result).dump()
        if not result: return None
        return result[0].id

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
                    if 'solution' in movement:
                        output.write("\t\t{name}\t{type}\t{solution}\n".format(solution=movement.solution, **movement.solution))

    def dumpUnsolved(self):
        with Path('unsolved.yaml').open('w', encoding='utf8') as output:
            output.write("unsolved:\n")
            for partner_id in sorted(self.movementsByPartner):
                movements = self.movementsByPartner[partner_id]
                if all('solution' in movement for movement in movements):
                    continue # all solved
                investments = list(sorted(set(
                    movement.solution.name
                    for movement in movements
                    if 'solution' in movement
                )))
                for investment in investments:
                    output.write(
                        "  {0}: # {1.partner_ref} {1.partner_name}\n"
                            .format(investment, movements[0]))
                    for movement in movements:
                        if 'solution' not in movement: continue
                        if movement.solution.name != investment: continue
                        output.write("    {id}: {solution.type} # {date_created} ({partner_name}) {amount} {name}\n".format(**movement))
                output.write(
                    "#  unsolved: # {partner_ref} {partner_name}\n"
                        .format(**movements[0]))
                for movement in movements:
                    if 'solution' in movement: continue
                    output.write("#    {id}: unknown # {date_created} ({partner_name}) {amount} {name}\n".format(**movement))
                output.write("\n")

    def matchPaymentOrders(self):

        paymentMoveLines = ns()
        matchedOrderLines = []

        def bindMoveLineAndPaymentLine(moveline, orderline):
            communication = orderline.communication2
            ip = communication.split(" IP ")[1] if communication and ' IP ' in communication else '0.0.0.0'
            moveline.partner_name = moveline.partner_name and u(moveline.partner_name)
            False and success(
                u"Match ml-po ml-{moveline.id} {orderline.name} {orderline.create_date} {amount:=8}€ {moveline.partner_name} {ip}"
                .format(
                    moveline=moveline,
                    orderline=orderline,
                    amount = moveline.credit-moveline.debit,
                    ip = ip,
                ))
            paymentMoveLines[moveline.id] = ns(
                movelineid = moveline.id,
                ref=orderline.name,
                order_date=orderline.create_date,
                partner_id = orderline.partner_id,
                partner_name = orderline.partner_name,
                amount = moveline.credit-moveline.debit,
                ip = ip,
                )
            matchedOrderLines.append(orderline.id)
            self.movements[moveline.id].update(
                solution = ns(
                    type = 'paid',
                    name = orderline.name,
                    orderline_id = orderline.id,
                    ip = ip,
                )
            )

        order2MovementMatches = investmentOrderAndMovements(self.cr)
        for o2m in order2MovementMatches:
            step(" Quadrant remesa feta el {move_create_date}".format(**o2m))
            step("  Comprovant que la remesa i el moviment coincideixen. "
                "Ordres a la remesa: {}, Assentaments al moviment: {}",
                o2m.order_nlines,
                o2m.move_nlines,
            )
            if not o2m.move_id:
                warn("Remesa sense moviment. {}: Id {}, amb {} linies" .format(
                    o2m.order_sent_date or "not yet",
                    o2m.order_id,
                    o2m.order_nlines,
                    ))
                continue
            if not o2m.order_id:
                warn("Moviment sense remesa. {}: Id {}, amb {} linies".format(
                    o2m.move_create_date or "sense o2m",
                    o2m.move_id,
                    o2m.move_nlines,
                    ))
                continue

            if o2m.move_nlines != o2m.order_nlines:
                warn("{}: Different number of lines. Payment order {}, Movement {}".format(
                    o2m.move_create_date,
                    o2m.order_nlines,
                    o2m.move_nlines,
                    ))

            orderLines = getOrderLines(self.cr, o2m.order_id)
            moveLines = getMoveLines(self.cr, o2m.move_id)

            if len(orderLines) != o2m.order_nlines:
                warn("Got different number of lines {} than reported {} in Order"
                    .format(len(orderLines), o2m.order_nlines))

            if len(moveLines) != o2m.move_nlines:
                warn("Got different number of lines {} than reported {} in Move"
                    .format(len(moveLines), o2m.move_nlines))

            step("  Quadrant pagaments amb apunts per persona i quantitat")
            orderLinesDict = ns()
            repesca = []

            #step("  Create a map partner,amount -> orderline")
            for line in orderLines:
                key = (line.partner_id, -line.amount)
                appendToKey(orderLinesDict, key, line)

            #step("  for each move line look up orderlines by partner,amount")
            for moveline in moveLines:
                key = (moveline.partner_id, moveline.credit)
                orderline = getAndRemoveFirst(orderLinesDict, key)
                if not orderline:
                    repesca.append(moveline)
                    continue

                # orderline-movementline match found
                bindMoveLineAndPaymentLine(moveline, orderline)

            if repesca: step("  Repescant els que no coincideix la quantitat")

            #step("  Create a partner -> unpaired movelines map")
            movelinesByPartnerId = {}
            for moveline in repesca:
                if moveline.id in paymentMoveLines: continue
                appendToKey(movelinesByPartnerId, moveline.partner_id, moveline)

            #step("  Lookup for each unpaired order")
            for key, options in orderLinesDict.items():
                for orderline in options:
                    if orderline.id in matchedOrderLines:
                        options.remove(orderline)
                        continue

                    moveline = getAndRemoveFirst(movelinesByPartnerId, orderline.partner_id)
                    if not moveline:
                        error(
                            "Linia de Remesa sense apunt: "
                            "{name} id {id} {order_sent_date} {amount}€ {partner_name}",
                            **orderline)
                        continue
                    bindMoveLineAndPaymentLine(moveline, orderline)
                    if orderline.name not in self.cases.misscorrectedPayments:
                        error(
                            "Amount missmatch {orderline.name} "
                            "order {orderline.amount}€ move {moveline.credit}",
                                partner_id = moveline.partner_id,
                                orderline=orderline,
                                moveline=moveline,
                            )
                        displayPartnersMovements(self.cr, orderline.partner_id)
                        continue
                    corrected = self.cases.misscorrectedPayments[orderline.name]
                    if corrected != moveline.credit:
                        error(
                            "Badly corrected amount missmatch {orderline.name}  "
                            "order {orderline.amount}€ move {moveline.credit} "
                            "corrected {corrected}€",
                                partner_id = moveline.partner_id,
                                orderline=orderline,
                                moveline=moveline,
                                corrected=corrected,
                            )
                        displayPartnersMovements(self.cr, orderline.partner_id)
                        continue
                    warn(
                        "Already corrected amount missmatch {orderline.name} "
                        "order {orderline.amount}€ move {moveline.credit}"
                        .format(
                            orderline=orderline,
                            moveline=moveline,
                        ))

            for partner_id, movelines in movelinesByPartnerId.items():
                for moveline in movelines:
                    error(
                        "Apunt sense linea de remesa "
                        "id {id} {create_date} {credit}€ {partner_name}",
                        **moveline)

    def matchExistingInvestments(self):
        for investment in self.investments.values():
            out(investment.name)
            log = investment.log
            loglines = log.split('\n')
            for logline in loglines:
                out(logline)
                if not logline: continue
                action = re.search(r'\] ([A-Z]+):', logline)
                if not action:
                    warn("Unrecognized action in: ".format(logline))
                    continue
                action = action.group(1)
                move = re.search(r'\[([0-9]+)\]', logline)
                if not move:
                    #warn("Action {} without moveline".format(action))
                    continue
                move_id=int(move.group(1))
                move_id=self.peerMoveLine(move_id)
                if move_id not in self.movements:
                    #warn("Action {} refers movement {} not found".format(action, move_id))
                    continue
                movement = self.movements[move_id]
                if 'solution' in movement:
                    warn("Invesment {} referring an solved movement {}",
                        invesment.name, movement.id)
                success(action)
                movement.solution=ns(
                    type=action.lower(),
                )

    def solveExistingInvestments(self):
        step("Solving movements referring existing Invesments")
        unsolvedInvestments = set(self.investments.keys())
        for moveline_id, moveline in self.movements.items():
            if not (
                moveline.name.startswith("Inversió APO00") or
                moveline.name.startswith("Inversión APO00")
            ): continue
            investment_name = moveline.name.split()[1]
            if investment_name not in unsolvedInvestments:
                error("Movement {} refers not pending {}",
                    moveline_id,
                    investment_name,
                )
                continue

            if 'solution' in moveline:
                error("Movement {} refers already solved",
                    moveline_id,
                )
                continue

            moveline.solution=ns(
                type='existing',
                name=investment_name,
                )
            unsolvedInvestments.remove(investment_name)

    def resolve(self):
        for investment_name, actions in self.cases.legacyCases.items():
            for moveline_id, action in sorted(actions.items()):
                try:
                    action.type
                except AttributeError:
                    action = ns(
                        type = action,
                    )

                self.movements[moveline_id].solution = ns(
                    action,
                    name = investment_name,
                )

    def doSteps(self):
        self.cleanUp()
        self.investments = {
            investment.name: investment
            for investment in self.getAllInvestments()
        }
        self.listMovementsByPartner()
        self.matchPaymentOrders()
        #self.matchExistingInvestments()
        self.solveExistingInvestments()
        self.resolve()
        self.dumpMovementsByPartner()
        self.dumpUnsolved()
        #main(cr)
        #deleteNullNamedInvestments(cr)
        #showUnusedMovements(cr)
        #displayAllInvestments(cr)

    @staticmethod
    def main(args):
        with psycopg2.connect(**dbconfig.psycopg) as db:
            with db.cursor() as cr:
                psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, cr)
                with transaction(cr, discarded='--doit' not in args):
                    m = Migrator(cr)
                    m.doSteps()

Migrator.main(sys.argv)

# vim: et ts=4 sw=4
