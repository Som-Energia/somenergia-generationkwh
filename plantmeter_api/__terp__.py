# -*- coding: utf-8 -*-
{
  "name": "Generationkwh production manager",
  "description": """Support for SomEnergia's plantmete in GisceERP""",
  "version": "0.0.3",
  "author": "Som-Energia",
  "category": "Master",
  "depends": ['base'],
  "init_xml": [],
  "demo_xml": [],
  "update_xml": [
    "security/plantmeter_api.xml",
    "security/ir.model.access.csv",
    ],
  "active": False,
  "installable": True
}
