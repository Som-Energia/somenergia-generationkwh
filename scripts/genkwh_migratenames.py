#!/usr/bin/env python
# -*- coding: utf8 -*-


import configdb
import psycopg2
import dbutils
import contextlib
from yamlns import namespace as ns
from consolemsg import step, warn, success, error as consoleError, fail
import sys
import generationkwh.investmentmodel as gkwh

errorCases = ns()

def error(message, **params):
    msg = message.format(**params)
    consoleError(msg)
    errorCases.setdefault(ns(params).partner_id, []).append(msg)

@contextlib.contextmanager
def transaction(cursor, discarded=False):
    cursor.execute('begin')
    try:
        yield cursor
    except:
        cursor.execute('rollback')
        raise
    else:
        cursor.execute('rollback' if discarded else 'commit')

def fixInvestmentMovelines(cr, investmentMovelinePairs):
    for investment, moveline in investmentMovelinePairs:
        success("   Fixing inv {investment} -> mov {moveline}".format(
            **locals()))
        cr.execute("""
            UPDATE
                generationkwh_investment as inv
            SET
                move_line_id = %(moveline)s
            WHERE
                id = %(investment)s
        """, dict(
            moveline=moveline,
            investment=investment
        ))

def ungeneratedInvestments(cr):
    cr.execute("""\
        select
            ml.*,
            acc.name
        from
            account_move_line as ml
        left join
            account_account as acc
        on
            acc.id = ml.account_id
        left outer join
            generationkwh_investment as inv
        on
            ml.id = inv.move_line_id
        left join
            account_period as p
        on
            p.id = ml.period_id
        where
            acc.code like '1635%%' and
            not p.special and
            inv.id is NULL
        """)
    return dbutils.nsList(cr)
        

def activeNegativeInvestments(cr):
    cr.execute("""\
        select
            *
        from
            generationkwh_investment as inv
        left join
            somenergia_soci as soc
        on
            inv.member_id = soc.id
        left join
            res_partner as p
        on
            soc.partner_id = p.id
        where
            inv.nshares < 1 and
            inv.active and
            true
        """)
    return dbutils.nsList(cr)

def moveLinesReferencedTwice(cr):
    cr.execute("""\
        select
            p.id as partner_id,
            inv.id as investment_id,
            inv.move_line_id as moveline_id,
            p.name as partner_name,
            acc.name as account_name,
            p.ref as partner_code,
            acc.code as account_code,
            nshares as amount,
            true
        from
            generationkwh_investment as inv
        left join
            somenergia_soci as soc
        on
            inv.member_id = soc.id
        left join
            res_partner as p
        on
            soc.partner_id = p.id
        left join
            account_move_line as ml
        on
            ml.id = inv.move_line_id
        left join
            account_account as acc
        on
            acc.id = ml.account_id
        where inv.move_line_id in (
            select
                inv.move_line_id as id
            from
                generationkwh_investment as inv
            group by
                inv.move_line_id
            having
                count(id) > 1
            )
        """)
    return dbutils.nsList(cr)

def investmentPointingSomeoneElsesAccount(cr):
    cr.execute("""\
        select
            p.id as partner_id,
            inv.id as investment_id,
            inv.move_line_id as moveline_id,
            p.name as partner_name,
            acc.name as account_name,
            p.ref as partner_code,
            acc.code as account_code,
            nshares as amount,
            true
        from
            generationkwh_investment as inv
        left join
            somenergia_soci as soc
        on
            inv.member_id = soc.id
        left join
            res_partner as p
        on
            soc.partner_id = p.id
        left join
            account_move_line as ml
        on
            ml.id = inv.move_line_id
        left join
            account_account as acc
        on
            acc.id = ml.account_id
        where 
            acc.code <> '1635' || right('000'||right(p.ref,-1),8)
        """)
    return dbutils.nsList(cr)


def movementsVsInvesmentAmounts(cr):
    cr.execute("""\
        select
            accounting.account_code as accounting_account,
            investment.account_code as investment_account,
            investment.partner_id as investment_partner_id,
            accounting.amount as accounting_amount,
            investment.amount as investment_amount,
            partner_name,
            partner_id,
            true
        from (
            select
                sum(ml.credit-ml.debit) as amount,
                ac.code as account_code,
                true
            from
                account_move_line as ml
            left join
                account_account as ac
            on
                ac.id = ml.account_id
            where
                ac.code ilike '1635%%' and
                true
            group by
                ac.code
            ) as accounting	
        left outer join (
            select
                '1635' || right('000'||right(partner.ref,-1),8) as account_code,
                partner.name as partner_name,
                partner.id as partner_id,
                sum(inv.nshares)*100.00 as amount,
                true
            from
                generationkwh_investment as inv
            left join
                somenergia_soci as member
            on
                inv.member_id = member.id
            left join
                res_partner as partner
            on
                member.partner_id = partner.id
            where
                inv.active=True and
                (inv.last_effective_date is NULL or inv.last_effective_date > now()) and
                true
            group by
                partner.id,
                partner.ref,
                partner.name
            ) as investment
        on
            accounting.account_code = investment.account_code
        where
            investment.amount - accounting.amount <> 0
        order by
            accounting.account_code
    """, dict(shareValue=gkwh.shareValue))
    return dbutils.nsList(cr)


def activeInvestmentRelatedToFiscalEndYear(cr):
    """Returns the list of active investment related to
    movelines of a fiscal closure.
    Investments of such movelines should be disabled."""
    query = """\
        select
            inv.id as id
        from
            generationkwh_investment as inv
        left join
            account_move_line as ml
        on
            inv.move_line_id = ml.id
        left join
            account_period as p
        on
            p.id = ml.period_id
        where
            p.special and
            inv.active
        """
    cr.execute(query)

def deleteInactiveInvestmentRelatedToFiscalEndYear(cr):
    query = """\
        delete
        from generationkwh_investment
        where id in (
            select
                inv.id as id
            from
                generationkwh_investment as inv
            left join
                account_move_line as ml
            on
                inv.move_line_id = ml.id
            left join
                account_period as p
            on
                p.id = ml.period_id
            where
                p.special and
                not inv.active
            )
        """
    cr.execute(query)

def getGenerationMovelinesByPartner(cr, partner_id):
    cr.execute("""\
        select
            p.*
        from
            res_partner as p
        where
            p.id = %(partner_id)s
        order by p.id
    """, dict(
        partner_id=partner_id,
    ))
    partner = dbutils.nsList(cr)[0]
    partner.account = '1635{:08}'.format(int(partner.ref[1:]))
    cr.execute("""\
        select
            %(partner_name)s as partner_name,
            ml.*,
            false
        from
            account_move_line as ml
        left join
            account_period as period
        on
            period.id = ml.period_id
        left join
            account_account as a
        on
            ml.account_id=a.id
        where
            a.code = %(account)s and
            not period.special and
            true
        order by ml.id
    """, dict(
        partner_id = partner_id,
        partner_name = partner.name,
        account = partner.account,
    ))
    return dbutils.nsList(cr)

def getInvestmentsByPartner(cr, partner_id):
    cr.execute("""\
        select
            p.*
        from
            res_partner as p
        where
            p.id = %(partner_id)s
        order by p.id
    """, dict(
        partner_id=partner_id,
    ))
    partner = dbutils.nsList(cr)[0]
    cr.execute("""\
        select
            %(partner_name)s as partner_name,
            inv.*,
            false
        from
            generationkwh_investment as inv
        left join
            somenergia_soci as member
        on
            member.id = inv.member_id
        where
            member.partner_id = %(partner_id)s and
            true
        order by inv.id
    """, dict(
        partner_id = partner_id,
        partner_name = partner.name,
    ))
    return dbutils.nsList(cr)


def getOrderLines(cr, order_id):
    cr.execute("""\
        select
            pl.*,
            po.date_done as order_sent_date,
            p.name as partner_name,
            false
        from
            payment_line as pl
        left join
            payment_order as po
        on
            po.id = pl.order_id
        left join
            res_partner as p
        on
           p.id = pl.partner_id
        where
            pl.order_id = %(order_id)s
        order by pl.id
    """, dict(
        order_id=order_id,
    ))
    return dbutils.nsList(cr)

def getMoveLines(cr, move_id):
    cr.execute("""\
        select
            ml.*,
            p.name as partner_name
        from
            account_move_line as ml
        left join
            account_account as ac
        on ac.id = ml.account_id
        left join
            res_partner as p
        on
           p.id = ml.partner_id
        where
            ac.code ilike '1635%%' and
            ml.move_id = %(move_id)s
        order by ml.id
    """, dict(
        move_id=move_id,
    ))
    return dbutils.nsList(cr)

def getActiveInvestments(cr):
    cr.execute("""\
        select
            inv.*,
            ml.name as mlname,
            ml.date_created as move_date_created,
            soci.partner_id,
            p.name as partner_name
        from
            generationkwh_investment as inv
        left join
            account_move_line as ml
        on
            inv.move_line_id = ml.id
        left join
            somenergia_soci as soci
        on
            soci.id = inv.member_id
        left join
            res_partner as p
        on
            p.id = soci.partner_id
        where
            inv.active and
            true
        order by inv.id
    """, dict(
    ))
    return dbutils.nsList(cr)


def lastInvestment(cr):
    cr.execute("""\
        select
            max(move_line_id)
        from
            generationkwh_investment as inv
        where
            inv.active and
            true
    """, dict(
    ))
    return dbutils.nsList(cr)[0].max


def investmentOrderAndMovements(cr, modeName='GENERATION kWh'):
    cr.execute("""\
        select
            o.id as order_id,
            m.move_id as move_id,
            o.n_lines as order_nlines,
            m.nlines as move_nlines,
            o.date_done as order_sent_date,
            m.date_created as move_create_date
        from
        (
            select
                po.id,
                po.n_lines,
                po.date_done,
                true
            from
                payment_order as po
            left join
                payment_mode as pm
            on
                pm.id = po.mode
            where
                pm.name = 'GENERATION kWh' or
                po.id = 1389 or -- has mode 'ENGINYERS'
                false
        ) as o
        full outer join (
            select
                l.move_id,
                count(l.id) as nlines,
                l.date_created
            from
                account_move_line as l
            left join
                account_account as a
            on
                l.account_id=a.id
            where
                a.code ilike '1635%%' and
                l.name = '/' and
                true
            group by
                move_id,
                l.date_created
            order by
                l.date_created
        ) as m
            on o.date_done = m.date_created
        order by
            m.date_created
        ;
        """)
    return dbutils.nsList(cr)


def appendToKey(d, key, value):
    values = d.get(key, [])
    wasEmpty = bool(values)
    values.append(value)
    d[key] = values
    return wasEmpty

def getAndRemoveFirst(d, key):
    values = d.get(key, [])
    if not values: return None
    return values.pop(0)

def bindMoveLineAndPaymentLine(moveline, orderline):
    True and success(
        "Match ml-po ml-{moveline.id} {orderline.name} {orderline.create_date} {amount:=8}€ {moveline.partner_name}"
        .format(**ns(
            moveline=moveline,
            orderline=orderline,
            amount = moveline.credit-moveline.debit,
            )))
    paymentMoveLines[moveline.id] = ns(
        ref=orderline.name,
        order_date=orderline.create_date,
        partner_id = orderline.partner_id,
        partner_name = orderline.partner_name,
        amount = moveline.credit-moveline.debit,
        )

def bindInvestmentWithOrder(cr, investment, moveline):
    True and success(
        "Match inv-od {investment.id} {moveline.ref} {moveline.order_date} {amount:=8}€ {moveline.partner_name}"
        .format(**ns(
            investment=investment,
            moveline=moveline,
            amount=investment.nshares*gkwh.shareValue,
            )))
    cr.execute("""\
        UPDATE generationkwh_investment as inv
        SET
            name = %(name)s,
            order_date = %(order_date)s
        WHERE
            inv.id = %(id)s
        """, dict(
            id = investment.id,
            order_date = moveline.order_date,
            name = moveline.ref,
        ))

def displayPartnersMovements(cr, partner_id):
    movelines = getGenerationMovelinesByPartner(cr,partner_id)
    for m in movelines:
        m.amount = m.credit -m.debit
        error("    mov {date_created} {id} {partner_name} {amount} {name}",
            **m)
    investments = getInvestmentsByPartner(cr, partner_id)
    for inv in investments:
        inv.amount = inv.nshares*gkwh.shareValue
        inv.active = 'y' if inv.active else 'n'
        error("    inv {active} {order_date_or_not} {purchase_date_or_not} {first_effective_date_or_not} {last_effective_date_or_not} {id} {partner_name} {amount} {name}",
            partner_id = partner_id,
            order_date_or_not = inv.order_date or '____-__-__',
            purchase_date_or_not = inv.purchase_date or '____-__-__',
            first_effective_date_or_not = inv.first_effective_date or '____-__-__',
            last_effective_date_or_not = inv.last_effective_date or '____-__-__',
            **inv)

def main(cr):
    global paymentMoveLines
    step("Clean up cases")

    step(" Fiscal end year movements")
    fiscalEndYearInvestments = activeInvestmentRelatedToFiscalEndYear(cr)
    if fiscalEndYearInvestments:
        fail("There are active investments which are related to fiscal end year")
    deleteInactiveInvestmentRelatedToFiscalEndYear(cr)

    step(" Fixing known bad investment-movelines relations")
    fixInvestmentMovelines(cr, cases.investmentMovelinesToFix.items())

    step(" Fixing known bad investment shares")
    for invid, nshares in cases.investmentSharesToFix.items():
        step("  Fixing {} to be {}".format(invid, nshares))
        cr.execute("UPDATE generationkwh_investment SET nshares=%s WHERE id=%s",
            (nshares, invid))

    # Generate here the pending investments
    step(" Checking for ungenerated investments")
    ungenerated = ungeneratedInvestments(cr)
    if ungenerated:
        for inv in ungenerated:
            success(inv.dump())
        fail("You should generate remaining investment from accounting at this point.")

    step(" Compensating negative investments")
    for mlid in cases.investmentsToDeactivateByMoveline:
        cr.execute("""\
            UPDATE generationkwh_investment
            SET
                active=false,
                first_effective_date=NULL
            WHERE move_line_id=%(mlid)s
            """, dict(mlid=mlid))

    step(" Compensating pending negative investments already efective")
    for case in cases.lateDisinvestments:
        cr.execute("""\
            UPDATE generationkwh_investment
            SET
                active=false
            WHERE move_line_id=%(negative)s
            ;
            UPDATE generationkwh_investment
            SET
                last_effective_date = %(date)s
            WHERE
                move_line_id = %(positive)s
            """,case)

    step(" Detecting remaining negative investments")
    negativeInvestments = activeNegativeInvestments(cr)
    for inv in negativeInvestments:
        displayPartnersMovements(cr, inv.partner_id)

    if False and negativeInvestments:
        fail("No puc avançar si hi ha aquests errors")


    step(" Investments pointing to someone else's account")
    squatters = investmentPointingSomeoneElsesAccount(cr)
    if squatters:
        for squat in squatters:
            error("Investment {investment_id} -> {moveline_id}, {partner_code} {partner_name} -> {account_code} {account_name} {amount}",
                **squat)
            displayPartnersMovements(cr, squat.partner_id)
    

    step(" Multiple referenced movements")
    referencedTwice = moveLinesReferencedTwice(cr)
    if referencedTwice:
        for reference in referencedTwice:
            error("Investment {investment_id} -> {moveline_id}, {partner_code} {partner_name} -> {account_code} {account_name} {amount}",
                **reference)
            displayPartnersMovements(cr, reference.partner_id)

    if squatters or referencedTwice:       
        fail("No puc avançar si hi ha aquests errors")



    # Movelines related to payment orders
    paymentMoveLines = ns()

    step("Emparellant moviments amb remeses")

    for data in investmentOrderAndMovements(cr):
        step("Quadrant remesa feta el {move_create_date}".format(**data))


        step(" Emparellant les linies del moviment amb les de la remesa")

        if not data.move_id:
            warn("Remesa sense moviment. {}: Id {}, amb {} linies" .format(
                data.order_sent_date or "not yet",
                data.order_id,
                data.order_nlines,
                ))
            continue
        if not data.order_id:
            warn("Moviment sense remesa. {}: Id {}, amb {} linies".format(
                data.move_create_date or "sense data",
                data.move_id,
                data.move_nlines,
                ))
            continue
        if data.move_nlines != data.order_nlines:
            warn("{}: Different number of lines. Payment order {}, Movement {}".format(
                data.move_create_date,
                data.order_nlines,
                data.move_nlines,
                ))

        orderLines = getOrderLines(cr, data.order_id)
        moveLines = getMoveLines(cr, data.move_id)

        if len(orderLines) != data.order_nlines:
            warn("Got different number of lines {} than reported {} in Order"
                .format(len(orderLines), data.order_nlines))

        if len(moveLines) != data.move_nlines:
            warn("Got different number of lines {} than reported {} in Move"
                .format(len(orderLines), data.order_nlines))


        step(" Matching order lines and move lines by partner, amount and order")
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

        step(" Matching missed order lines just by partner")

        #step("  Create a partner -> unpaired movelines map")
        movelinesByPartnerId = {}
        for moveline in repesca:
            appendToKey(movelinesByPartnerId, moveline.partner_id, moveline)

        #step("  Lookup for each unpaired order")
        for key, options in orderLinesDict.items():
            for orderline in options:
                moveline = getAndRemoveFirst(movelinesByPartnerId, orderline.partner_id)
                if not moveline:
                    error(
                        "Linia de Remesa sense parella: "
                        "{name} id {id} {order_sent_date} {amount}€ {partner_name}",
                        **orderline)
                    print key
                    continue
                bindMoveLineAndPaymentLine(moveline, orderline)
                warn(
                    "Amount missmatch {orderline.name} "
                    "order {orderline.amount}€ move {moveline.credit}"
                    .format(**ns(
                        orderline=orderline,
                        moveline=moveline,
                    )))
                displayPartnersMovements(cr, orderline.partner_id)

        for partner_id, movelines in movelinesByPartnerId.items():
            for moveline in movelines:
                error(
                    "Linia de Moviment sense parella "
                    "id {id} {create_date} {credit}€ {partner_name}",
                    **moveline)

    step("Pairing investments")
    step(" Pairing investments using existing relation")

    investments = getActiveInvestments(cr)

    unmatchedMoveLines = list(paymentMoveLines.keys())
    unmatchedInvestments = []

    for inv in investments:
        moveline_id = inv.move_line_id

        if moveline_id not in paymentMoveLines.keys():
            warn("Moveline {move_line_id} refered by inv {id} not in a payment order: "
                "partner {partner_name} {nshares}00€ '{mlname}'"
                .format(**inv))
            #warn(inv.dump())
            unmatchedInvestments.append(inv.id)
            continue
        related_moveline = paymentMoveLines[moveline_id]
        if related_moveline.partner_id != inv.partner_id:
            error("Moveline partner missmatch inv {partner_name} mov {mov_partner} {move_line_id} {nshares}00€ {mlname}",
                mov_partner=related_moveline.partner_name,
                **inv
                )
            displayPartnersMovements(cr, inv.partner_id)
            displayPartnersMovements(cr, related_moveline.partner_id)
            unmatchedInvestments.append(inv.id)
            continue
        if related_moveline.amount != inv.nshares*gkwh.shareValue:
            warn("Amount missmatch {partner_name} inv {nshares}00€ mov {mov_amount}€ {mlname}"
                .format(
                    mov_amount=related_moveline.amount,
                    **inv))
            displayPartnersMovements(cr, inv.partner_id)
        bindInvestmentWithOrder(cr, inv, paymentMoveLines[moveline_id])
        if moveline_id not in  unmatchedMoveLines:
            error("Move line referenced twice {move_line_id} {partner_name}", **inv)
            displayPartnersMovements(cr, inv.partner_id)
        else:
            unmatchedMoveLines.remove(moveline_id)


    lastGeneratedMoveLine = lastInvestment(cr)
    ungenerated = [
        line_id
        for line_id in unmatchedMoveLines
        if line_id > lastGeneratedMoveLine
    ]

    unmatchedMoveLines = [
        line_id
        for line_id in unmatchedMoveLines
        if line_id <= lastGeneratedMoveLine
    ]

    step("Retry match investments just by partner")
    orphanMoveLinesByPartner = {}

    for moveline_id in unmatchedMoveLines:
        moveline = paymentMoveLines[moveline_id]

        wasEmpty = appendToKey(orphanMoveLinesByPartner, moveline.partner_id, moveline)
        if wasEmpty:
            warn("partner with two pending movements id {id} {partner_name}".format(id=moveline_id, **moveline))

    for inv in investments:
        if inv.id not in unmatchedInvestments:
            continue

        partner_id = inv.partner_id
        solution = getAndRemoveFirst(orphanMoveLinesByPartner, partner_id)
        if not solution:
            error("No name for Investment {move_date_created} {move_line_id} {nshares:=5}00.00€ {partner_name}",**inv)
            displayPartnersMovements(cr, inv.partner_id)
            continue
        bindInvestmentWithOrder(cr, inv, solution)

    for orphanNames in orphanMoveLinesByPartner.values():
        for orphanName in orphanNames:
            error("Unassigned name {ref} {order_date} {partner_name}",
                **orphanName)
            displayPartnersMovements(cr, orphanName.partner_id)


    for moveline_id in ungenerated:
        moveline = paymentMoveLines[moveline_id]
        warn("Not yet generated investment {ref} {order_date} {partner_name}".format(**moveline))
        
    for missmatch in movementsVsInvesmentAmounts(cr):
        error("Balance missmatch: "
            "Accounting {accounting_amount} "
            "Investment {investment_amount} "
            "{partner_name}",
            **missmatch)

        displayPartnersMovements(cr, missmatch.investment_partner_id)


#import erppeek_wst
#client = erppeek_wst.ClientWST(**configdb.erppeek)
#client.begin()
#client.rollback()

cases = ns.load('migration.yaml')

with psycopg2.connect(**configdb.psycopg) as db:
    with db.cursor() as cr:
        with transaction(cr, discarded='--doit' not in sys.argv):
            main(cr)


# vim: et ts=4 sw=4
