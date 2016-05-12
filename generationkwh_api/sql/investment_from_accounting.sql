--- Returns tuples to create new investments
--- from the accounting move lines.
--- Versio dura
SELECT
    member_id AS member_id,
    DIV(credit-debit,100) AS nshares,
    purchase_date AS purchase_date,
    move_line_id AS move_line_id,
    CASE
        WHEN %(waitingDays)s IS NULL
        THEN NULL
        ELSE
            purchase_date
            + %(waitingDays)s * interval '1 day'
        END AS activation_date,
    CASE
        WHEN %(waitingDays)s IS NULL
        OR %(expirationYears)s IS NULL
        THEN NULL
        ELSE
            purchase_date
            + %(waitingDays)s * interval '1 day'
            + %(expirationYears)s * interval '1 year'
        END AS deactivation_date
FROM (
    SELECT
        soci.id AS member_id,
        line.credit AS credit,
        line.debit AS debit,
        line.date_created AS purchase_date,
        line.id AS move_line_id
    FROM
        account_account AS account
    INNER JOIN
        account_move_line AS line
        ON line.account_id = account.id
    JOIN
        res_partner AS partner
        ON partner.id = line.partner_id
--        OR partner.ref = 'S' || LPAD(RIGHT(account.code,6),6,'0')
    JOIN
        somenergia_soci AS soci
        ON soci.partner_id = partner.id
    LEFT JOIN
        generationkwh_investment AS investment
        ON investment.move_line_id = line.id
    WHERE
        investment.move_line_id IS NULL AND
        account.code ILIKE %(generationAccountPrefix)s AND
        -- {timecondition}
        COALESCE(line.date_created <=%(stop)s, TRUE) AND
        COALESCE(line.date_created >=%(start)s, TRUE) AND
        TRUE
) AS sub
ORDER BY
    sub.move_line_id
