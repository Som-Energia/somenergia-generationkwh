SELECT
    pol.id as polissa_id,
    soci.id AS soci_id,
    cups.conany_kwh as annual_use,
--    CASE
--        WHEN pol.pagador=soci.id THEN 1
--        WHEN pol.titular=soci.id THEN 2
--        END AS prioridad,
    TRUE
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
--    soci.active AND
--    pol.state = 'activa' AND
--    cups.active AND
--    pol.active AND
    TRUE
ORDER BY
--    soci.id,
--    prioridad,
--    annual_use DESC,
--    polissa_id,
    TRUE
