#!/usr/bin/env python
# -*- coding: utf8 -*-


import dbutils
from yamlns import namespace as ns


def activeInvestmentRelatedToFiscalEndYear(db):
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
    with db.cursor() as cr:
        cr.execute(query)

def deleteInactiveInvestmentRelatedToFiscalEndYear(db):
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
    with db.cursor() as cr:
        cr.execute(query)

def getGenerationMovelinesByPartner(db, partner_id):
    with db.cursor() as cr:
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
    with db.cursor() as cr:
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

def getInvestmentsByPartner(db, partner_id):
    with db.cursor() as cr:
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
    with db.cursor() as cr:
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


def getOrderLines(db, order_id):
    with db.cursor() as cr:
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

def getMoveLines(db, move_id):
    with db.cursor() as cr:
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

def getActiveInvestments(db):
    with db.cursor() as cr:
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


def lastInvestment(db):
    with db.cursor() as cr:
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


def investmentOrderAndMovements(db, modeName='GENERATION kWh'):
    with db.cursor() as cr:
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
    solvedMovelines[moveline.id] = ns(
        ref=orderline.name,
        order_date=orderline.create_date,
        partner_id = orderline.partner_id,
        partner_name = orderline.partner_name,
        amount = moveline.credit-moveline.debit,
        )

def bindInvestmentWithOrder(db, investment, moveline):
    True and success(
        "Match inv-od {investment.id} {moveline.ref} {moveline.order_date} {amount:=8}€ {moveline.partner_name}"
        .format(**ns(
            investment=investment,
            moveline=moveline,
            amount=investment.nshares*100.,
            )))

    with db.cursor() as cr:
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

def displayPartnersMovements(db, partner_id):
    movelines = getGenerationMovelinesByPartner(db,partner_id)
    for m in movelines:
        m.amount = m.credit -m.debit
        error("    mov {date_created} {id} {partner_name} {amount} {name}"
            .format(**m))
    investments = getInvestmentsByPartner(db, partner_id)
    for inv in investments:
        inv.amount = inv.nshares*100.
        inv.active = 'y' if inv.active else 'n'
        error("    inv {active} {order_date_or_not} {purchase_date_or_not} {first_effective_date_or_not} {last_effective_date_or_not} {id} {partner_name} {amount} {name}"
            .format(
            order_date_or_not = inv.order_date or '____-__-__',
            purchase_date_or_not = inv.purchase_date or '____-__-__',
            first_effective_date_or_not = inv.first_effective_date or '____-__-__',
            last_effective_date_or_not = inv.last_effective_date or '____-__-__',
            **inv))

import configdb
import psycopg2
from consolemsg import step, warn, success, error, fail

with psycopg2.connect(**configdb.psycopg) as db:

    step("Clean up cases")
    fiscalEndYearInvestments = activeInvestmentRelatedToFiscalEndYear(db)
    if fiscalEndYearInvestments:
        fail("There are active investments which are related to fiscal end year")
    print deleteInactiveInvestmentRelatedToFiscalEndYear(db)

    solvedMovelines = ns()
    step("Pairing movelines and orderlines by order/move")

    for data in investmentOrderAndMovements(db):
        step("Quadrant remesa feta el {move_create_date}".format(**data))


        step(" Check that movement and order are paired")

        if not data.move_id:
            warn("{}: Order without movement. Id {}, with {} entries" .format(
                data.order_sent_date or "not yet",
                data.order_id,
                data.order_nlines,
                ))
            continue
        if not data.order_id:
            warn("{}: Movement without order. Id {}, with {} entries".format(
                data.move_create_date or "not yet",
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

        orderLines = getOrderLines(db, data.order_id)
        moveLines = getMoveLines(db, data.move_id)

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
                        "{name} id {id} {order_sent_date} {amount}€ {partner_name}"
                        .format(**orderline))
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
                displayPartnersMovements(db, orderline.partner_id)

        for partner_id, movelines in movelinesByPartnerId.items():
            for moveline in movelines:
                error(
                    "Linia de Moviment sense parella "
                    "id {id} {create_date} {credit}€ {partner_name}"
                    .format(**moveline))

    step("Pairing investments")
    step(" Pairing investments using existing relation")

    investments = getActiveInvestments(db)

    unmatchedMoveLines = list(solvedMovelines.keys())
    unmatchedInvestments = []

    for inv in investments:
        moveline_id = inv.move_line_id

        if moveline_id not in solvedMovelines.keys():
            warn("Moveline {move_line_id} refered by inv {id} not in a payment order: "
                "partner {partner_name} {nshares}00€ '{mlname}'"
                .format(**inv))
            #warn(inv.dump())
            unmatchedInvestments.append(inv.id)
            continue
        related_moveline = solvedMovelines[moveline_id]
        if related_moveline.partner_id != inv.partner_id:
            error("Moveline partner missmatch inv {partner_name} mov {mov_partner} {move_line_id} {nshares}00€ {mlname}".format(
                mov_partner=related_moveline.partner_name,
                **inv
                ))
            displayPartnersMovements(db, inv.partner_id)
            displayPartnersMovements(db, related_moveline.partner_id)
            unmatchedInvestments.append(inv.id)
            continue
        if related_moveline.amount != inv.nshares*100:
            warn("Amount missmatch {partner_name} inv {nshares}00€ mov {mov_amount}€ {mlname}"
                .format(
                    mov_amount=related_moveline.amount,
                    **inv))
            displayPartnersMovements(db, inv.partner_id)
        bindInvestmentWithOrder(db, inv, solvedMovelines[moveline_id])
        if moveline_id not in  unmatchedMoveLines:
            error("Move line referenced twice {move_line_id} {partner_name}".format(**inv))
            displayPartnersMovements(db, inv.partner_id)
        else:
            unmatchedMoveLines.remove(moveline_id)


    lastGeneratedMoveLine = lastInvestment(db)
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
        moveline = solvedMovelines[moveline_id]

        wasEmpty = appendToKey(orphanMoveLinesByPartner, moveline.partner_id, moveline)
        if wasEmpty:
            warn("partner with two pending movements id {id} {partner_name}".format(id=moveline_id, **moveline))

    for inv in investments:
        if inv.id not in unmatchedInvestments:
            continue

        partner_id = inv.partner_id
        solution = getAndRemoveFirst(orphanMoveLinesByPartner, partner_id)
        if not solution:
            error("No name for Investment {move_date_created} {move_line_id} {nshares:=5}00.00€ {partner_name}".format(**inv))
            displayPartnersMovements(db, inv.partner_id)
            continue
        bindInvestmentWithOrder(db, inv, solution)

    for orphanNames in orphanMoveLinesByPartner.values():
        for orphanName in orphanNames:
            error("Unassigned name {ref} {order_date} {partner_name}"
                .format(**orphanName))
            displayPartnersMovements(db, orphanName.partner_id)


    for moveline_id in ungenerated:
        moveline = solvedMovelines[moveline_id]
        warn("Not yet generated investment {ref} {order_date} {partner_name}".format(**moveline))
        




