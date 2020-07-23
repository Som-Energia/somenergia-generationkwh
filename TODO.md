# TODO's

## APO's migration

+ Afegir el partner id
- Obtenir objectes movelines, indexats per usuari
- Anar marcant movelines com fetes, a mida que anem lligant movelines amb una operacio d'una inversio numerada
	- Recuperar mapping de noms (i document) de les remeses
	- Remeses sense moveline?
	- Associar les inversions desinvertides
		- Desinversions parcials
		- Desinversions globals
	- Que passa amb el macro moviment d'abril?


## Inmediate TODO's

- Turn warning on investment creation with no member available into a logged warning
- Investment: Add test on list for inactivated investment
- Assignments: Add test for observations log
- Cron: Turn move lines into investments
- Cron: Create members from partners becoming members
- Manual testing scripts
    - Afegir lectures (a ma)
    - Generar factures (a ma)
- Modify invoicing mail to warn about having Genkwh active
- ProductionToRightsPerShare naive: Protect againts divby0 when total active actions is zero
- Investment: ondelete -> member
- Investment: Janitoring: mode lines without partner
- Investment: Janitoring: mode lines without dates
- Investment: constant for the account root for generationkwh accounts
- Investment: constant for the number of digits for the soci code in accounts
    - Can be found at `ir_secuence.code="socis"`
- Assignment: ondelete -> polissa
- Assignment: ondelete -> member
- Assignment: Having a log, remove expiration field, just delete the assigment
- BUG: Mongodb erp integration: reconnections do not refresh connection attr
- Assignments Script: filter members with 'mail already sent' flag, unles `--insist` flag is enabled
- Assignments Script: filter members already with assignments unless `--force` option


## Postponed for Next Iterations

- Rights/Usage: Protect the system when Rights < Usage (because of recomputation of procduction, or any weir thing)
- Rights/Usage: Regularize usage above member rights (because of recomputation of procduction, or any weir thing)
- Investment: optimize investment creation with sql
- Investment created by webforms and then payment orders are created on them.
    - Webform -> draft investment 
    - draft investment -> payment request -> active investment
    - active investment -> payment rejected -> inactive invesment
- Assignment: Given a contract that can consume rights from several members, define the order in which it should consume them.
    - Right now is an arbitrary order, not bad
    - Rare case, low priority, wait for actual cases
- WebForms: Create the soci
- WebForms: Create the investments form webforms
- Investments: Desinvestment action
    - Decide when apply 4%
    - Warn when too many desinvestments for the year
    - Decide policy with effective dates
    - Decide policy with rigths caducity
- Investments: Transfer action
    - Decide policy with effective dates
    - Decide policy with rights caducity
- Introduce new assignations constraints
- OV: List investments
- OV: List assignations
- OV: Assignation editor
- OV: Stats and graphs: accomulated, used (by X), and about to expire rights
- OV: Sencondary market of shares
- Invoice: Include more info


## DONE

+ Make assignation test resilent to changes on contract annual use [Cesar]
+ Filter invoices by having generation or not [Gisce]
+ Security: add users to generationkwh group
+ Security: add users to plantmeter group
+ Testing invocing
+ Testing production import
+ Init:
    + Setup plants
    + First remainder
        + Reminder Migration: a reminder for 1-shares curve
        + Reminder Migration: a reminder for known to be used n-shares (optional)
    + Inicialitzar preus Genkwh (a ma)
+ Testing scripts: Create investments
+ Testing scripts: Create assignments
+ Testing scripts: Init: initial date, 1-shares remainder
+ Testing scripts: Additional init for n-shares remainders
+ Testing scripts: Inject flat production for several days (without plants)
+ Testing scripts: Inject csv production for several days (without plants)
+ Testing scripts: Inicialitzar preus per a proves (a ma)
+ Testing scripts: Show rights and other curves
+ `genkwh_assigment`default --all: consider active flag and other states
+ Assignments Script: `--until date` filters out members with no investment effective that date
+ Assignments Script: `--mail` sends mail option
+ Generate the first investment batch at production
+ Accounting: review desinvestments and returned payments on first batch
+ Assignation proposal for the first investment batch and email sending
+ Include the member code into the mail template for default assignment
+ Investment: negative move line: activation date should be the same or inmediate? -> They are deactivated by hand
+ Use xml for the mail template so we can reference model data id instead of id number
+ Rename assignment.isActive -> assignment.anyForContract
+ Catalan translation of Assignment model strings
+ Default assignment mail: include the member id on subject to easy support tasks when receiving answers
+ Default assignment mail: upload to production and tests
+ Assignment: log modifications into soci observations
+ Access to new models to all ERP users
+ Generation flag column at invoice tree to display whether has generation enabled
+ Member tree: include the 'Default assignment mail sent' flag
+ En el wizard que crees una nova assignació en una fitxa de soci, el membre per defecte que d'aparèixer és el soci en qüestió i que aquest no es pugui canviar.
+ Member flag: whether the default assigment mail has been sent
    + Adding it to the model [gisce]
    + Mail Callback sets it [gisce]
+ Quan s'escrigui al generation del soci, sempre lo més nou és el que s'escriu primer.
+ Rename tree "Informació GKWH del soci" to "Socis amb generation kWh"
+ Member Generation tab: "precisio" -> "previsió"
+ Assignment: update priority overwritting write?? -> No, use log
+ Investment: review who uses `active_investments` and consider `effective_for_member` similar implementation
+ Investment: review dupliation among `create_from_account` and `create_for_member`
+ Rename `generationkwh_api` -> `som_generationkwh`
+ Rename `plantmeter_api` -> `som_plantmeter`
+ Investment: create by member
+ Investment: properly test active flag
+ Script to feed testing (and real?) production
+ ProductionLoader tests working again
+ ProductionLoader use dates
+ Cas: Factura contracte amb assignacions de membres que no tenen inversions effectives, no hauria de sortir linia generation
+ Assignment: Wizard per canviar flag active des del tree [gisce]
+ Annual use (see card board)
+ Invoice visual design implementation [gisce]
+ Compose default assignation mail
+ Mako implementation for default assignation mail
+ Invoice visual design wireframe
+ Assignment: Script: --all flag for default
+ Investment: test activate and move it from erppeek to erp
+ Investment: `active` field to hide failed payments (the original one and the refund) [Agusti]
+ Investments: Wizard to disable them in batch from tree [Agusti]
+ Investments: Wizard to disable them from form [Agusti]
+ Investments: Evaluate implications of active flag on Investment usagea
+ Investment: rename `de/activation_date` -> `first_effective_date`
+ Investment: activate considered in listActive
+ Investment: init considers already existing but also inactive
+ Refund to a member that does not exist -> not refunded
+ RemainderProvider: More semantics to method names (set,get -> updateRemainders, lastRemainders)
+ Dealer: `refund_kwh` integration test
+ DealerAPI: `refund_kwh` (id mapping)
+ Assignment: Script: assign command
+ Assignment: Script: test expire command
+ Dealer.isActive(contract) returns true if contract has any assignment right now [Cesar]
+ DealerAPI.isActive(contract) returns true if contract has any assignment right now [Cesar]
+ Assignment.isActive(contract) returns true if contract has any assignment right now [Cesar]
+ Dealer.`use_kwh`: Retornar els consums tot i que siguin 0 per un member [Cesar]
+ Assignment: Script: id conversion
+ datetime review: Use dates instead local datetimes wherever we can
    + RightsPerShare receives date (and uses datetime with mongotimecurve)
    + MemberRightCurver receives date (and still sends local to ActiveShareCurve)
    + MemberShareCurve uses date
    + InvestmentProvider: uses date
    + genkwh-investment list sends dates as strings instead of local
    + FarePeriod uses dates
    + MemberRights usage uses dates
    + UseTracker uses dates
    + Remainders uses dates
    + Dealer uses dates
+ DealerAPI: Convert `soci_id` from and to `partner_id` [David]
+ FarePeriodCurve: Use numpy arrays
+ FarePeriodCurve: Date parameter should be dates not strings
+ Contrast API usage from invoice with actual API
+ Assignment: rewrite create, call expire, then super, deprecate add
+ FarePeriodCurve: Fares dictionary should be at libfacturacioatr
+ FarePeriodCurve: Include all fares !!!!!!!
+ Verify invoicing refund should not depend on isActive: if it has genkwh lines, refund should be ok
+ Assignment: Filter out inactive contracts and others (ask Pere)
+ Dealer: `use_kwh`
+ Dealer: `refund_kwh`
+ AssignmentSeeker becomes Dealer
+ Investment: backref to the account lines
+ Investment: protect againts regenerating already generated account lines
+ Investment: Change `member_id` relation from partner to soci
+ Investment: create receives as parameter `partner_id` instead `soci_id`
+ Assignment: Filter out expired assignments when seeking
+ Assignment: Expired ones do not constraint the date
+ Assignment: Default assignment: query with all sorted contracts for a set of members
    + Incorporate the query
    + Adapt results to the expected ones
    + Split test cases
    + Sort by annual use
    + Integrate both functions
+ Assignment: Default assignment: given previous list create the assignment with proper priorities
+ Remainders: What to do with n-share right curve not yet started:
	+ Add Remainder method (startTrackingRights?) to add a 0 kW remainder at production start for n-shares if there is no remainder yet
	+ When invoicing, if nshares has no reminder, call startTrackingRights, so next time we load production will be computed, and use 1-share multiplied instead
	+ Make generationkwh.rightspershare.RightsPerShare.rightspershare resilent to those cases
+ Locate and fix the found problem in tested batch
    + Fix: 32 limit on choose
    + Fix: 3.0 P4-P5-P6 not used in P1-P2-P3
+ Traduir Mail Premi
+ Definir grups enviament segons data enviament vs data efectiva
    + Grup 1: fins el dia que s'envii
    + Grup 2: fins el 2016-04-26
+ Muntar template
+ Redactar versio sense maquina del temps
+ Traduir sense maquina del temps
+ Posar la data efectiva de tots
+ Introduir els preus a produccio
+ Escriure script d'enviament
    + Seleccionar els socis que han invertit abans de 2016-04-26
    + Funcio per enviar el correu
+ Enviar correu
+ Modificar el mail d'assignacio per que inclogui la data effectiva
+ Posar la data effectiva a totes les inversions comprovades
+ Cron: Create default assignment for investment a month about becoming effective and send an email


