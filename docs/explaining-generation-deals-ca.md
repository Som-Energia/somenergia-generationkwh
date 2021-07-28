# Explicant el repartiment del generation (CA)

Un dels problemes del Generation es la seva actual opacitat.
Les usuaries reben els kWh a la factura segons l'algoritme establert,
pero no tenim eines suficients per explicar
perquè han rebut més o menys kWh en una factura concreta.

Les usuaries s'acostumen a rebre una quantitat més o menys regular de Generation,
i, quan no és així, sovint ens demanen explicacions per telèfon o per correu.
Aquest document es per centralitzar, les respostes i el protocol,
en aquests casos.


## La resposta ràpida

La resposta genèrica sense entrar en els motius concrets podria ser:

> Els drets a kWh s'han aplicat seguint l'algoritme establert pel Generation.
> Dintre del seu funcionament normal, a vegades es donen aquestes variacions.
> Els motius poden ser diversos.
> Però, en tot cas, els kWh que no han pogut entrar en aquesta factura
> es queden guardats a la teva bossa per factures posteriors.
> No es perden.
> 
> Els motius més comuns d'aquestes variacions són:
> 
> - Que per problemes de comunicació amb alguna de les plantes,
> les lectures no arribin a la bossa a temps per la facturació
> - Que tinguis més d'un contracte assignat al generation i s'hagin
> facturat en un ordre diferent a l'habitual.
> - Que les factures s'hagin generat en un ordre no cronològic.
> - Que la factura s'hagi cancel·lat mentres estava en esborrany, i posteriorment refet.
> - Que s'hagi fet una refacturació
> - Que un contracte més prioritari no hagi facturat i estigui reservant els darrers drets produïts
> - Que hagi canviat la tarifa i no tots els intervals horaris tinguin drets
> 
> En tots aquests casos, com deiem, tard o d'hora els kWh acabaran
> arribant a les factures dels contractes que tens assignats com a beneficiaris.
> Pots consultar el balanç de drets disponibles i assignats a l'Oficina Virtual.
> 
> Dit això, actualment no tenim eines per concretar de forma senzilla,
> la causa concreta del repartiment fet a una factura
> sense fer un anàlisi forense bastant costós en recursos.
> El podem fer, per descomptat.
> Tens dret a demanar-ho i el farem si el demanes.
> 
> També podria ser un error, però, quan ho és,
> normalment passa a molts contractes a la vegada
> i no tenim constància de que sigui el cas.



## Entenent l'algoritme

### Recollint la informació de producció

Recollim la producció de cada planta hora a hora.
Ho fem de totes les plantes a la vegada.
Si una d'elles té problemes de comunicació, per exemple,
ens esperem a que estiguin solucionats fins que estiguin totes.
Quan tenim totes les plantes es reprén la recollida.

**Afectació:** Si la incidència s'allarga més de quinze dies
pot passar que es facturin dies que es podrien aprofitar
d'aquests kWh's que encara no estan a la bossa.

**Messures:**

- Hem afegit alarmes que ens avisen per poder reaccionar abans dels 15 dies
- Si arriba a passar, l'efecte és relatiu, els kWh es podran fer servir a la pròxima factura.

**Detecció:**

- Si la factura es recent, 
	- Llistat http://scriptlauncher.somenergia.lan/runner/productionCurve
	- Seleccionar els comptadors de les plantes de generation
	- Els darrers dies 
- Si fa dies de la factura,
	- IT: els documents de us de kwh del mongo tenen timestamp de quan s'afegeixen
	- IT: podem detectar que aixo es dona si les dates d'inserció es fan a una data posterior a la factura
	- TODO: Un llistat amb data de tall, per poder veure com estava la producció a la data de la factura


### La bossa de kWh per perfil d'accions (num de accions)

- Els kWh produïts es reparteixen **proporcionalment a les accions** que tingui la socia.
- Com que normalment, proporcionalment, hora a hora, no s'arriba al kWh, anem acomulant les fraccions
- Els kWh es computen per cada perfil d'accions, quan les fraccions acomulen kWh sencers.
- Com que aquest càlcul depén del nombre d'accions, generem una bossa de drets per cada perfil d'accions (1 accio, 2 accions, 3 accions....)
- Cada usuari tindrà disponible tants drets com sumi el perfil de les accions que tè.
- El perfil d'un usuari canvia.
  Exemple: Un usuari té 3 accions i el divendres se li acaba la carencia de 7 accions més que va comprar,
  els drets que li corresponen son els del perfil de 3 accions fins el dijous i el de 10 apartir del divendres.

http://scriptlauncher.somenergia.lan/runner/rightsCurve

![](images/(genkwh-scripts-rightsCurve)


### El primer que arriba

- Un soci pot tenir assignats diversos contractes
- La primera factura que arriba agafa els kWh que li son accessibles (segons les restriccions detallades més avall)
- **Per això l'ordre en que s'emeten les factures pot canviar el resultat.**
- Els kWh emprats es guarden a la corba propia de la socia i mai no pot superar el que té el seu perfil d'accions
- Script per veure la corba de kWh emprats per una socia: http://scriptlauncher.somenergia.lan/runner/corbesUsPerSoci

### Discriminació horària

- Si el contracte te discriminació horària, només es podran fer servir els kWh produïts al mateix període


### Finestra temporal d'accés als drets

- Si no hi ha cap altre factura més prioritaria, una factura té accés als drets generats entre:
	- Un any abans de la primera data facturada (**caducitat d'un any**)
	- I la darrera data facturada (**no consumir del futur**)
- Sempre es gasten els drets més antics disponibles per evitar que caduquin

Possible problema:

Si, per algun motiu (refacturació...),
**no les facturem per ordre cronològic**
potser que la factura més antiga es quedi sense Generation.

Ex. facturem Agost abans que Juliol.
La factura d'Agost gastarà els kWh de Juliol que son més antics,
pero quan factura Juliol, els drets generats a l'Agost no li son disponibles perque estan en el futur.
Això generaria una factura de Juliol no tants o fins i tot zero kWh de Generation.
L'impacte es relatiu perque la factura de Setembre ja podrà gastar els drets d'Agost.



### 



### Aplicació dels periodes










