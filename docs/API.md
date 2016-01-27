
- AssignadorGenKwh
  - kwhDisponibles(contracte, periode, dataInici, dataFinal) : kwh
  - gasta(contracte, periode, dataInici, dataFinal, kwh)
  - retorna(contracte, periode, dataInici, dataFinal, kwh)

- TrackerConsumGenKwh
  - protocol per l'Assignador
    - disponible(soci, periode, dataInici, dataFinal): corbaKwh
    - gasta(soci, periode, dataInici, dataFinal, kwh)
    - retorna(soci, periode, dataInici, dataFinal, kwh)
  - protocol Estadistiques (per la info de la factura i la OV)
    - produccio(soci, dataInici, dataFinal): corbaKwh
    - dretsNoGastats(soci, dataInici, dataFinal): corbaKwh
    - dretsCaducats(soci, dataInici, dataFinal): corbaKwh
    - dretsEnPerillDeCaducarse(soci, dataInici, dataFinal) : (kwh, data)*
