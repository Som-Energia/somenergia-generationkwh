# -*- coding: utf-8 -*-
{
  "name": "Generation kWh",
  "description": """Support for SomEnergia's Generation kWh in GisceERP""",
  "version": "0.0.1",
  "author": "GISCE-TI & Som Energia",
  "category": "Master",
  "depends": [
    'base',
    "poweremail",
    "poweremail_references",
    'som_polissa_soci',
    'som_inversions',
    'som_plantmeter',
    ],
  "init_xml": [],
  "demo_xml": [],
  "update_xml": [
    "security/generationkwh_api_security.xml",
    "generationkwh_api_data.xml",
    "giscedata_facturacio_view.xml",
    "generationkwh_api_view.xml",
    "wizard/wizard_investment_activation.xml",
    "investment_view.xml",
    "assignment_view.xml",
    "somenergia_soci_view.xml",
    "somenergia_soci_data.xml",
    "security/ir.model.access.csv",
    ],
  "active": False,
  "installable": True
}
