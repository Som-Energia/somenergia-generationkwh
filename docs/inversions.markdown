# Domain Analysis on investments


- Three kinds of investments:
    - GenerationkWh (_Accions Energetiques_, AE)
    - _Aportacions voluntaries al capital social_ (Aportacions)
    - _Títols participatius_ (Titols)


## Accions energètiques (Generation kWh)

![Energetic Actions States](inversions-states-generation.png)


- 25 years loan to the cooperative
- 0% interest
- Yearly amortization (4%), depending on the purchase date
- First year (waiting period) has no amortization
- Last year has double amortization
- Quantized to 100€ (Accio energetica)
- TODO: Maximum? Per campaign?

- Rights:
    - Investor obtain right to get kWh at special price
    - Available kWh are proportional to actual plant production and effective AE's
    - During the waiting period, there are no production rights
    - Production rights are kept for a year to be used
    - Special prices is fixed every June in the Assembly along with regular prices.
    - Changes in the number of effective AE's apply to the daily production.


### Operations

- Apply: Filling and sending the form
- Bank charge: We send the payment order to the bank.
    - In current implementation this is the "purchase date"
- Bank return:
    - Bank notifies us, the charge could not be done
    - AE's become draft again until we charge again
- Expire:
    - 25 years 
- Transfer:
    - The rights are transfered to a new user
    - No penalty is applied
    - For the emitter is a Divestment with no penalty.
    - The receiver has no waiting period
    - The receiver inherits the expiration date
    - Rights generated up to the transfer date remain for the emitter
    - Rights generated since the transfer date belong to the receiver
- Inheritance
    - Managed like a transfer among members
    - Old rights can be assigned by hand to the proper contracts until exhausted
- Early divestment:
    - During the wating period
    - No penalties applied
- Regular divestment
    - After the waiting period
    - Penalties apply: 1%-4% of the pending capital or 4€ if lower
        - (TODO: Contract says so but concrete conditions not clear)
- Amortizations:
    - Every year at the aniversary of the purchase date



## Aportaciones voluntarias


![Voluntary Contribution States](inversions-states-aportacions.png)

- Do not expire
- Has no amortization
- Give moderate interests
- You can invest and uninvest with no penalization
- Limit 25k€/member
- Investments quantize to 100€, just in form, by other means it can be unquantize
- Interest payment 31D, executed 31G
- Prorated interests depending on the investment
- The interest rate is decide on May but it is applied retroactively since January

### Operations:

- Invest
- Divest
- Inheritances
- Interest payment


## Títols participatius


### Current (5 years)


![Participation Titles States](inversions-states-titols5.png)


### Legacy (10 years)

![Old participation Titles States](inversions-states-titols10.png)


- They expire (first ones were 10years, later 5years)
- Quantized to 100€
- Limit 100k€/member
- Higher and fixed interest rate
- Interest payment 30Jun, executed first days of July
- 10 years titles can divest after 5year with no penalty
- Capital is returned on expiration
- Divest penalty: 12 months of interest taken from the returned capital
    - Interest are paid as usual on June
- TODO: How the variable interest rate affects to the penalty

### Operations

- Invest
- Divest
- Inheritances
- Interest payment
- Expiration (different)


## Ops with impact in accounting and finances


- Interest payment

    - <- proveidors (inversors) (associat a factura)
    - -> Despeses interessos
    - -> Retencions

- Amortization

    - <- compte d'inversió
    - -> bank  (TODO: associat a rebut??)

- Divestment

    - <- compte d'inversió
    - -> bank  (TODO: associat a rebut??)
    - -> penalitzacions (si n'hi hagues)

- Bank Charge / Bank Transfer

    - <- bank
    - -> compte d'inversió (TODO: associat a una remesa o payment line?)

- Bank Return

    - <- compte d'inversió
    - -> bank
    - TODO: Despeses bancaries?


## Glossary

- Interest payment: Liquidación de intereses
- Investment: Inversión
- Divestment: Desinversion
- Inheritance: Herencia
- Expire: Vencer
- Prorate: Prorateo
- Penalty: Penalizacion
- Loan: Prestamo
- Transfer: traspaso
- Waiting period: periodo de carencia
- Amortization: Amortizacion, devolver el capital
- Bank return: devolución bancaria



