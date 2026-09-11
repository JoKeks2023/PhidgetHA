# Implementation Report

## Umgesetzt

- `custom_components/phidget_rfid/`: `manifest.json`, `const.py`,
  `models.py` (Capability-Layer), `device.py` (Phidget22-Wrapper,
  Executor-/Thread-Bridging), `coordinator.py` (Push-State, Reconnect mit
  Backoff), `entity.py`, `sensor.py`, `binary_sensor.py`, `config_flow.py`
  (Discovery + manuelle Eingabe als Fallback, kein Freitext für
  enumerierbare Werte), `diagnostics.py`, `services.yaml`, `strings.json`,
  `translations/{en,de}.json`.
- Capability-Matrix für 1023_0, 1023_1, 1024_0, 1024_0B, 1024_1.
- Events `phidget_rfid_tag`, `phidget_rfid_tag_lost`.
- Entities: `sensor.last_tag`, `binary_sensor.tag_detected`,
  `binary_sensor.connectivity` (diagnostic).
- Service `phidget_rfid.write_tag`, per `supported_features`-Bitmask nur für
  schreibfähige Geräte sichtbar (HA-Konvention, analog `light`/`climate`).
- Reconnect mit exponentiellem Backoff (5s–300s) bei USB-Detach.
- Vollständig gemockte Unit-Tests (`tests/components/phidget_rfid/`), kein
  Hardware- oder libphidget22-Bedarf zum Testen.
- README, CHANGELOG, LICENSE (MIT), Hardware-Test-Checkliste, `hacs.json`.

## Bewusst nicht umgesetzt (dokumentiert statt erfunden)

- LED-Steuerung: keine `setLEDOn`-artige Methode auf der Phidget22
  `RFID`-Channel-Klasse in Primärquellen gefunden. Nicht implementiert statt
  geraten.
- Antenna-Service: API-seitig implementiert (`device.py`,
  `async_set_antenna_enabled`), aber kein HA-Service/Entity, da nicht
  ursprünglich angefragt.
- HID-26-bit/HID-Generic-Protokollwerte (nur 1024_1): im Capability-Modell
  als Strings vorhanden, aber die exakten `phidget22.RFIDProtocol`-Enum-Namen
  dafür sind nicht primärquellen-verifiziert.

## Abweichungen vom ursprünglichen Architekturvorschlag

- Kein Add-on (s. `00_brief.md` — Architekturentscheidung nach Nutzer-
  Rückfrage geändert, explizit bestätigt).

## Tatsächlich ausgeführte Verifikation

Siehe `05_validation_report.md`.
