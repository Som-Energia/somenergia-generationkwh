# -*- coding: utf-8 -*-
{
  "name": "Generation kWh",
  "description": """Support for SomEnergia's Generation kWh in GisceERP""",
  "version": "2.5.7",
  "author": "GISCE-TI & Som Energia",
  "category": "Master",
  "depends": [
    'base',
    'product',
    "poweremail",
    "poweremail_references",
    'som_polissa_soci',
    'som_inversions',
    'som_plantmeter',
    'l10n_ES_aeat_mod193',
    'l10n_ES_aeat_sii',
    'remeses_base',
    'som_poweremail_common_templates',
    'som_partner_account',
    ],
  "init_xml": [],
  "demo_xml": [
      "tests/generation_data_demo.xml",
      ],
  "update_xml": [
    "amortization_report.xml",
    "som_generationkwh_data.xml",
    "giscedata_facturacio_view.xml",
    "som_generationkwh_view.xml",
    "wizard/wizard_investment_activation.xml",
    "wizard/wizard_investment_amortization.xml",
    "wizard/wizard_investment_payment.xml",
    "wizard/wizard_investment_creation.xml",
    "wizard/wizard_investment_cancel_or_resign.xml",
    "wizard/wizard_investment_divest.xml",
    "wizard/wizard_investment_transfer.xml",
    "wizard/wizard_aeat193_from_gkwh_invoices_view.xml",
    "wizard/wizard_send_retencio_estalvi_to_members.xml",
    "investment_view.xml",
    "assignment_view.xml",
    "somenergia_soci_view.xml",
    "somenergia_soci_data.xml",
    "security/som_generationkwh_security.xml",
    "security/ir.model.access.csv",
    "emission_view.xml",
    ],
  "active": False,
  "installable": True
}
