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
import datetime


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
    for investement_id, moveline_id in investmentMovelinePairs:
        success("   Fixing inv {investement_id} -> mov {moveline_id}".format(
            **locals()))
        cr.execute("""
            UPDATE
                generationkwh_investment as inv
            SET
                move_line_id = %(moveline_id)s
            WHERE
                id = %(investement_id)s
        """, dict(
            moveline_id=moveline_id,
            investement_id=investement_id
        ))

def ungeneratedInvestments(cr):
    "Locates any investment yet to be generated"
    cr.execute("""\
        select
            ml.*,
            acc.name as account_name
        from
            account_move_line as ml
        left join
            account_account as acc
        on
            acc.id = ml.account_id
        left join
            account_account as pacc
        on
            pacc.id = acc.parent_id
        left outer join
            generationkwh_investment as inv
        on
            ml.id = inv.move_line_id
        left join
            account_period as p
        on
            p.id = ml.period_id
        where
            pacc.code = '1635' and
            not p.special and
            inv.id is NULL
        order by
            create_date
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
            nshares*%(shareValue)s as amount,
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
        """, dict(
            shareValue=gkwh.shareValue,
        ))
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
            nshares*%(shareValue)s as amount,
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
        """,dict(
            shareValue=gkwh.shareValue,
        ))
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
            left join
                account_account as pac
            on
                pac.id = ac.parent_id
            where
                pac.code = '1635' and
                true
            group by
                ac.code
            ) as accounting	
        left outer join (
            select
                '1635' || right('000'||right(partner.ref,-1),8) as account_code,
                partner.name as partner_name,
                partner.id as partner_id,
                sum(inv.nshares)*%(shareValue)s as amount,
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


# no cleanup

def getMoveLineInfo(cr, mlids):
    cr.execute("""\
        select
            p.name as partner_name,
            p.id as partner_id,
            ml.*,
            ml.credit-ml.debit as amount,
            false
        from
            account_move_line as ml
        left join
            account_account as a
        on
            ml.account_id=a.id
        left join
            res_partner as p
        on
            --- p.id = ml.partner_id or
            p.ref = 'S' || right(a.code, 6)
        where
            ml.id in %(mlids)s and
            true
        order by p.id, ml.id
    """, dict(
        mlids = tuple(mlids),
    ))
    return dbutils.nsList(cr)

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
            ml.credit-ml.debit as amount,
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
        on
            ac.id = ml.account_id
        left join
            account_account as pac
        on
            pac.id = ac.parent_id
        left join
            res_partner as p
        on
           p.id = ml.partner_id
        where
            pac.code = '1635' and
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
            soci.partner_id as partner_id,
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

def getInvestment(cr, id):
    cr.execute("""\
        SELECT
            inv.*,
            bank.iban as iban
        FROM
            generationkwh_investment as inv
        left join
            somenergia_soci as member
        on
            member.id = inv.member_id
        left join
            res_partner as partner
        on
            partner.id = member.partner_id
        left join
            res_partner_bank as bank
        on
            bank.id = partner.bank_inversions
        WHERE
            inv.id = %(id)s
        """,dict(id=id))
    return dbutils.nsList(cr)[0]

def getInvestmentByMoveline(cr, moveline_id):
    cr.execute("""\
        SELECT
            inv.*,
            bank.iban as iban
        FROM
            generationkwh_investment as inv
        left join
            somenergia_soci as member
        on
            member.id = inv.member_id
        left join
            res_partner as partner
        on
            partner.id = member.partner_id
        left join
            res_partner_bank as bank
        on
            bank.id = partner.bank_inversions
        WHERE
            inv.move_line_id = %(moveline_id)s
        """,dict(moveline_id=moveline_id))
    return dbutils.nsList(cr)[0]



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
            left join
                account_account as pa
            on
                pa.id = a.parent_id
            where
                pa.code = '1635' and
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
    values = d.setdefault(key, [])
    wasEmpty = bool(values)
    values.append(value)
    return wasEmpty

def getAndRemoveFirst(d, key):
    values = d.get(key, [])
    if not values: return None
    return values.pop(0)

def bindMoveLineAndPaymentLine(moveline, orderline):
    communication = orderline.communication2
    ip = communication.split(" IP ")[1] if communication and ' IP ' in communication else '0.0.0.0'
    False and success(
        "Match ml-po ml-{moveline.id} {orderline.name} {orderline.create_date} {amount:=8}€ {moveline.partner_name} {ip}"
        .format(**ns(
            moveline=moveline,
            orderline=orderline,
            amount = moveline.credit-moveline.debit,
            ip = ip,
            )))
    paymentMoveLines[moveline.id] = ns(
        movelineid = moveline.id,
        ref=orderline.name,
        order_date=orderline.create_date,
        partner_id = orderline.partner_id,
        partner_name = orderline.partner_name,
        amount = moveline.credit-moveline.debit,
        ip = ip,
        )

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

def cleanUp(cr):
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
            error("{create_date} {amount} € {account_name} {name}",
                amount=inv.credit-inv.debit,
                **inv)
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

    step(" Compensating pending negative investments already effective")
    for case in cases.lateDivestments:
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

    success("Clean up done")




def allMovements(cr):
    cr.execute("""\
        select
            ml.*,
            ml.credit-ml.debit as amount,
            COALESCE(u.name, 'Nobody') as user,
            partner.name as partner_name
        from
            account_move_line as ml
        left join
            account_account as acc
        on
            acc.id = ml.account_id
        left join
            account_account as pacc
        on
            pacc.id = acc.parent_id
        left join
            account_period as p
        on
            p.id = ml.period_id
        LEFT JOIN
            res_users as u
        ON
            u.id = ml.create_uid
        LEFT JOIN
            res_partner as partner
        ON
            partner.ref = 'S' || right(acc.code, 6)
        where
            pacc.code = '1635' and
            not p.special and
            true
        order by
            create_date
        """)
    return {x.id: x for x in dbutils.nsList(cr)}


def main(cr):

    # Movelines related to payment orders
    step("Emparellant moviments amb remeses")

    global paymentMoveLines
    paymentMoveLines = ns()
    for data in investmentOrderAndMovements(cr):
        step(" Quadrant remesa feta el {move_create_date}".format(**data))


        step("  Comprovant que la remesa i el moviment coincideixen")

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


        step("  Quadrant pagaments amb assentaments per persona i quantitat")
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
                    continue
                bindMoveLineAndPaymentLine(moveline, orderline)
                if orderline.name not in cases.misscorrectedPayments:
                    error(
                        "Amount missmatch {orderline.name} "
                        "order {orderline.amount}€ move {moveline.credit}",
                            partner_id = moveline.partner_id,
                            orderline=orderline,
                            moveline=moveline,
                        )
                    displayPartnersMovements(cr, orderline.partner_id)
                    continue
                corrected = cases.misscorrectedPayments[orderline.name]
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
                    displayPartnersMovements(cr, orderline.partner_id)
                    continue
                warn(
                    "Already corrected amount missmatch {orderline.name} "
                    "order {orderline.amount}€ move {moveline.credit}"
                    .format(**ns(
                        orderline=orderline,
                        moveline=moveline,
                    )))

        for partner_id, movelines in movelinesByPartnerId.items():
            for moveline in movelines:
                error(
                    "Linia de Moviment sense parella "
                    "id {id} {create_date} {credit}€ {partner_name}",
                    **moveline)

    step("Recopilant tots els asentaments del generation")
    global unusedMovements
    unusedMovements = allMovements(cr)

    step("Pairing investments")
    step(" Pairing investments using existing relation")

    activeInvestments = getActiveInvestments(cr)

    unmatchedMoveLines = list(paymentMoveLines.keys())
    unmatchedInvestments = []

    for inv in activeInvestments:
        moveline_id = inv.move_line_id

        if moveline_id not in paymentMoveLines:
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
        solveNormalCase(cr, inv, paymentMoveLines[moveline_id])
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

    step("Retry match payments-investment just by partner")
    orphanPaymentsByPartner = {}

    for moveline_id in unmatchedMoveLines:
        payment = paymentMoveLines[moveline_id]

        wasEmpty = appendToKey(orphanPaymentsByPartner, payment.partner_id, payment)
        if wasEmpty:
            warn("partner with two pending movements id {id} {partner_name}".format(id=moveline_id, **payment))

    unnamedActiveInvestments = []

    for inv in activeInvestments:
        if inv.id not in unmatchedInvestments:
            continue

        partner_id = inv.partner_id
        payment = getAndRemoveFirst(orphanPaymentsByPartner, partner_id)
        if payment:
            solveRepaidCase(cr, inv, payment)
            continue

        if inv.move_line_id in cases.unnamedCases:
            unnamedActiveInvestments.append(inv)
            continue

        error("No name for Investment {move_date_created} {move_line_id} {nshares:=5}00.00€ {partner_name}",**inv)
        displayPartnersMovements(cr, inv.partner_id)

    if orphanPaymentsByPartner:
        step("Solving payments with active no investment (cancelled?)")
    for orphanPayments in orphanPaymentsByPartner.values():
        for orphanPayment in orphanPayments:
            if solveInactiveInvestment(cr, orphanPayment):
                continue
            error("Unassigned name {ref} {order_date} {partner_name}",
                **orphanPayment)
            displayPartnersMovements(cr, orphanPayment.partner_id)

    for inv in unnamedActiveInvestments:
        solveUnnamedCases(cr, inv)


    for moveline_id in ungenerated:
        payment = paymentMoveLines[moveline_id]
        warn("Not yet generated investment {ref} {order_date} {partner_name}"
            .format(**payment))

    for missmatch in movementsVsInvesmentAmounts(cr):
        error("Balance missmatch: "
            "Accounting {accounting_amount} "
            "Investment {investment_amount} "
            "{partner_name}",
            **missmatch)

        displayPartnersMovements(cr, missmatch.investment_partner_id)


from generationkwh.investmentlogs import (
    log_formfilled,
    log_corrected,
    log_charged,
    log_refunded,
    log_banktransferred,
)

def logOrdered(cr, attributes, investment, amount, order_date, ip):
    attributes.nominal_amount = amount
    attributes.paid_amount = 0
    attributes.order_date = order_date.date()
    attributes.purchase_date = None
    attributes.first_effective_date = None
    attributes.last_effective_date = None
    attributes.active = True
    return log_formfilled(dict(
        create_date=order_date,
        user="Webforms",
        ip=ip,
        amount=int(amount),
        iban=investment.iban or u"None",
        ))

def logCorrected(cr, attributes, investment, what):
    if attributes.nominal_amount != what['from']:
        consoleError("Correction missmatches the from was {} but annotated {}"
            .format(attributes.nominal_amount, what['from']))
    attributes.nominal_amount = what.to
    return log_corrected(dict(
        create_date=what.when,
        user="Nobody",
        oldamount = what['from'],
        newamount = what.to,
        ))

def firstEffectiveDate(purchase_date):
    pionersDay = '2016-04-28'
    waitDays = gkwh.waitingDays
    if str(purchase_date) < pionersDay:
        waitDays -= 30
    waitDelta = datetime.timedelta(days=waitDays)
    return purchase_date + waitDelta

def logPaid(cr, attributes, investment, move_line_id):
    ml = unusedMovements.pop(move_line_id)
    attributes.purchase_date = ml.create_date.date()
    attributes.paid_amount += ml.amount
    attributes.first_effective_date = firstEffectiveDate(ml.create_date.date())
    return log_charged(dict(
        create_date=ml.create_date,
        user=ml.user.decode('utf-8'),
        amount=int(ml.amount),
        iban=investment.iban or u"None",
        move_line_id=move_line_id,
        ))

def logRefund(cr, attributes, move_line_id):
    ml = unusedMovements.pop(move_line_id)
    attributes.purchase_date = None
    attributes.first_effective_date = None
    attributes.last_effective_date = None
    attributes.paid_amount += ml.amount
    attributes.active = False
    return log_refunded(dict(
        create_date=ml.create_date,
        user=ml.user.decode('utf-8'),
        move_line_id=move_line_id,
        ))

def logRepaid(cr, attributes, move_line_id):
    ml = unusedMovements.pop(move_line_id)
    attributes.purchase_date = ml.create_date.date()
    attributes.paid_amount += ml.amount
    attributes.first_effective_date = firstEffectiveDate(ml.create_date.date())
    attributes.active = True
    return log_banktransferred(dict(
        create_date=ml.create_date,
        user=ml.user.decode('utf-8'),
        move_line_id=move_line_id,
        ))

def logPartial(cr, attributes, investment, move_line_id):
    ml = unusedMovements.pop(move_line_id)
    attributes.nominal_amount += ml.amount
    attributes.paid_amount += ml.amount
    return (
        u'[{create_date} {user}] '
        u'PARTIAL: Desinversió parcial de {amount} €, en queden {remaining} € [{move_line_id}]\n'
        .format(
        create_date=ml.create_date,
        user=ml.user.decode('utf-8'),
        remaining=attributes.paid_amount,
        move_line_id=move_line_id,
        amount=ml.amount,
        ))

sold = ns()

def logSold(cr, attributes, investment, move_line_id, what):
    import datetime
    from generationkwh.investmentstate import InvestmentState
    ml = unusedMovements.pop(move_line_id)
    mlto = unusedMovements[what.to]
    transaction_date = what.get('date', ml.create_date.date())
    inv1 = InvestmentState(ml.user.decode('utf-8'), ml.create_date,
        first_effective_date = attributes.first_effective_date,
        paid_amount = attributes.paid_amount,
        log = '',
        )
    inv1.emitTransfer(
        data = transaction_date,
        to_partner_name = mlto.partner_name.decode('utf-8'),
        to_name = cases.unnamedCases[mlto.id],
        move_line_id = move_line_id,
        amount = -ml.amount,
        )
    inv2 = InvestmentState(ml.user.decode('utf-8'), ml.create_date)
    inv2.receiveTransfer(
        data = transaction_date,
        move_line_id = what.to,
        amount = mlto.amount,
        from_name = investment.name,
        from_partner_name = ml.partner_name,
        from_order_date = attributes.order_date,
        from_purchase_date = attributes.purchase_date,
        from_first_effective_date = attributes.first_effective_date,
        from_last_effective_date = attributes.last_effective_date,
        )
    changes_to = inv2.changed()
    sold[what.to] = ns(
        changes_to,
        from_partner_name = ml.partner_name,
        from_ref = investment.name,
        )
    changes = inv1.changed()
    attributes.last_effective_date = changes.last_effective_date
    attributes.paid_amount = changes.paid_amount
    attributes.active = changes.active
    return changes.log

def logBought(cr, attributes, investment):
    ml = unusedMovements.pop(investment.move_line_id)
    peer = sold[investment.move_line_id]
    attributes.nominal_amount = peer.nominal_amount
    attributes.paid_amount = ml.amount
    attributes.order_date = peer.order_date
    attributes.purchase_date = peer.purchase_date
    attributes.first_effective_date = peer.first_effective_date
    attributes.last_effective_date = peer.last_effective_date
    attributes.active = True
    return peer.log

def logPact(cr, attributes, investment, what):
    attributes.update(what.changes)
    return (
        u'[{create_date} {user}] '
        u'PACT: Pacte amb l\'inversor. {changes} Motiu: {note}\n'
        .format(
        create_date=what.create_date,
        user=what.user,
        changes=', '.join("{}: {}".format(*x) for x in what.changes.items()),
        note=what.note,
        ))

def crossed(attributes):
    if not attributes.first_effective_date:
        return True
    if not attributes.last_effective_date:
        return False
    if attributes.last_effective_date < attributes.first_effective_date:
        return True
    return False

def logDivestment(cr, attributes, investment, move_line_id):
    ml = unusedMovements.pop(move_line_id)
    attributes.paid_amount += ml.amount
    attributes.last_effective_date = ml.create_date.date()
    attributes.active = not crossed(attributes)
    return (
        u'[{create_date} {user}] '
        u'DIVESTED: Desinversió total [{move_line_id}]\n'
        .format(
        create_date=ml.create_date,
        user=ml.user.decode('utf8'),
        move_line_id=move_line_id,
        ))


def logMovement(cr, attributes, investment, movelineid, what):
    try:
        type = what.type
    except:
        type = what

    if type == 'corrected':
        return logCorrected(cr, attributes, investment, what)
    if type == 'sold':
        return logSold(cr, attributes, investment, movelineid, what)
    if type == 'pact':
        return logPact(cr, attributes, investment, what)
    if type == 'paid':
        return logPaid(cr, attributes, investment, movelineid)
    if type == 'refunded':
        return logRefund(cr, attributes, movelineid)
    if type == 'repaid':
        return logRepaid(cr, attributes, movelineid)
    if type == 'partial':
        return logPartial(cr, attributes, investment, movelineid)
    if type == 'divested':
        return logDivestment(cr, attributes, investment, movelineid)
    raise Exception(
        "T'has colat posant '{}'"
        .format(type))


def checkAttributes(real, computed):

    def check(condition, msg, *args, **kwds):
        if condition: return
        check.failed |= True
        consoleError("Check failed: "+msg.format(*args, **kwds))

    check.failed = False


    for attribute in [
        'order_date',
        'purchase_date',
        'first_effective_date',
        'last_effective_date',
        'active',
        ]:
        realvalue = real[attribute]
        computedvalue = computed[attribute]
        check(realvalue == computedvalue,
            "{} differ {} but computed {}",
            attribute, realvalue, computedvalue)

    expired = computed.last_effective_date and computed.last_effective_date < datetime.date.today()

    if real.active and not expired:
        check(computed.nominal_amount == computed.paid_amount,
            "Nominal is {nominal_amount} but balance is {paid_amount}",
            **computed)

    if not real.active:
        check(computed.paid_amount == 0,
            "Inactive investment should have balance zero and had {}",
            computed.paid_amount)

    if not expired and real.active:
        check(computed.nominal_amount == gkwh.shareValue * real.nshares,
            "Missmatch nshares {}, nominal {} €",
            real.nshares, computed.nominal_amount)

    if expired:
        check(computed.nominal_amount == gkwh.shareValue * real.nshares,
            "Expired not matching nshares {} with nominal {} €",
            real.nshares, computed.nominal_amount)
        check(computed.paid_amount == 0,
            "Expired should have balance 0 and has {} €",
            computed.paid_amount)

    return check.failed

def solveNormalCase(cr, investment, payment):
    "Active investment is paired to the original payment"
    True and success(
        "Solved single {investment.id} {payment.ref} {payment.order_date} {amount:=8}€ {payment.partner_name}"
        .format(**ns(
            investment=investment,
            payment=payment,
            amount=investment.nshares*gkwh.shareValue,
            )))
    investment = getInvestment(cr, investment.id)
    investment.name = payment.ref
    attributes = ns()
    log = ""
    log += logOrdered(cr, attributes, investment, payment.amount, payment.order_date, payment.ip)

    if payment.ref in cases.singlePaymentCases :
        case = cases.singlePaymentCases.pop(payment.ref)
        for movelineid, what in case.iteritems():
            log += logMovement(cr, attributes, investment, movelineid, what)
    else:
        log += logPaid(cr, attributes, investment, payment.movelineid)
        False and displayPartnersMovements(cr, payment.partner_id)

    True and success(("\n"+log).encode('utf-8'))

    cr.execute("""\
        UPDATE
            generationkwh_investment as inv
        SET
            name = %(name)s,
            log = %(log)s,
            order_date = %(order_date)s
        WHERE
            inv.id = %(id)s
        """, dict(
            id = investment.id,
            order_date = payment.order_date,
            name = payment.ref,
            log = log,
        ))

    investment = getInvestment(cr, investment.id)
    if checkAttributes(investment, attributes):
        displayPartnersMovements(cr, payment.partner_id)



def solveRepaidCase(cr, investment, payment):
    "Active investment is related to a posterior payment"

    True and success(
        "Solved repaid {investment.id} {payment.ref} {payment.order_date} {amount:=8}€ {payment.partner_name}"
        .format(**ns(
            investment=investment,
            payment=payment,
            amount=investment.nshares*gkwh.shareValue,
            )))
    log= ""
    attributes = ns()
    investment = getInvestment(cr, investment.id)
    investment.name = payment.ref
    log += logOrdered(cr, attributes, investment, payment.amount, payment.order_date, payment.ip)
    if payment.ref not in cases.repaidCases :
        failed("En serio") # TODO explain the error

    case = cases.repaidCases.pop(payment.ref)
    for movelineid, what in case.iteritems():
        log += logMovement(cr, attributes, investment, movelineid, what)
    False and displayPartnersMovements(cr, payment.partner_id)
    True and success(("\n"+log).encode('utf-8'))

    cr.execute("""\
        UPDATE
            generationkwh_investment as inv
        SET
            name = %(name)s,
            log = %(log)s,
            order_date = %(order_date)s
        WHERE
            inv.id = %(id)s
        """, dict(
            id = investment.id,
            order_date = payment.order_date,
            name = payment.ref,
            log = log,
        ))
    investment = getInvestment(cr, investment.id)
    if checkAttributes(investment, attributes):
        displayPartnersMovements(cr, payment.partner_id)


def solveUnnamedCases(cr, investment):
    "Cases with no payment order, usually transfer receptors"
    name = cases.unnamedCases[investment.move_line_id]
    partner_id = investment.partner_id
    True and success(
        "Solved compra {investment.id} {name} {amount:=8}€ {investment.partner_name}"
        .format(
            investment=investment,
            amount=investment.nshares*gkwh.shareValue,
            name=name,
            ))
    log = ""
    attributes=ns()
    log += logBought(cr, attributes, investment)
    success(("\n"+log).encode('utf-8'))
    cr.execute("""\
        UPDATE
            generationkwh_investment as inv
        SET
            name = %(name)s,
            log = %(log)s
        WHERE
            inv.id = %(investment)s
    """, dict(
        name = name,
        log = log,
        investment=investment.id,
    ))
    investment = getInvestment(cr, investment.id)
    if checkAttributes(investment, attributes):
        displayPartnersMovements(cr, partner_id)
    return True

def solveInactiveInvestment(cr, payment):
    "There is no active investment"

    name = payment.ref
    if name not in cases.cancelledCases:
        return False

    case = cases.cancelledCases.pop(name)
    investment = getInvestmentByMoveline(cr, payment.movelineid)
    log = ""
    attributes=ns()
    investment.name = name
    log += logOrdered(cr, attributes, investment, payment.amount, payment.order_date, payment.ip)
    for movelineid, what in case.iteritems():
        log += logMovement(cr, attributes, investment, movelineid, what)

    True and success(
        "Solved inactive {investment.id} {payment.ref} {payment.order_date} {amount:=8}€ {payment.partner_name}"
        .format(**ns(
            investment=investment,
            payment=payment,
            amount=investment.nshares*gkwh.shareValue,
            )))
    success(("\n"+log).encode('utf-8'))
    cr.execute("""\
        UPDATE
            generationkwh_investment as inv
        SET
            name = %(name)s,
            log = %(log)s,
            order_date = %(order_date)s,
            purchase_date = %(purchase_date)s,
            active = false
        WHERE
            inv.id = %(investment)s
    """, dict(
        order_date = payment.order_date,
        investment = investment.id,
        name = investment.name,
        log = log,
        purchase_date = attributes.purchase_date,
    ))
    investment = getInvestment(cr, investment.id)
    if checkAttributes(investment, attributes):
        displayPartnersMovements(cr, payment.partner_id)
    return True

def showUnusedMovements(cr):
    if unusedMovements:
        consoleError("Some movements were still not considered in logs") 
        for info in getMoveLineInfo(cr, unusedMovements):
            error("    mov {date_created} {id} {partner_name} {amount} {name}",
                **info)

    if cases.repaidCases:
        consoleError("Some repaid cases have been not considered")
        consoleError(cases.repaidCases.dump())

    if cases.singlePaymentCases:
        consoleError("Some single payment cases have been not considered")
        consoleError(cases.singlePaymentCases.dump())


    if cases.cancelledCases:
        consoleError("Some cancelled payment cases have been not considered")
        consoleError(cases.cancelledCases.dump())


cases = ns.load('migration.yaml')

with psycopg2.connect(**configdb.psycopg) as db:
    with db.cursor() as cr:
        with transaction(cr, discarded='--doit' not in sys.argv):
            cleanUp(cr)
            main(cr)
            showUnusedMovements(cr)


# vim: et ts=4 sw=4
