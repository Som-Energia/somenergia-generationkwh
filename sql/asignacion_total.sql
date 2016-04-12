select sub.name as soci, max(pol.name) as assigned_polissa from (
               SELECT
                    soci.id AS soci_id,
                    soci.name AS name,
                    max(case when pol.pagador=soci.id then 2 when pol.titular=soci.id then 1 end) as PRIORIDAD,
                    COALESCE(	MAX(CASE when POL.PAGADOR=soci.id THEN cups.conany_kwh ELSE NULL END), 
				MAX(CASE when POL.PAGADOR!=soci.id AND POL.TITULAR=soci.id THEN cups.conany_kwh ELSE NULL END)
			    ) as consumprioritario,
                    FALSE
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
                    cups.active and
                    pol.active and
                    TRUE
                GROUP BY 
		    SOCI.ID
                ORDER BY
                    soci.id ASC
) as sub
	INNER JOIN giscedata_polissa pol ON
		CASE WHEN PRIORIDAD = 2 THEN POL.PAGADOR=SOCI_ID WHEN PRIORIDAD=1 THEN POL.TITULAR=SOCI_ID ELSE FALSE END
	INNER JOIN giscedata_cups_ps cups ON
		cups.conany_kwh=consumprioritario AND
		cups.id = pol.cups
        INNER JOIN (
            SELECT 
		sum(LINE.AMOUNT) as inversion,
                max(partner_id) AS already_invested
            FROM payment_line AS line
            LEFT JOIN
                payment_order AS remesa ON remesa.id = line.order_id 
            WHERE
                remesa.mode = 19
            GROUP BY partner_id
            ) AS investments on already_invested=soci_id
where
	POL.STATE = 'activa' and
	cups.active and
	pol.active
group by sub.name