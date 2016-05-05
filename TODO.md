# TODO's

## Inmediate TODO's

+ DealerAPI: Convert `soci_id` from and to `partner_id` [David]
- Dealer: `refund_kwh` test
- DealerAPI: `refund_kwh`
- Assignment.isActive(contract) returns true if contract has any assignment right now [Cesar]
- Dealer.isActive(contract) returns true if contract has any assignment right now [Cesar]
- DealerAPI.isActive(contract) returns true if contract has any assignment right now [Cesar]
- Investment: `active` field to hide failed payments (the original one and the refund) [Agusti]
- Investments: Wizard to disable them in batch from tree [Agusti]
- Investments: Wizard to disable them from form [Agusti]
- Investments: Evaluate implications of active flag
- Dealer.`use_kwh`: Retornar els consums tot i que siguin 0 per un member [Cesar?]
- Rename `generationkwh_api` -> `som_generationkwh`
- Rename `plantmeter_api` -> `som_plantmeter`
- datetime review: Use dates instead local datetimes wherever we can
    + RightsPerShare receives date (and uses datetime with mongotimecurve)
    + MemberRightCurver receives date (and still sends local to ActiveShareCurve)
    + MemberShareCurve uses date
    + InvestmentProvider: uses date
    + genkwh-investment list sends dates as strings instead of local
    + FarePeriod uses dates
    - MemberRights usage uses dates
    - UseTracker uses dates
    - Remainders uses dates
    - Dealer uses dates
- Assignment: update priority overwritting write?? (Low)
- Assignment: log in soci observations
- Investment: test activate and move it from erppeek to erp
- Assignment: Script: add command
- Assignment: Script: test expire command
- Assignment: Script: id conversion


## Unscheduled TODO's

- ProductionToRightsPerShare naive: Protect againts divby0 when total active actions is zero
- Investment: ondelete -> member
- Investment: Janitoring: mode lines without partner
- Investment: Janitoring: mode lines without dates
- Investment: negative move line: activation date should be the same or inmediate?
- Investment: constant for the account root for generationkwh accounts
- Investment: constant for the number of digits for the soci code in accounts
    - Can be found at `ir_secuence.code="socis"`

- Reminder Migration: a reminder for 1-shares curve
- Reminder Migration: a reminder for known to be used n-shares (optional)

- Assignment: ondelete -> polissa
- Assignment: ondelete -> member
- Make assignation test resilent to changes on contract annual use
- Assignment: Change priority expires assigments and creates new
- Assignment: Send an activation mail explaining default assignment

+ FarePeriodCurve: Use numpy arrays
+ FarePeriodCurve: Date parameter should be dates not strings

- BUG: Mongodb erp integration: reconnections do not refresh connection attr
- Review dates management across interfaces
- Security: add users to generationkwh group
- Security: add users to plantmeter group
- Refund to a member that does not exist


## Postponed for Next Iteration

- Invert the investment creation flux: webform -> draft investment -> payment -> active investment
- Assignment: Given a contract that can consume rights from several members, define the order in which it should consume them.
    - Right now is an arbitrary order, not bad
    - Rare case, low priority, wait for actual cases
- WebForms: Create the soci
- WebForms: Create the investments form webforms


## DONE

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



