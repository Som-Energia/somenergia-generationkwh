- ProductionToRightsPerShare: Protect againts divby0 when total active actions is zero
- Investment: backref to the account lines
- Investment: protect againts regenerating already generated account lines
- Investment: Change member_id relation from partner to soci
- Investment: Janitoring: mode lines without partner
- Investment: Janitoring: mode lines without datesa
- Investment: negative move line: activation date should be the same or inmediate?

- Remainders: What to do with n-share right curve not yet started:
	+ Add Remainder method (startTrackingRights?) to add a 0 kW remainder at production start for n-shares if there is no remainder yet
	+ When invoicing, if nshares has no reminder, call startTrackingRights, so next time we load production will be computed, and use 1-share multiplied instead
	- Ensure that 1-shares curve is always started like that
	- At init call startTrackingRights for used curves we know exist
	+ Make generationkwh.rightspershare.RightsPerShare.rightspershare resilent to those cases

- Assignment: Filter out inactive contracts and others (ask Pere)
- Assignment: Given a contract that can consume rights from several members, define the order in which it should consume them.
    - Right now is an arbitrary order, not bad
    - Rare case, low priority, wait for actual cases

- FarePeriodCurve: Fares dictionary should be at libfacturacioatr
- FarePeriodCurve: Include all fares
- FarePeriodCurve: Use numpy arrays
- FarePeriodCurve: Where to get holidays?
- FarePeriodCurve: Date parameter should be dates not strings

- BUG: Mongodb erp integration: reconnections do not refresh connection attr


