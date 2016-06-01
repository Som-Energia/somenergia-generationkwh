# Introducció als conceptes rera el _Generation kWh_


## Què és el Genkwh?

- Una forma d'invertir en renovables que,
en comptes donar-te dret a un interès,
**et dóna dret a fer servir els kWh que produeixen les plantes a preu de cost**.


## Com funciona? (molt resumit)

- Els socis fan **inversions** per construir plantes
	- es retornen en 25 anys
	- sense interessos
	- amb un any de carència
- Un cop construïdes, els kWh que van produint les plantes esdevenen **drets** d'ús de kWh pels inversors, proporcionalment a la seva inversió.
- Aquests drets es reparteixen a diferents contractes segons les **assignacions** que hagi definit l'inversor.
- A les factures d'aquests contractes, apareixerà una part de l'energia a **Preu Generation kWh** i una altra part a preu de mercat.


## Quin és el preu _Generation kWh_?

- Aquest preu dels kWh Generation es fixarà cada any a l'assemblea segons els costos reals d'amortització i de manteniment que preveiem
- És un preu que **esperem que sigui** més barat, donat que no pateix la bufada especulativa de la subasta del mercat elèctric


## Com funciona la inversió? (Inversions)

- Les inversions es fan en **accions** de 100€
- És una inversió a 25 anys: un any de **carència** i 24 **efectius**.
- El primer any de carència serveix per donar temps a que es construeixin plantes noves amb aquests diners.
- Passat l'any de carència, es comencen a generar drets a kWh durant els 24 anys que queden d'inversió.
- També passat aquest any de carència es comença a tornar el prèstec
	- El primer any, el de carència, no es torna res
	- El segon any es torna el corresponent al primer any i al segon: 8€/acció
	- Els 23 anys restants es tornen 4€/acció, fins tornar els 100€/acció
	- TODO: Confirmar que el retorn de l'any de carència es fa l'any 2 i no el 25


## Quants kWh li toquen a cada inversor? (Drets)

- Quan **es posa en marxa** cada nova planta, s'afegeix el seu cost de construcció al **valor total del _Generation kWh_**.
- De la producció real que generin les plantes,
	- ens correspondran els kWh proporcionals a la relació entre
		- les nostres accions i,
		- el _valor total del Generation kWh_.
- Els kWh s'acomulen en forma de **drets**
	- es poden fer servir durant tot **un any** abans que no caduquin.


## Cicle de vida d'una inversió? (Dates efectives)

- Cada inversió tè certes dates significatives:
	- **Data de comanda:** quan s'omple el formulari. **No la tenim en compte!**
	- **Data de compra:** quan es fa la remesa. Es considera que hi comencen els 25 anys.
	- **Primera data efectiva:** a partir de quan comença a rebre la producció en forma de drets
		- normalment 1 any després de la compra
		- mentre no posem cap valor a l'ERP, no serà efectiva mai
	- **Darrera data efectiva:** la darrera data on es rep producció
		- normalment 25 anys després de la compra
		- mentre no posem cap valor a l'ERP, no deixarà de ser efectiva mai
	- Els drets caduquen en un any, o sigui que és possible que encara es consumeixin kWh Generation un any després de la darrera data efectiva.

## Com veiem l'equip les inversions a l'ERP

- Les opcions del Generation estan una mica amagades:

![On trobar al menu les opcions del Generation kWh](pantallades/genkwh-menu.png)

- Al menu `Generation kWh/Inversions Generation kWh` tenim la llista de totes les inversions
    - Veure les que han anat entrant
    - Per localitzar i desactivar les que s'han desinvertit (Comptabilitat)
    - (Futur) Botó per generar assignacions per defecte per les noves

![Llistat d'inversions](pantallades/inversions.png)

- Generalment farem servir millor la pestanya `Generation kWh` del soci:
	- Només apareix la pestanya si el soci té inversions
	- La podem trobar a:
		- Menú `Generation kWh/Socis amb Generation kWh`
		- Menú `Empreses/Socis`

![Pestaña Generation kWh del soci](pantallades/socis_form.png)


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


### Com poden els inversors canviar les seves assignacions?

- De moment, poden demanar canvis per email a <generationkwh@somenergia.coop>
- Nosaltres, en rebre els mails, haurem d'editar les assignacions amb l'ERP.
- Més endavant, ho podran fer ells mateixos via Oficina Virtual. De moment, no.


### Com veig i edito les assignacións a l'ERP?

- Com les inversions, les podem veure des de una vista general o desde Soci
- Les assignacions es poden crear, eliminar o editar (la prioritat) com altres objectes de l'ERP (lectures...)
- Totes les accions que fem amb les assignacions quedaran registrades a les observacions a la part inferior.


## Factures Generation

- Quan fem una factura, serà Generation:
	- Si el contracte té assignacions
	- Si cap inversió assignada és efectiva a dins del periode de facturació.

- A la factura impresa s'identifica pel logo a la primera pàgina

![Logo a la factura](pantallades/factura-header.png)

- A la llista de factures, un nou check indica si la factura té Generation.

![Nova columna a la llista de factures](pantallades/llista-factures-tegeneration.png)

- A les línies de detall de la factura apareixen línies generation que indiquen el soci que ha fet la inversió.

![Linieas de factura Generation](pantallades/factura-detall.png)


## Procediments

### Com funcionarem normalment

- Els inversors omplen el formulari d'inversió
- El sistema deixa una línia de pagament amb la remesa
- Quan comptabilitat envia la remesa es genera un apunt comptable
- Cada nit es revisen els nous apunts comptables, els que siguin de comptes generation generen una inversió pendent de revisar
- Comptabilitat revisa les inversions i neteja les retornades, o els moviments de desinversió
- Quan falta un més per la primera data efectiva, s'envia un correu a l'inversor amb una proposta d'assignació
- Els inversors poden contestar per correu per modificar la proposta
- Nosaltres aplicarem les modificacions amb el client ERP


### Com funcionarem en el futur (alguns dels canvis previstos)

- El camí Formulari -> Linia de pagament -> Apunt Comptable -> Inversió es tornarà Formulari -> Inversió Esborrany -> Linia de Pagament -> Apunt Comptable -> Inversió activa
- La revisió de les devolucions es seguirà fent a mà, però, en el moment de la devolució.
- Les modificacions de les assignacions es podran fer via l'Oficina virtual.
- Incorporarem algun element més de control sobre les assignacions segons reaccionin els inversors.


### Les primeres inversions estan _premiades_. Què vol dir?

- Hem decidit premiar als primers inversors avançant la data efectiva un mes.
	- La planta d'Alcolea ja fa unes setmanes que està produint.
- Començaran a fer factures Generation quan estava previst, però tindran la producció d'aquest mes acomulada.


### Els primers dies del Generation

- La primera remesa
	- va ser el 2016-06-22,
	- és de gaire be 400 persones, son bastantes
	- enviarem les propostes d'assignació per aquestes 400 dilluns
	- aquesta setmana veurem si podem gestionar els canvis
	- si ho hem pogut fer a finals de setmana, activarem la facturació Generation per aquestes persones
		- ho farem fixant la data efectiva aquell dia
		- però la data efectiva serà el 2016-05-22


## Generation kWh Master

### Inversors que han fet succesives inversions

- Si un inversor fa inversions en diferents dates, les dates efectives de cadascuna són independents.
- Exemple:
	- Si jo inverteixo:
		- Inversió 1: 1000€ el 2015-01-01
		- Inversió 2: 2000€ el 2015-02-01
	- tindré:
		- 0 accions efectives fins el 2015-12-31
		- 10 accions efectives a partir del 2016-01-01 <- Inversió 1 comença a generar drets
		- 30 accions efectives a partir del 2016-02-01 <- Inversió 2 comença a generar drets
		- 20 accions efectives a partir del 2030-01-01 <- Inversió 1 deixa de generar drets
		- 0 accions efectives a partir del 2030-02-01 <- Inversió 2 deixa de generar drets
		- Encara podré estar gastant kWh acomulats de la inversió 1 fins el 2031-12-31
		- Encara podré estar gastant kWh acomulats de la Inversió 2 fins el 2031-01-31

### Contractes amb més d'una font de drets Generation

- Un mateix contracte podria rebre drets de més d'una persona inversora (**font**), si així ho configuren
- Cada font tindrà línies de factura independents al detall de la factura
- Cada línia de factura Generation indica el nom de la font
- De moment no hi ha cap criteri per escollir d'on agafar primer els drets
	- S'agafen tots els que drets d'una font arbitrària i si no hi ha prou, s'agafen de la següent

TODO: Pantallada factura multi-font


### Contractes amb discriminació horària

- Els drets tenen dia i hora de producció
- Una factura amb **discriminació horària** només pot gastar drets produïts al mateix període (P1, P2...) en el que es van generar.
- Per exemple, és normal que un contracte 2.0DHS no tingui Generation a P3 (nocturn) mentre tinguem només fotovoltàica.
- A la factura apareixen diferenciats els periodes Generation tot i que **el preu Generation és el mateix per tots els períodes**.


### Cancelant, abonant i rectificant factures Generation

- Un esborrany amb Generation està reservant kWh que no poden fer servir altres factures
	- **Compte amb deixar factures en esborrany si són Generation**, estan reservant drets
- Quan esborrem un esborrany es retornen els drets a les seves fonts.
- El mateix passa quan abonem i rectifiquem
	- les abonadores retornen
	- les rectificadores tornen a reservar
- Si entre que abonem i rectifiquem, canvia la disponibilitat dels drets, **és possible que els conceptes de la factura varïin**.


### Com funciona la caducitat dels drets?

- Quan es cerquen els drets disponibles, es considera una finestra de temps que inclou el periode de facturació i un any enrera (un any i un mes)
- Per evitar que es caduquin:
	- Es gasten sempre els drets més antics no caducats.
	- Es retornen els drets usats més nous
- Quan hi hagi drets a pocs mesos de caducar-se, enviarem un mail avisant a l'inversor per si vol fer una assignació addicional.


### Es pot controlar més com repartir els drets a les assignacions?

- De moment no.
- Hem optat començar per una opció molt simple d'implementar que permeti certa flexibilitat.
- La complexitat d'implementar altres fórmules ve de que les factures dels diferents contractes:
	- arriben sense cap ordre
	- els periodes de facturació són diferents i canviants
	- es refacturen, s'anul·len...
- Es viable implementar altres però considerem que millor esperar el feedback dels inversors.
- Esperarem que passin uns mesos i veiem com es fa servir o a que hagi una certa demanda d'algun tipus de restricció per implementar-la.


### Es pot assignar contractes en esborrany?

- Sí, cap problema.
- Els contractes en esborrany no afecten als altres fins que no s'activen.
- Per exemple, si el posem com a prioritari, els menys prioritaris no s'esperen.


## Glossari

- Inversió: diners que soci dóna per fer plantes.
- Acció Energètica: paquet de 100€ en els que es divideix una inversió
- Valor construït: cost de construcció de les plantes que estan produint en un moment.
- Dret: energia (kWh) que un soci pot fer servir perquè ha estat produït per les plantes.
- Dates efectives: dates en que la inversió genera drets.
- Assignació: dessignació d'un contracte com a receptor dels drets d'un soci.
- Font: Soci que aporta a un contracte els seus drets






