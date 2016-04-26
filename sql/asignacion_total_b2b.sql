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
    WHERE
        COALESCE(soci.active,TRUE) AND
        COALESCE(pol.state = 'activa',TRUE) AND
        COALESCE(cups.active, TRUE) AND
        COALESCE(pol.active, TRUE) AND
        soci.id in (10283,24500,13846,32922,12992,4320,400) AND
        TRUE
    ORDER BY
        soci.id,prioridad ASC
