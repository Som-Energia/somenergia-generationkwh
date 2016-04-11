   SELECT
		    pol.name,
                    cups.conany_kwh as consumo,
                    case when pol.pagador=soci.id then 1 when pol.titular=soci.id then 2 end as PRIORIDAD
                FROM res_partner AS soci

                inner JOIN
		    giscedata_polissa AS pol ON 
			pol.pagador = soci.id 
			or pol.titular = soci.id AND 
			pol.active AND 
			pol.state = 'activa'
                inner JOIN 
                    giscedata_cups_ps AS cups ON 
			cups.id = pol.cups AND
			cups.active
                WHERE
                    soci.id=31712 AND
                    pol.state = 'activa' and
                    tRUE
                ORDER BY
		    PRIORIDAD,
		    CONSUMO
