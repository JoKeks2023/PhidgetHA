# Scope

## In Scope

- `custom_components/phidget_rfid/` — HACS-fähige Home Assistant Custom
  Integration (Config Flow, Coordinator, Device Registry, Entities, Services,
  Diagnostics, Translations DE/EN).
- Capability-Abstraktionsschicht: Device/Model Detection → Capability
  Detection → RFID Interface. Kein Code prüft hart auf `1024_0B`.
- Unterstützte Modelle: 1023_0, 1023_1, 1024_0, 1024_0B (Referenzgerät,
  First-Class), 1024_1.
- Event `phidget_rfid_tag` bei Tag-Erkennung.
- Entities: Sensor (letzter Tag, Protokoll), Binary Sensor (Tag präsent),
  Diagnostic-Entities (Verbindung, Firmware, Seriennummer). Nur wenn vom Gerät
  unterstützt: Write-Service, LED-Steuerung.
- Reconnect-/Fehlerbehandlung (USB-Trennung, Wiedereinstecken, Phidget22-Fehler).
- Unit-Tests mit gemocktem `phidget22`.
- README, CHANGELOG, LICENSE, Hardware-Testanleitung.

## Out of Scope (für diese Iteration)

- Home Assistant Add-on (Architekturentscheidung: keins nötig).
- Home Assistant Core-Aufnahme (technisch ausgeschlossen, s. `00_brief.md`).
- Mehrere Reader gleichzeitig aktiv testen (nur architektonisch vorbereitet,
  da nur 1 Gerät real vorhanden ist).
- VINT-Hub-Betrieb (nur direkter USB-Anschluss real getestet).
