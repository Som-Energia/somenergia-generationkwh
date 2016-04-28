SELECT
    pol.id as contract_id,
    soci.id AS member_id,
    cups.conany_kwh as annual_use,
    CASE
        WHEN pol.pagador=soci.id THEN 1
        WHEN pol.titular=soci.id THEN 2
        END AS payerOwner
FROM res_partner AS soci
LEFT JOIN
    giscedata_polissa AS pol ON
        pol.pagador = soci.id OR
        pol.titular = soci.id OR
        FALSE
LEFT JOIN
    giscedata_cups_ps AS cups ON
        cups.id = pol.cups
WHERE
    soci.id in %(socis)s AND
    -- Next filters not supported by tests
    soci.active AND
    pol.state = 'activa' AND
    pol.active AND
    cups.active AND
    TRUE
ORDER BY
    soci.id,
    payerOwner ASC,
    annual_use DESC,
    TRUE
