# somenergia-generationkwh

OpenERP module and library to manage [Som Energia]'s Generation kWh


[![CI](https://github.com/Som-Energia/somenergia-generationkwh/actions/workflows/main.yml/badge.svg)](https://github.com/Som-Energia/somenergia-generationkwh/actions/workflows/main.yml)
[![CircleCI](https://circleci.com/gh/Som-Energia/somenergia-generationkwh.svg?style=svg)](https://circleci.com/gh/Som-Energia/somenergia-generationkwh)
[![Coverage Status](https://coveralls.io/repos/github/Som-Energia/somenergia-generationkwh/badge.svg)](https://coveralls.io/github/Som-Energia/somenergia-generationkwh)

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

## Testing

```bash
nosetests generationkwh # for unittests
nosetests som_generationkwh/test # for functional/erp, requires running local erp
dodestral -m som_generationkwh # for destral tests, without production database either running local erp
```

[Destral docs]:https://destral.readthedocs.io/en/latest/


## CHANGES

### 2.5.8 2023-09-25

- PR [#8](https://github.com/Som-Energia/somenergia-generationkwh/pull/136) Added bank mandate wizard

### 2.5.7 2020-01-29

- PR #8 Added logic to model 193 lines wizard

### 2.5.6 2020-01-15

- CreateFromForm: Can create Aportacions

### 2.5.5 2019-12-16

- `genkwh_mtc curve` new option `--by`, to aggregate the matrix in different ways.
	- dayhour: values for every hour for each day (the old one)
	- day: just the dayly accomulated
	- monthhour: values summated each month for each hour
	- month: just the monthly accomulated
- Rights granter: logs now include input and output remainder
- scriptlaucher: more scripts and options
- `genkwh_plants`: safe unicode for pipes
- Regression: Python 3 compatibility for the generationkwh module
- New model generationkwh.emission to create new investment campaigns

### 2.5.4 2019-07-19

_Production rewrite release_

- Simplifications due to plantmeter functionality externalized to gisce
    - ProductionLoader renamed as RightsGranter
    - Tests fill production directly instead using csv's plugins
    - Removed `som_generation.RightsGranter.retrieveMeasuresFromPlants`
    - Removed `som_generation.RightsGranter.endPoint`
    - Removed `som_generation.ProductionAggregatorProvider.getNShares`
- `genkwh_reminders` new subcommands pop and update
- `genkwh_productionloader` recompute subcommand to be able to recompute
  rights respecting existing ones if something weird happens
  (ex. you have been reading from the wrong plant for a while)
- A new mongo collection `rightscorrection` used to track the divergences
  from the rights curve that should be expected given the production
  when you apply recompute.
- Added scriptlauncher file to remotely launch commands of interest
- added parameter `lastDateToCompute` to `RightsGranter.computeAvailableRights`

### 2.5.3 2019-06-17

- MOD: Add IRPF retention to amortization and divestment invoices
- MOD: Change profint formula to avoid 3rd decimal

### 2.5.2 2019-05-13

- MOD: Add profit amount in Generationwkh invoice line

### 2.5.1 2019-04-29

- FIX: Change date type in `Investment.create_from_transfer`
- `genkwh_reminders` has a new `active` subcommand to list just active
- `genkwh_reminders` subcommand `listactive` renamed to `listall` which is what it does
- Install scripts: `genkwh_reminders`, `genkwh_productionloader`, `genkwh_curve`, `genkwh_rights`, `genkwh_usage`

### 2.5.0 2019-04-02

- Multiple plants supported
- LayeredShareCurve: Generalized additive constant curve from MemberShareCurve for PlantShareCurve

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






