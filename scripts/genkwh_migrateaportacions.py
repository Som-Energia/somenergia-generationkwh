#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import unicode_literals

import sys
import psycopg2
from yamlns import namespace as ns
import dbconfig
import dbutils
import genkwh_migratenames
from genkwh_migratenames import (
    transaction,
    getOrderLines,
    getMoveLines,
)
from generationkwh.investmentstate import InvestmentState, AportacionsState
from io import open
from tqdm import tqdm as old_tqdm
#def tqdm(x): return x
def tqdm(x):
    return old_tqdm(x, file=open('/dev/tty', 'w', encoding='utf8'), ascii=False)

from pathlib2 import Path
import re
from consolemsg import out, step, success, warn, error, u


class Migrator:
    def __init__(self, cr):
        self.cases = genkwh_migratenames.cases = ns.load('migration-aportacions.yaml')
        self.cr = cr
        self.unmatchedOrderLines = {}

    def cleanUp(self):
        """Clean up inconsistencies in cases so that the rest of
        the migrations goes on painfully
        """
        step("Clean up cases")
        # TODO

    def getAllInvestments(self):
        emission = self.cases.get('emissionType', 'genkwh')
        cachefile = Path('cached-investments-{}.yaml'.format(emission))
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

    def getInvestmentPaymentOrders(self):
        paymentModes = self.cases.get('formPaymentModes', ['GENERATION kWh'])
        extraPaymentOrders=self.cases.get('extraPaymentOrders', [])
        excludedOrders=self.cases.get('excludedOrders', [])
        self.cr.execute("""\
            select
                po.id as order_id,
                po.n_lines as order_nlines,
                po.date_done as order_sent_date,
                true as ignored
            from
                payment_order as po
            left join
                payment_mode as pm
            on
                pm.id = po.mode
            where
                (
                    pm.name = ANY(%(paymentModes)s) or
                    po.id = ANY(%(extraPaymentOrders)s) or
                    false
                ) and
                po.id != ALL(%(excludedOrders)s) and
                true
            order by
                po.date_done,
                po.n_lines
            ;
            """, dict(
                paymentModes=paymentModes,
                excludedOrders=excludedOrders,
                extraPaymentOrders=extraPaymentOrders,
            ))
        return dbutils.nsList(self.cr)

    def getInvestmentPaymentMovement(self):
        """
            Returns movelines containing payments for investment payment orders.
            They are identified by having lines against investment accounts
            and having '/' as the name, because that's the name a payment order uses.
        """
        parentAccount = self.cases.get('parentAccount', '1635')
        self.cr.execute("""\
            select
                l.move_id as move_id,
                count(l.id) as move_nlines,
                l.date_created as move_create_date
            from
                account_move_line as l
            left join
                account_account as a
            on
                l.account_id=a.id
            left join
                account_account as pa
            on
                pa.id = a.parent_id
            where
                pa.code = %(parentAccount)s and
                l.name = '/' and
                true
            group by
                move_id,
                date_created
            order by
                move_create_date,
                move_nlines
            ;
            """, dict(
                parentAccount=parentAccount,
            ))
        return dbutils.nsList(self.cr)


    def getAllMovementsLines(self):
        cachingEnabled = False
        parentAccount = self.cases.get('parentAccount', '1635')
        cachefile = Path('apos_movementlines-{}.yaml'.format(parentAccount))
        if cachingEnabled and cachefile.exists():
            out("loading from cache {}".format(cachefile))
            return ns.load(str(cachefile)).data
        self.cr.execute("""\
            select distinct
                ml.id,
                ml.move_id,
                ml.name as name,
                ml.date_created as date_created,
                ml.create_date as create_date,
                ml.credit,
                ml.debit,
                --NULL no partner
                -- 1 SomEnergia
                -- 39060 Caja Laboral
                CASE WHEN COALESCE(moveline_partner.id,1) IN (1,39060)
                    THEN account_partner.ref
                    ELSE moveline_partner.ref
                    END AS partner_ref,
                CASE WHEN COALESCE(moveline_partner.id,1) IN (1,39060)
                    THEN account_partner.id
                    ELSE moveline_partner.id
                    END AS partner_id,
                CASE WHEN COALESCE(moveline_partner.id,1) IN (1,39060)
                    THEN account_partner.name
                    ELSE moveline_partner.name
                    END AS partner_name,
                ml.credit-ml.debit as amount,
                account.name as account_name,
                account.code as account_code,
                COALESCE(usr.name, 'Nobody') as username,
                -- account_partner.id as account_partner_id,
                -- moveline_partner.id as moveline_partner_id,
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
        if cachingEnabled:
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

    def loadInvestments(self):
        step("Loading all investments")
        self.investments = {
            investment.name: investment
            for investment in self.getAllInvestments()
        }

    def loadMovements(self):
        step("Loading all movelines")
        movelines = self.getAllMovementsLines()

        self.movelines = {
            movement.id: movement
            for movement in movelines
        }
        self.movelinesByPartner = {}
        for movement in movelines:
            self.movelinesByPartner.setdefault(movement.partner_id, []).append(movement)

    def dumpMovementsByPartner(self):
        with Path('apos_movementlines.csv').open('w', encoding='utf8') as output:
            for partner_id in sorted(self.movelinesByPartner):
                movelines = self.movelinesByPartner[partner_id]
                output.write("({partner_id}) {partner_ref} {partner_name}\n".format(**movelines[0]))
                for movement in movelines:
                    output.write("\t{account_code}\t{date_created}\t{credit: 10f}\t{debit: 10f}\t{id: 10d}\t{name}\n".format(**movement))
                    if 'solution' in movement:
                        names = (
                            movement.solution.names
                            if 'names' in movement.solution
                            else [movement.solution.name]
                        )
                        for name in names:
                            output.write("\t\t{investment}\t{type}\t{solution}\n".format(solution=movement.solution, investment=name, **movement.solution))

    def dumpUnsolved(self):
        with Path('unsolved.yaml').open('w', encoding='utf8') as output:
            output.write("unsolved:\n")
            for partner_id in sorted(self.movelinesByPartner):
                movelines = self.movelinesByPartner[partner_id]
                if all('solution' in movement for movement in movelines):
                    continue # all solved
                investments = list(sorted(set(
                    movement.solution.name
                    for movement in movelines
                    if 'solution' in movement
                    and 'name' in movement.solution
                )))
                for investment in investments:
                    output.write(
                        "  {0}: # {1.partner_ref} {1.partner_name}\n"
                            .format(investment, movelines[0]))
                    for movement in movelines:
                        if 'solution' not in movement: continue
                        if 'name' in movement.solution:
                            if movement.solution.name != investment: continue
                        else: # names
                            if investment not in movement.solution.names: continue
                        output.write("    {id}: {solution.type} # {date_created} ({partner_name}) {amount} {name}\n".format(**movement))
                output.write(
                    "#  unsolved: # {partner_ref} {partner_name}\n"
                        .format(**movelines[0]))
                for movement in movelines:
                    if 'solution' in movement: continue
                    output.write("#    {id}: unknown # {date_created} ({partner_name}) {amount} {name}\n".format(**movement))
                output.write("\n")

    def organize(self, items, key):
        result = ns()
        for item in items:
            result.setdefault(key(item), []).append(item)
        return result

    def takeFirst(self, pool, key):
        values = pool.get(key, [])
        if not values: return None
        return values.pop(0)
        

    def orderLineIP(self, orderline):
        communication = orderline.communication2
        if communication and ' IP ' in communication:
            return communication.split(" IP ")[1]
        return '0.0.0.0'

    def bindMoveLineAndPaymentLine(self, moveline, orderline):
        """Function to be called when a payment has been matched"""

        ip = self.orderLineIP(orderline)
        moveline.partner_name = moveline.partner_name and u(moveline.partner_name)
        False and success(
            u"Match ml-po ml-{moveline.id} {orderline.name} {orderline.create_date} {amount:=8}€ {moveline.partner_name} {ip}"
            .format(
                moveline=moveline,
                orderline=orderline,
                amount = moveline.credit-moveline.debit,
                ip = ip,
            ))
        investment_name = orderline.name
        if investment_name in self.cases.renamedInvestments:
            investment_name = self.cases.renamedInvestments[investment_name]
            warn("Renaming orderline {} as {}", orderline.name, investment_name)

        if self.movelines[moveline.id].get('solution') is not None:
            warn("Binding twice ml {}, was ol {}, now ol {}",
                moveline.id, self.movelines[moveline.id].solution, orderline)
            
        self.paymentMoveLines[moveline.id] = ns(
            movelineid = moveline.id,
            ref = investment_name,
            order_date=orderline.create_date,
            partner_id = orderline.partner_id,
            partner_name = orderline.partner_name,
            member_id = orderline.member_id,
            amount = moveline.credit-moveline.debit,
            ip = ip,
            )
        self.movelines[moveline.id].update(
            solution = ns(
                type = 'paid',
                name = investment_name,
                orderline_id = orderline.id,
                iban = orderline.iban,
                order_date=orderline.create_date,
                member_id = orderline.member_id,
                partner_name = orderline.partner_name,
                amount = moveline.credit-moveline.debit,
                ip = ip,
            )
        )

    def matchPaymentOrders(self):
        """
        As old investment information is bound to the payment order
        (name, order date, ip...), relate them to move lines.
        This function identifies first payments move lines with their order.
        Binds payment order lines (having order data such as name and dates)
        with the movement line first matching lines from date-size matching
        orders and movements and within, matching parther-amount lines.
        Unmatched blocks fallback matching just by date, and unmatched
        lines fallback matching just by partner.
        """

        def update(d, **kwds):
            d.update(**kwds)
            return d

        self.paymentMoveLines = ns()

        step("Loading payment related movelines")
        paymentMoves = self.getInvestmentPaymentMovement()

        paymentMoves_byDateLines = self.organize(paymentMoves,
            lambda m: (m.move_create_date, m.move_nlines))
        paymentMoves_byDateLines.dump("moves_byDateLine.yaml")

        step("Loading payment related movements lines")
        pendingMovelines = [
            update(line,
                move_id = move.move_id,
                create_date = move.move_create_date,
                move_nlines = move.move_nlines,
            )
            for move in tqdm(paymentMoves)
            for line in getMoveLines(self.cr, move.move_id)
        ]

        step("Loading payment related orders")
        paymentOrders = self.getInvestmentPaymentOrders()

        paymentOrders_byDateLine = self.organize(paymentOrders,
            lambda o: (o.order_sent_date, o.order_nlines))
        paymentOrders_byDateLine.dump("orders_byDateLine.yaml")

        step("Loading payment related order lines")
        pendingOrderlines = [
            update(line,
                order_id = order.order_id,
                order_sent_date = order.order_sent_date,
                order_nlines = order.order_nlines,
            )
            for order in tqdm(paymentOrders)
            for line in getOrderLines(self.cr, order.order_id)
        ]

        def matchBy(orderlines, movelines, orderkey, movementkey):
            orderlineDict = self.organize(orderlines, orderkey)
            out(">> {}", len(movelines))
            pendingMovelines = []
            for moveline in tqdm(movelines):
                key = movementkey(moveline)
                orderline = self.takeFirst(orderlineDict,key)
                if not orderline:
                    pendingMovelines.append(moveline)
                    continue
                # Found
                self.bindMoveLineAndPaymentLine(moveline, orderline)

            pendingOrderlines = sum(orderlineDict.values(), [])
            return pendingOrderlines, pendingMovelines

        def matchExplicit(orderlines, movelines):
            explicitOrderlineToMoveLine = {
                ol : ml
                for ml, ol in self.cases.movelineToOrderline.items()
                }
            movelinesById = {
                ml.id : ml
                for ml in movelines
            }
            pendingOrderlines = []
            for orderline in orderlines:
                moveline_id = explicitOrderlineToMoveLine.pop(orderline.id,None)
                if not moveline_id:
                    pendingOrderlines.append(orderline)
                    continue
                moveline = movelinesById.pop(moveline_id, None)
                if not moveline: # el moveline no tenia la "/"
                    moveline = self.movelines[moveline_id]
                    warn(
                        "Explicit moveline to orderline: {ol.order_sent_date} {ol.amount} {ol.partner_name}",
                        ml=moveline,
                        ol=orderline,
                    )
                if (
                    orderline.order_sent_date,
                    -orderline.amount,
                    orderline.partner_id,
                ) != (
                    moveline.date_created,
                    moveline.credit,
                    moveline.partner_id,
                ):
                    warn("Explicit moveline to orderline with missmatching info:\n"
                        "\torderline moveline\n"
                        "\t{ol.order_sent_date} {ml.date_created}\n"
                        "\t{orderamount} {ml.credit}\n"
                        "\t{ol.partner_name} {ml.partner_name}",
                        ol=orderline,
                        ml=moveline,
                        orderamount=-orderline.amount,
                    )

                self.bindMoveLineAndPaymentLine(moveline, orderline)

            for orderline_id in explicitOrderlineToMoveLine:
                error("Not a pending order {}", orderline_id)

            return pendingOrderlines, movelinesById.values()

        warn("Pending: orderlines: {} movelines: {}", len(pendingOrderlines), len(pendingMovelines))
        step("  Matching by date, nlines, amount, partner")
        pendingOrderlines, pendingMovelines = matchBy(pendingOrderlines, pendingMovelines,
            lambda ol: (
                ol.order_sent_date,
                ol.order_nlines,
                -ol.amount,
                ol.partner_id,
            ),
            lambda ml: (
                ml.create_date,
                ml.move_nlines,
                ml.credit,
                ml.partner_id,
            ),
        )
        warn("Pending: orderlines: {} movelines: {}", len(pendingOrderlines), len(pendingMovelines))
        step("  Matching by date, amount, partner")
        pendingOrderlines, pendingMovelines = matchBy(pendingOrderlines, pendingMovelines,
            lambda ol: (
                ol.order_sent_date,
                -ol.amount,
                ol.partner_id,
            ),
            lambda ml: (
                ml.create_date,
                ml.credit,
                ml.partner_id,
            ),
        )
        warn("Pending: orderlines: {} movelines: {}", len(pendingOrderlines), len(pendingMovelines))
        step("  Matching explicit pairs from yaml")
        pendingOrderlines, pendingMovelines = matchExplicit(pendingOrderlines, pendingMovelines)

        warn("Pending: orderlines: {} movelines: {}", len(pendingOrderlines), len(pendingMovelines))
        self.pendingOrderlines = pendingOrderlines
        self.pendingMovelines = pendingMovelines

        step("  Matching non-legacy investments")
        self.solveExistingInvestments()
        warn("Pending: orderlines: {} movelines: {}", len(self.pendingOrderlines), len(self.pendingMovelines))

        for orderline in self.pendingOrderlines:
            error(
                "Linia de Remesa sense apunt: "
                "{name} id {id} {order_sent_date} {amount}€ {partner_name} \"{communication}\"",
                **orderline)
        for moveline in self.pendingMovelines:
            error(
                "Apunt sense linea de remesa: "
                "id {id} {create_date} {credit}€ {partner_name}",
                **moveline)

    def solveExistingInvestments(self):
        step("Solving movelines referring existing Invesments")
        pendingInvestments = set(self.investments.keys())

        pendingOrderlines = {
            orderline.communication[:9]: orderline
            for orderline in self.pendingOrderlines
        }

        pendingMovelines = {
            moveline.id: moveline
            for moveline in self.pendingMovelines
        }

        for moveline_id, moveline in self.movelines.items():
            if not (
                moveline.name.startswith("Inversió APO00") or
                moveline.name.startswith("Inversión APO00")
            ): continue
            investment_name = moveline.name.split()[1]
            orderline = pendingOrderlines.pop(investment_name, None)
            if not orderline:
                warn("Inversio sense línia de remesa: {}", investment_name)
            pendingMovelines.pop(moveline_id,None)

            if investment_name not in pendingInvestments:
                warn("APO movement {} refers to missing investment {}",
                    moveline_id,
                    investment_name,
                )
            else:
                pendingInvestments.remove(investment_name)

            if 'solution' in moveline:
                warn("Movement {} refers already solved",
                    moveline_id,
                )
                continue

            orderline.name = investment_name # New apos are not named as the investment
            self.bindMoveLineAndPaymentLine(moveline, orderline)
            moveline.solution.type='existing'

        for investment in pendingInvestments:
            error("Investment with no moveline: {name} {nshares} shares member: {member_id} {purchase_date} {first_effective_date} {last_effective_date}",
                **self.investments[investment])

        self.pendingOrderlines = pendingOrderlines.values()
        self.pendingMovelines = pendingMovelines.values()

    def processExplicitAction(self, investment_name, moveline_id, action, attributes):
        """Binds an action explicitly enumerated in the yaml file"""

        if action.type == 'corrected':
            self.logCorrected(attributes, investment_name, action)
            return

        if action.type == 'pact':
            self.logPact(attributes, investment_name, action)
            return
            
        moveline = self.movelines[moveline_id]

        #step("::: Processing {} {} {} {}", investment_name, moveline.id, moveline.partner_name, action.type)
        if investment_name == 'unsolved':
            warn("::: Unsolved {} {} {}", moveline.id, moveline.partner_name, action.type)
            return


        if action.type in ['paid', 'existing']:
            if 'solution' not in moveline:
                error("Unexpected: Payment movement without solution {ml.id} {ml.date_created} {ml.credit} {ml.partner_name}",
                    ml=self.movelines[moveline_id])
                return

            if moveline.solution.name != investment_name:
                warn("Investment name missmatch overwritting {} with yaml {} for ml {}",
                    moveline.solution.name, investment_name, moveline_id)

            self.logOrdered(attributes,
                investment_name,
                moveline.solution.iban,
                moveline.solution.amount,
                moveline.solution.order_date,
                moveline.solution.ip,
                )
            self.logMovement(attributes, investment_name, moveline_id, ns(action, type='paid'))
            return

        if action.type == 'liquidated':
            if 'solution' not in moveline:
                moveline.solution = ns(
                    action,
                    names = [investment_name],
                )
                self.liquidations[moveline_id] = -moveline.amount
            else:
                moveline.solution.names.append(investment_name)
            self.logLiquidated(attributes, investment_name, moveline_id)
            return

        if 'solution' in moveline:
            error("Moveline {} already has solution {} and receive {} from investment {}",
                moveline_id, moveline.solution, action, investment_name)

        moveline.solution = ns(
            action,
            name = investment_name,
        )
        self.logMovement(attributes, investment_name, moveline_id, action)

    def structurizeAction(self, action):
        """Converts actions just being a string with the type name
        into a full sctructured action.
        """
        try:
            action.type
            return action
        except AttributeError:
            return ns(
                type = action,
            )


    def emissionFromDate(self, investmentDate):
        for firstEmissionDate, id in reversed(sorted(self.cases.emissions.items())):
            if firstEmissionDate <= investmentDate:
                return id
        return None

    def emissionDate(self, id):
        return dict((v,k) for k,v in self.cases.emissions.items()).get(id, "NONE")
        

    def resolveAllCases(self):
        investments = ns()
        pendingExplicitCases = ns(self.cases.legacyCases)
        investment_names = sorted((m.ref, m.movelineid) for m in self.paymentMoveLines.values())
        for investment_name, payment_moveline_id in tqdm(investment_names):
            actions = pendingExplicitCases.pop(investment_name, None)
            if investment_name in investments:
                error("Overwritting {}, was {}\nWith moveline {}",
                    investment_name, u(investments[investment_name].dump()), payment_moveline_id)
            investments[investment_name] = attributes = ns()
            if not actions:
                action = self.structurizeAction(self.movelines[payment_moveline_id].solution.type)
                self.processExplicitAction(investment_name, payment_moveline_id, action, attributes)
            else:
                for moveline_id, action in actions.items():
                    action = self.structurizeAction(action)
                    self.processExplicitAction(investment_name, moveline_id, action, attributes)

            attributes.member_id = self.movelines[payment_moveline_id].solution.member_id
            attributes.emission_id = self.emissionFromDate(attributes.order_date)
            False and success("{name} {order_date} {purchase_date} {emissionDate} {partner_name}",
                partner_name = self.movelines[payment_moveline_id].solution.partner_name,
                emissionDate = self.emissionDate(attributes.emission_id),
                **attributes)

        if not pendingExplicitCases:
            success("All explicit cases resolved")
        for investment_name in pendingExplicitCases:
            warn("Unreferred pending case {}", investment_name)

        for moveline_id, balance in self.liquidations.items():
            if balance:
                warn("Liquidacio incomplerta del moviment {} queden {}€ sense compensar",
                    moveline_id, balance)

        investments.dump('result.yaml')
        return investments

    def sqlInvestmentValues(self, investment):
        nshares = investment.nominal_amount//100
        if nshares*100 != int(investment.nominal_amount):
             warn("Investment {} {!r} and {!r} differ",
                investment.name, nshares*100, int(investment.nominal_amount))
        return self.cr.mogrify(u"""\
                (
                    """ +',\n                    '.join("%("+f+")s" for f in self.fields) +"""
                )""", dict(
                nshares = nshares,
                signed_date = None,
                move_line_id = None,
                **investment
            ))

    fields = """\
        move_line_id
        first_effective_date
        nshares
        member_id
        active
        last_effective_date
        purchase_date
        actions_log
        log
        name
        draft
        order_date
        amortized_amount
        signed_date
        emission_id
        """.split()


    def applySolution(self, investments):
        ns(data = [
            ns([(k,unordered[k]) for k in self.fields])
            for unordered in (
                ns(investment,
                    id=self.investments[investment.name],
                    nshares = int(investment.nominal_amount)//100,
                    signed_date = None,
                    move_line_id = None,
                )
                for investment in investments.values()
                if investment.name in self.investments
            )
            ]).dump("regenerated-existing-investments.yaml")

        sql = u"""\
            INSERT INTO
                generationkwh_investment
                (
                    {fieldNames}
                )
            VALUES\n{rows}""".format(
                fieldNames = ',\n                    '.join(self.fields),
                rows = u",\n".join(
                    u(self.sqlInvestmentValues(investment))
                    for investment in investments.values()
                    if investment.name not in self.investments
                    )
                )
        Path('finalQuery.sql').write_text(sql, encoding='utf8')
        #self.cr.execute(sql)


    def doSteps(self):
        self.cleanUp()
        self.loadInvestments()
        self.loadMovements()
        self.matchPaymentOrders()
        investments = self.resolveAllCases()
        self.applySolution(investments)
        self.dumpMovementsByPartner()
        self.dumpUnsolved()

    def logOrdered(self, attributes, investment_name, iban, amount, order_date, ip):
        inv = InvestmentState("Webforms", order_date,
            **attributes
            )
        inv.order(
            name=investment_name,
            date=order_date.date(),
            ip=ip,
            amount=amount,
            iban=iban,
            )
        inv.invoice()
        attributes.update(inv.changed())

    def logCorrected(self, attributes, investment, what):
        inv = InvestmentState(
            "Nobody",
            what.when,
            **attributes
            )
        inv.correct(
            from_amount = what['from'],
            to_amount = what.to,
            )
        attributes.update(inv.changed())

    def logPaid(self, attributes, move_line_id):
        ml = self.movelines.get(move_line_id)
        inv = AportacionsState(ml.username, ml.create_date,
            **attributes
            )
        inv.pay(
            date=ml.create_date.date(),
            amount=ml.amount,
            move_line_id=move_line_id,
            waitDays=0, # Specific for Apos
            expirationYears=0, # Specific for Apos
            )
        attributes.update(inv.changed())

    def logUnpay(self, attributes, move_line_id):
        ml = self.movelines.get(move_line_id)
        inv = InvestmentState(ml.username, ml.create_date,
            **attributes
            )
        inv.unpay(
            amount=-ml.amount,
            move_line_id=move_line_id,
            )
        attributes.update(inv.changed())

    def logResign(self, attributes):
        # TODO: Never should be today but in order to b2b properly
        nowOrNever = datetime.datetime.now() if '--doit' in sys.argv else 'Never'
        inv = InvestmentState('Migration', nowOrNever,
            **attributes
            )
        inv.cancel()
        attributes.update(inv.changed())

    def logPartial(self, attributes, investment, move_line_id):
        ml = self.movelines.get(move_line_id)
        inv = InvestmentState(ml.username, ml.create_date,
            **attributes
            )
        inv.partial(
            amount=-ml.amount,
            move_line_id=move_line_id,
            )
        attributes.update(inv.changed())

    sold = ns() # Temporary store for sold investments
    liquidations = ns()

    def logSold(self, attributes, investment, move_line_id, what):
        ml = self.movelines.get(move_line_id)
        mlto = self.movelines.get(what.to)
        transaction_date = what.get('date', ml.create_date.date())
        newname = cases.unnamedCases[mlto.id]
        oldinv = InvestmentState(ml.username, ml.create_date,
            **attributes
            )
        newinv = InvestmentState(ml.username, ml.create_date)
        # Important: keep before emitTransfer so that
        # receiveTransfer can access original values
        newinv.receiveTransfer(
            name = newname,
            date = transaction_date,
            move_line_id = what.to,
            amount = mlto.amount,
            origin = oldinv,
            origin_partner_name = ml.partner_name,
            )
        sold[what.to] = newinv.changed()
        oldinv.emitTransfer(
            date=transaction_date,
            to_partner_name=mlto.partner_name.decode('utf-8'),
            to_name=newname,
            move_line_id=move_line_id,
            amount=-ml.amount,
            )
        attributes.update(oldinv.changed())

    def logBought(self, attributes, investment):
        attributes.update(sold.pop(investment.move_line_id))

    def logPact(self, attributes, investment, what):
        inv = InvestmentState(
            what.user.encode('utf-8'),
            what.create_date,
            **attributes
            )
        inv.pact(
            date=what.create_date,
            comment = what.note,
            **what.changes
            )
        attributes.update(inv.changed())

    def logLiquidated(self, attributes, investment, move_line_id):
        ml = self.movelines.get(move_line_id)
        inv = InvestmentState(ml.username, ml.create_date,
            **attributes
            )
        amount = attributes.paid_amount
        self.liquidations[move_line_id] -= amount
        inv.divest(
            date=ml.create_date.date(),
            amount = amount,
            move_line_id = move_line_id,
            )
        attributes.update(inv.changed())

    def logDivestment(self, attributes, investment, move_line_id):
        ml = self.movelines.get(move_line_id)
        inv = InvestmentState(ml.username, ml.create_date,
            **attributes
            )
        inv.divest(
            date=ml.create_date.date(),
            amount = -ml.amount,
            move_line_id = move_line_id,
            )
        attributes.update(inv.changed())

    def logMigrated(self, attributes):
        nowOrNever = datetime.datetime.now() if '--doit' in sys.argv else 'Never'
        inv = InvestmentState('Migration', nowOrNever,
            **attributes
            )
        inv.migrate(
            oldVersion = "1.6",
            newVersion = "2.0",
            )
        attributes.update(inv.changed())

    def logMovement(self, attributes, investment, movelineid, what):
        try:
            type = what.type
        except:
            type = what

        if type == 'corrected':
            return self.logCorrected(attributes, investment, what)
        if type == 'sold':
            return self.logSold(attributes, investment, movelineid, what)
        if type == 'pact':
            return self.logPact(attributes, investment, what)
        if type == 'paid':
            return self.logPaid(attributes, movelineid)
        if type == 'unpaid':
            return self.logUnpay(attributes, movelineid)
        if type == 'repaid':
            return self.logPaid(attributes, movelineid)
        if type == 'partial':
            return self.logPartial(attributes, investment, movelineid)
        if type == 'divested':
            return self.logDivestment(attributes, investment, movelineid)
        raise Exception(
            "T'has colat posant '{}'"
            .format(type))

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
