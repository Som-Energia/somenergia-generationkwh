        SELECT
            soci_id,
            name,
            nsoci,
            nif,
            lang,
            consumannual,
            consumprioritario,
            ncontractes,
            polizas_titular,
            polizas_pagador,
            email,
            CEIL((0-inversion)/100) as acciones,
            already_invested IS NOT NULL AS already_invested,
            ARRAY[8] @> categories AS essoci,
            FALSE
        FROM (
            SELECT DISTINCT ON (sub.soci_id)
                sub.soci_id as soci_id,
                sub.name AS name,
                sub.nsoci AS nsoci,
                sub.nif AS nif,
                sub.lang AS lang,
                sub.consumannual AS consumannual,
		sub.consumprioritario as consumprioritario,
                sub.ncontractes AS ncontractes,
		sub.polizas_titular AS polizas_titular,
		sub.polizas_pagador AS polizas_pagador,
                address.email,
                categories,
                FALSE
            FROM (
                SELECT
                    soci.id AS soci_id,
                    soci.name AS name,
                    soci.ref AS nsoci,
                    soci.vat AS nif,
                    soci.lang AS lang,
                    COALESCE(SUM(cups_pag.conany_kwh),0)+COALESCE(SUM(cups_tit.conany_kwh),0) AS consumannual,
                    COALESCE(MAX(cups_pag.conany_kwh),MAX(cups_tit.conany_kwh)) as consumprioritario,
                    COUNT(CUPS_TIT.ID)+COUNT(CUPS_PAG.ID) AS ncontractes,
                    COUNT(pol_tit.id) AS polizas_titular,
                    COUNT(pol_pag.id) AS polizas_pagador,
                    ARRAY_AGG(cat.category_id) as categories,
                    FALSE
                FROM res_partner AS soci
                LEFT JOIN
                    giscedata_polissa AS pol_tit ON 
                        pol_tit.titular = soci.id AND
                        pol_tit.pagador != soci.id AND 
                        pol_tit.active AND 
                        pol_tit.state = 'activa'

                LEFT JOIN
		    giscedata_polissa AS pol_pag ON 
			pol_pag.pagador = soci.id AND 
			pol_pag.active AND 
			pol_pag.state = 'activa'
                LEFT JOIN 
                    giscedata_cups_ps AS cups_tit ON 
			cups_tit.id = pol_tit.cups AND
			cups_tit.active 
		LEFT JOIN
		    giscedata_cups_ps AS cups_pag ON
			cups_pag.id = pol_pag.cups AND
			cups_pag.active
                LEFT JOIN
                    res_partner_category_rel AS cat ON
                    cat.partner_id = soci.id
                WHERE
                    soci.active AND (
                    (pol_tit.state = 'activa' AND cups_tit.active ) OR
                    (pol_pag.state = 'activa' AND cups_pag.active )) AND
                    TRUE
                GROUP BY
                    soci.id
                ORDER BY
                    soci.id ASC
            ) AS sub
            LEFT JOIN
                res_partner_address AS address ON (address.partner_id = sub.soci_id)
            WHERE
                address.active AND
                address.email IS NOT NULL AND
                address.email != '' AND
                TRUE
            GROUP BY
                sub.soci_id,
                sub.name,
                sub.nsoci,
                sub.nif,
                sub.lang,
                sub.consumannual,
                sub.consumprioritario,
                sub.ncontractes,
		sub.polizas_titular,
		sub.polizas_pagador,
                address.email,
                categories,
                TRUE
        ) AS result
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
            ) AS investments ON already_invested = soci_id 
        WHERE
            soci_id=31712
        ORDER BY
            name ASC