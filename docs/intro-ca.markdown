# Introducció als conceptes rera el _Generation kWh_


## Què és el Genkwh?

- Una forma d'invertir en renovables que,
en comptes donar-te dret a un interès,
**et dona dret a fer servir els kWh que produeixen les plantes a preu de cost**.


## Com funciona? (molt resumit)

- Els socis fan **inversions** per construir plantes
	- es retornen en 25 anys
	- sense interessos
	- amb un any de carència
- Un cop construïdes, els kWh que van produint les plantes esdevenen **drets** d'ús de kWh pels inversors, proporcionalment a la seva inversió.
- Aquests drets es reparteixen a diferents contractes segons les **assignacions** que hagi definit l'inversor.
- A la factura d'aquests contractes, apareixerà una part de l'energia a **Preu Generation kWh** i una altra part a preu de mercat.


## Quin és el preu _Generation kWh_?

- Aquest preu dels kWh Generation es fixarà cada any a l'assemblea segons els costos reals d'amortització i de manteniment que preveiem
- És un preu que **esperem que sigui** més barat, donat que no pateix la bufada especulativa de la subasta del mercat elèctric
- TODO: Quina és la diferència estimada aquest any:
	- impacte en el preu de mercat (sense peatges)
	- impacte en el preu de la part d'energia (amb peatges),
	- impacte a una factura mitjana (comptant energia i potència mitjana)


## Com funciona la inversió? (Inversions)

- Les inversions es fan en **accions** de 100€
- És una inversió a 25 anys: un any de **carència** i 24 **efectius**.
- El primer any de carència serveix per donar temps a que es construeixin plantes noves amb aquests diners.
- Passat l'any de carència, es comencen a generar drets a kWh
	- Són 24 anys beneficiant-se de la producció de les plantes
- També passat aquest any de carència es comença a tornar el prèstec
	- El primer any, el de carència, no es torna res
	- El segon any es torna el corresponent al primer any i al segon: 8€/acció
	- Els 23 anys restants es tornen 4€/acció, fins tornar els 100€/acció
	- TODO: Confirmar que el retorn de l'any de carència es fa l'any 2 i no el 25


## Quants kWh li toquen a cada inversor? (Drets)

- Cada nova planta **que es posa en marxa** afegeix el seu cost de construcció al _valor total del Generation kWh_.
- De la producció real que generin les plantes,
	- ens correspondran els kWh proporcionals a la relació entre
		- les nostres accions i,
		- el _valor total del Generation kWh_.
- Els kWh s'acomulen en forma de **drets**
	- es poden fer servir durant tot **un any** abans que no caduquin.
- Els drets tenen dia i hora de producció
	- Una factura amb **discriminació horària** només pot gastar drets produïts al mateix període (P1, P2...) en el que es van generar.
		- Per exemple, és normal que un contracte 2.0DHS no tingui Generation a P3 (nocturn) mentre tinguem només fotovoltàica.


## Quines dates defineixen la vida d'una inversió? (Dates efectives)

- Cada inversió tè certes dates significatives:
	- **Data de comanda:** quan s'omple el formulari. **No la tenim en compte!**
	- **Data de compra:** quan es fa la remesa. Es considera que hi comencen els 25 anys.
	- **Primera data efectiva:** a partir de quan comença a rebre la producció
		- normalment 1 any despŕes de la compra
		- mentre no posem cap valor a l'ERP, no serà efectiva mai
	- **Darrera data efectiva:** la darrera data on es rep producció
		- normalment 25 anys després de la compra
		- mentre no posem cap valor a l'ERP, no deixarà de ser efectiva mai

## Com veiem l'equip les inversions a l'ERP

- Al menu `Generation kWh/Inversions Generation kWh` tenim la llista de totes les inversions
	- Comptabilitat la fa servir per fer neteja (desactivar) les inversions que no ho són.
	Són desinversions, balanços, remeses retornades...
	que no sabem identificar de forma automàtica i cal fer-ho a mà.
- Generalment farem servir millor la pestanya `Generation kWh` del soci:
	- Només apareix la pestanya si el soci té inversions
	- La podem trobar a:
		- Menú `Generation kWh/Socis amb Generation kWh`
		- Menú `Empreses/Socis`

TODO: ficar pantallades

TODO: Explicar els altres camps del resum generation


## Com es reparteixen els kwh que generen les inversions d'un soci? (Assignacions)

- Les inversions van lligades als socis, no pas als contractes
- Per poder-se'n beneficiar, cal que estiguin assignades a contractes receptors dels kWh
- **Per defecte s'assignen a tots els contractes on el soci és pagador o titular**
- Es pot assignar qualsevol contracte de SomEnergia
	- **No** cal que l'inversor en sigui titular, pagador o soci.
	- Un mateix contracte podria rebre kWh de diferents inversors


### Prioritzant els contractes entre ells

- Hi ha la possibilitat de donar prioritat a uns contractes respecte d'altres
- Els contractes menys prioritaris no poden fer servir kWh produïts en dies que encara no hagin facturat els més prioritaris.
- Dintre d'una mateixa prioritat, el primer contracte que factura s'emporta els kWh.
- **Per defecte es posa com a prioritari el contracte amb més consum anual dels que esta com a pagador, o sinó hi ha de pagador, el de més consum que està com a titular**
- La resta de contractes on el soci és pagador o titular es posen al següent nivell i agafaran tot el que el principal no agafi d'entrada.


### Es pot controlar més com repartir els drets?

- De moment no.
- Hem optat començar per una opció molt simple d'implementar que permeti certa flexibilitat.
- Les factures dels diferents contractes arriben sense cap ordre, es refacturen, s'anul·len...
	- Tot això, fa que sigui costós de implementar i executar (lent) repartiments, que poden semblar senzills com ara percentatges.
- Hi ha diverses possibles polítiques, encara hem de veure quina és la que interessa més als inversors.
- Esperarem que passin uns mesos i veiem com es fa servir o a que hagi una certa demanda d'algun tipus de restricció per implementar-la.


### Com poden els inversors canviar les seves assignacions?

- De moment, poden demanar canvis per email a <generationkwh@somenergia.coop>
- Nosaltres, en rebre els mails, haurem d'editar les assignacions amb l'ERP.
- Més endavant, ho podran fer ells mateixos via Oficina Virtual. De moment, no.


### Com veig i edito les assignacións a l'ERP?

- Com les inversions, les podem veure des de una vista general o desde Soci
- Les assignacions es poden crear, eliminar o editar (la prioritat) com altres objectes de l'ERP (lectures...)
- Totes les accions que fem amb les assignacions quedaran registrades a les observacions a la part inferior.

TODO: ficar pantallades


### Les primeres inversions estan _premiades_. Què vol dir?

- Hem decidit premiar als primers inversors avançant la data efectiva un mes.
	- La planta d'Alcolea ja fa unes semanes que està produint.
- Començaran a fer factures Generation quan estava previst, però tindran la producció d'aquest mes acomulada.


## Factures Generation

- Quan fem una factura, serà Generation:
	- Si el contracte té assignacions
	- Si cap inversió assignada és efectiva a dins del periode de facturació.

- A la factura impresa s'identifica pel logo a la primera pàgina

TODO: Pantallada de la capcelera amb el logo

- A la llista de factures, un nou check indica si la factura té Generation.

TODO: Pantallada de la llista de factures

- A les línies de detall de la factura apareixen línies generation que indiquen el soci que ha fet la inversió.

TODO: Pantallada del detall d'una factura


## Generation kWh Master

### Inversors que han fet succesives inversions

- Si un inversor fa inversions en diferents dates, les dates efectives de cadascuna són independents.
- Exemple:
	- Si jo inverteixo:
		- Inversió 1: 1000€ el 2015-01-01
		- Inversió 2: 2000€ el 2015-02-01
	- tindré:
		- 0 accions efectives fins el 2015-12-31
		- 10 accions efectives a partir del 2016-01-01 <- Inversió 1 efectiva
		- 30 accions efectives a partir del 2016-02-01 <- Inversió 2 efectiva
		- 20 accions efectives a partir del 2030-01-01 <- Inversió 1 deixa de ser efectiva
		- 0 accions efectives a partir del 2030-02-01 <- Inversió 2 deixa de ser efectiva
		- Encara podré estar gastant kWh acomulats fins el 2031-12-31

### Contractes amb més d'una font de drets Generation

- Un mateix contracte podria rebre drets de més d'un inversor, si així ho configuren
- Cada font tindrà línies de factura 
- De moment no hi ha cap criteri per escollir d'on agafar primer els drets
	- S'agafen tots els que drets d'una font arbitrària i si no hi ha prou, s'agafen de la següent

TODO: Pantallada factura multi-font


### Cancelant, abonant i rectificant factures Generation

- Un esborrany amb Generation està reservant kWh que no poden fer servir altres factures
	- **Compte amb deixar factures en esborrany si són Generation**, estan reservant drets
- Quan esborrem un esborrany es retornen els drets a les seves fonts.
- El mateix passa quan abonem i rectifiquem
	- les abonadores retornen
	- les rectificadores tornen a reservar
- Si entre que abonem i rectifiquem, canvia la disponibilitat dels drets, **és possible que els conceptes de la factura varïin**.


### Com funciona la caducitat dels drets?

- Quan es cerquen drets es considera una finestra que inclou el periode de facturació i un any enrera (un any i un mes)
- Per evitar que es caduquin:
	- Es gasten sempre els drets més antics no caducats.
	- Es retornen els drets usats més nous
- Quan hi hagi drets a pocs mesos de caducar-se, enviarem un mail avisant a l'inversor per si vol fer una assignació addicional.



## Glossari

- Inversió: diners que soci dóna per fer plantes.
- Acció Energètica: paquet de 100€ en els que es divideix una inversió
- Valor construït: cost de construcció de les plantes que estan produint en un moment.
- Dret: energia (kWh) que un soci pot fer servir perquè ha estat produït per les plantes.
- Dates efectives: dates en que la inversió genera drets.
- Assignació: dessignació d'un contracte com a receptor dels drets d'un soci.
- Font: Soci que aporta a un contracte els seus drets






