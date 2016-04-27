    SELECT
        pol.id as polissa_id,
        soci.id AS soci_id,
        CASE
            WHEN pol.pagador=soci.id THEN 1
            WHEN pol.titular=soci.id THEN 2
            END AS PRIORIDAD
    FROM res_partner AS soci
    LEFT JOIN
        giscedata_polissa AS pol ON
            pol.titular = soci.id OR
            pol.pagador = soci.id
    LEFT JOIN
        giscedata_cups_ps AS cups ON
            cups.id = pol.cups
    WHERE
        soci.active AND
        pol.state = 'activa' AND
        cups.active AND
        pol.active AND
        soci.id in %(socis)s AND
        TRUE
    ORDER BY
        soci.id,prioridad,polissa_id ASC
