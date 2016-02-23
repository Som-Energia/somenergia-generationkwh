# -*- coding: utf-8 -*-
{
  "name": "Generation kWh",
  "description": """Support for SomEnergia's Generation kWh in GisceERP""",
  "version": "0.0.1",
  "author": "GISCE",
  "category": "Master",
  "depends": ['base', 'som_polissa_soci'],
  "init_xml": [],
  "demo_xml": [],
  "update_xml": [
    "generationkwh_api_data.xml",
    "security/ir.model.access.csv",
    ],
  "active": False,
  "installable": True
}
