    SELECT
	pol.name as polissa_id,
        soci.id AS soci_id,
        CASE
            WHEN pol.pagador=soci.id THEN 2
            WHEN pol.titular=soci.id THEN 1
            END AS PRIORIDAD
    FROM res_partner AS soci
    LEFT JOIN
        giscedata_polissa AS pol ON
            pol.titular = soci.id OR
            pol.pagador = soci.id
    LEFT JOIN
        giscedata_cups_ps AS cups ON
            cups.id = pol.cups
    INNER JOIN (
        SELECT 
            sum(LINE.AMOUNT) AS inversion,
            max(partner_id) AS already_invested
        FROM payment_line AS line
        LEFT JOIN
            payment_order AS remesa ON remesa.id = line.order_id 
        WHERE
            remesa.mode = 19
        GROUP BY partner_id
        ) AS investments on already_invested=soci.id
    WHERE
        soci.active AND
        pol.state = 'activa' AND
        cups.active AND
        pol.active AND
        soci.id in (10283,24500,13846,32922,12992,4320,400,3) AND
        TRUE
    ORDER BY
        soci.id,prioridad,polissa_id ASC
