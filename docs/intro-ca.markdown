# Introducció als conceptes rera el Generation kWh


## Què és el Genkwh?

- Una forma d'invertir en renovables que en comptes
donar-te dret a un interés et dona dret a consumir els
kWh que produeixen les plantes a preu de cost.

- Sobre els preus de l'energia:
	- Aquest preu dels kWh Generation es fixarà cada any a l'assemblea segons els costos reals de manteniment que preveiem
	- És un preu que normalment és més barat; no pateix la bufada de la subasta del mercat elèctric
    - TODO: Quina es la diferència estimada:
        - impacte en el preu sense peatges (de mercat),
        - impacte en el preu de la part d'energia (amb peatges),
        - impacte a una factura amb consum i potència típiques

## Com funciona la inversió

- És una inversió a 25 anys: un any de carència i 24 efectius.
- El primer any de carència serveix per donar temps a que es construeixin plantes noves amb aquests diners.
- Passat l'any de carència, es comencen a generar drets a kWh
- També passat aquest any de carència es comença a tornar el prèstec (la veinticuatrena part cada any, sense interessos)
- Les inversions es fan en accions de 100€
- Cada nova planta que es posa en marxa afegeix el seu cost de construcció al total del valor del Generation kWh.
- Dels kWh generats cada hora per les plantes del Generation kWh, cada inversor rep la mateixa proporció que en té d'accions respecte al valor total del projecte.

## Com veiem l'equip les inversions a l'ERP

- Al menu `Generation kWh/Inversions Generation kWh` tenim la llista de totes les inversions
- Al menu `Generation kWh/TODO` veiem la llista de les inversions de cada soci
- Cada inversio te un numero d'accions, una data de compra i 
- La data de compra no és quan s'omple el formulari sinó quan es fa la remesa.

TODO: ficar pantalladas


## Com reparteixo els kwh que genera la meva inversió (Assignacions)

- Les inversions van lligades als socis, no pas als contractes
- Per poder-se'n beneficiar, cal que estiguin assignades a contractes receptors dels kWh
- Es pot assignar qualsevol contracte de SomEnergia
- **Per defecte s'assignen a tots els contractes on el soci és pagador o titular**

## Prioritzant els contractes entre ells

- Hi ha la possibilitat de donar prioritat a uns contractes respecte d'altres
- Els contractes amb menys prioritat s'esperen a que tots els contractes amb més prioritat hagin facturat el període on s'han generat els kWh
- Dintre d'una mateixa prioritat, el primer contracte que factura s'emporta els kWh.
- **Per defecte es posa com a prioritari el contracte amb més consum anual dels que esta com a pagador, o sinó hi ha de pagador, el de més consum que està com a titular**
- La resta de contractes on el soci es pagador o titular es posen al següent nivell i agafaran tot el que el principal no agafi.

## Com veig les assignacións a l'ERP

TODO: ficar pantallades

## Cosetes que ens trobarem

- En esborrar una factura i tornar-la a generar, hi ha una petita possibilitat que l 'import no coincideixi si els kWh Generation disponibles son diferents, p entremig altres contractes assignats pel soci fan factures.
- Els kWh s'agafen al mateix període que es produeixen, és normal que un contracte 2.0DH no tingui generation a P2 mentres tinguem nomes fotovoltaica.








