Domain Criteria
===============

This file holds a log of statements that capture conclusions on discussions with the stakeholders about the domain and the functionality.

People involved in the discussion are [marked within brackets].

**Embrace the change: These are not immutable laws. Just a log to know who you are to talk if you consider them wrong.**


Invoices
--------

- Generation kWh Line Product Name format 'Pn Gkwh' [Marc-Agusti]
- Even when a contract hasn't got GkWh shares, the invoice line is created, with quantity 0 [Marc-Agusti]

Production and shares
---------------------

- Production must be divided by the total shares of each activated plant. [Nuria-David]
	- Not by the total of active owned shares. [Nuria-David]
	- Not all the production has to be dealt if not all shares have been bought [Nuria-David]
- Plants are activated for generation at an arbitrary date. [Nuria-David]
- There is no deactivation date for plants (by now, to be reconsidered later). [Nuria-David]
- Activation date for owned shares is fixed by adding a given number of days (delay, _carencia_) to the purchase date [Nuria-David]
- Delay can be different for share batches. Batches can be set either
	- by selecting by purchase date (between two dates) or
	- by purchasing order (till the nth action). [Nuria-David]

Doubts
------

- DOUBT: [David] Do shares expire a number of years after the purchase date or after the activation date?
- DOUBT: [David] Can a plant be activated before metering is available? Consequences?
- DOUBT: [David] Can a plant be activated after metering is available? Consequences?









