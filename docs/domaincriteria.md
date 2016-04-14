Domain Criteria
===============

This file holds a log of statements that capture conclusions on discussions with the stakeholders about the domain and the functionality.

People involved in the discussion are [marked within brackets].

**Embrace the change:**
These are not immutable laws at all.
If you think some criteria are no longer true,
this is a log providing way to track who you need to talk to.

Invoices
--------

- Generation kWh Line Product Name format 'Pn Gkwh' [Marc-Agusti]
- A contract with Generation kWh activated, must show 'Pn GkWh' invoice lines even if assigned production is 0 kWh [Marc-Agusti]

Production and shares
---------------------

- Production must be divided by the total shares of each activated plant. [Nuria-David]
	- Not dividing by the total of active owned shares. [Nuria-David]
	- Collorary 1: when not all shares are bought, remaining production goes to the cooperative. [Nuria-David]
- Plants are activated for generation at an arbitrary date. [Nuria-David]
- There is no deactivation date for plants (by now, to be reconsidered later). [Nuria-David]
- Activation date for owned shares is fixed by adding a given number of days (delay, _carencia_) to the purchase date [Nuria-David]
- Delay can be different for share batches. Batches can be set either
	- by selecting by purchase date (between two dates) or
	- by purchasing order (till the nth action). [Nuria-David]
- [Discarded] The purchase date is the date the member orders, not the payment day [Gijsbert-Marc-Eduard]
- The purchase date is the date of the accounting movement [Marc-Eduard-Carles-Agusti-David pending of confirmation from Gijsbert]

Dealing
-------

- Dealing rights to contracts, method for the first iteration
    - All from a meeting with [Marc-Nuri-Pere-Eduard-Aleix-Agusti-David]
    - Investor members have a priority list of contracts
    - Rights are not taken if they were produced:
        - after the invoicing period end,
            - **Exemple:**
                si el dia 25 de Març fem una factura que arriba fins al 3 de Març,
                no s’utilitzarà la producció feta a partir del 4 de Març que potser
                ja tenim carregada.
        - after the last invoiced date of the other contracts in the list with higher priority
            - **Exemple:**
                Un dels inversors d’on podem treure drets
                té dos contractes mes prioritaris
                ja facturats fins els dies 2015-02-03, i 2015-02-15.
                Això implica que un contracte menys prioritari només pot fer servirs
                drets generats el 2015-02-02 o abans.
        - before a years before of the invoicing period start
            - **Exemple:**
                Una factura del periode de 3 de Juny de 2017 a 2 de Juliol,
                no pot utilitzar drets generats abans del 3 de Juny de 2016,
                aquests ja han caducat.
    - The contract list will be initialized with:
        - the biggest contract having the investor as payer
        - if none is found, the biggest contract having the investor as owner
        - left unassigned if no contracts have the investor as payer or owner
    - A mail will be sent
        - At start of generation or whenever a new investment is created
        - Telling the assignation if any by default and why
        - Telling the means to change it.
            By now mail to generationkwh@somenergia.coop + ERP operator.
            Eventually using the virtual office.
    - ERP client IF will manage this list for a given member
    - ERP client IF will display the list of investment
        - Set the activation date relative to the purchase date of many at once

- Next iterations, will address:
    - more complex deal policies (or not)
    - configuration from oficina virtual
    - a erpclient view from contract to access assigned gkwh investors

Invoice live cycle
------------------

- What to do if a refunded invoice still in draft is deleted and the 
    rights used in the original invoice are not available anymore
    or they come from different sources?
    [Carles, Eduard, David, Agusti]
    - Just try to reallocate them, if the reallocation missmatches
        in number or source, just go on with it, but generate a
        log/report about the missmatch.
        During the first months, we will check the cases and if
        the drift is too large we could reconsider
        doing something about it.


Doubts
------

- [David] Do shares expire a number of years after the purchase date or after the activation date?
- [David] Can a plant be activated before metering is available? Consequences?
- [David] Can a plant be activated after metering is available? Consequences?
- [David] Defining the time span of the plant shares. When they get extinct?
- [David] When is a contract considered to be activated for GenkWh? If active during the invoicing period?



Glossary
--------

- **Rigths:** A member's right to use a produced kWh from a GenerationkWh plant
- **Usage:** How many rights have been used by a member

















