# somenergia-generationkwh

OpenERP module and library to manage [Som Energia]'s Generation kWh

[![Build Status](https://travis-ci.org/Som-Energia/somenergia-generationkwh.svg?branch=master)](https://travis-ci.org/Som-Energia/somenergia-generationkwh)

[Generation kWh] is a campaign to design a feasible alternative
to electricity self-production in the Spanish market.
Spanish market legislation has been designed in a way quite
hostile towards distributed renewable energies and user self-production
and we propose _collective self-production_ as a formula that still
fits in the market.

[Generation kWh]:https://generationkwh.org
[Som Energia]:https://somenergia.coop

The goal of the campaign is to collect investment from cooperative members
for new renewable production projects.
Investors don't get an interest rate in exchange for their investment
but the right to use kWh produced in such plants at cost price,
instead of the price derived from the official auction.
Official auction use a marginalist method so that the inclusion
in the mix of expensive fossil sources, raises final prices
to be paid for every source, even cheaper renewable sources.

This package holds the business logic to handle the use rights
coming from the production plants related to this campaing and
transfer them to user invoices.

## Dependencies

In Debian/Ubuntu

```bash
$ sudo apt-get build-dep python-numpy
```

## CHANGES

### 2.4.1

- Fix: Error calling notification function on default assignments
- `calculate_irpf_generation.py`: New script to compute the IRPF tax retention

### 2.4.0

- API for the OV to list investments and assignments for a member
    - `ResPartner.www_generationkwh_assignments(partner_id)`
    - `ResPartner.www_generationkwh_investments(partner_id)`
- New verbose list command `genkwh_investment ls`
- Python3 compatibility on the python module (not yet the erp one)
- Travis coverage
- Overall test desfragilization
- `Investment.create_from_transfer` returns just the new id, not also the old one






