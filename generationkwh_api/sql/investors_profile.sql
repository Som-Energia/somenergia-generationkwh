SELECT
    soci.id,
    partner_id,
    COUNT(cups.id) AS ncontractes,
    SUM(CASE
        WHEN pol.pagador=soci.partner_id
        THEN 1
        ELSE 0
        END
    ) AS npolizas_pagador,
    SUM(CASE
        WHEN
            pol.pagador!=soci.partner_id AND
            pol.titular=soci.partner_id
        THEN 1
        ELSE 0
        END
    ) AS npolizas_titular,
    SUM(CASE
        WHEN
            pol.pagador!=soci.partner_id AND
            pol.titular!=soci.partner_id AND
            pol.soci=soci.partner_id
        THEN 1
        ELSE 0
        END
    ) AS npolizas_socio,
    SUM(cups.conany_kwh) AS consumannual,
    MAX(cups.conany_kwh) AS maxconsumannual,
    STRING_AGG(pol.id::text,',') AS polizas,
    TRUE
FROM somenergia_soci AS soci
LEFT JOIN giscedata_polissa AS pol ON
    (
        pol.titular = soci.partner_id OR
        pol.pagador = soci.partner_id OR
        pol.soci = soci.partner_id
        ) AND
    pol.active AND 
    pol.state = 'activa' AND
    TRUE
LEFT JOIN giscedata_cups_ps AS cups ON
    cups.id = pol.cups
INNER JOIN (
    SELECT 
        SUM(line.amount) AS inversion,
        MAX(line.partner_id) AS already_invested
    FROM payment_line AS line
    LEFT JOIN
        payment_order AS remesa ON remesa.id = line.order_id 
    WHERE
        remesa.mode = 19 -- Generationkwh
    GROUP BY partner_id
    ) AS investments ON already_invested = partner_id 
GROUP BY
    soci.id,
    partner_id,
    TRUE



