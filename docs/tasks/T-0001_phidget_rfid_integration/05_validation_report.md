# Validation Report

## Tatsächlich ausgeführt (nicht nur behauptet)

- `python3 -m venv .venv && pip install -r requirements_test.txt` — real
  install of `pytest-homeassistant-custom-component` (zieht `homeassistant`
  als Abhängigkeit), gegen `homeassistant==2026.9.1` (sehr nah an der
  Zielumgebung 2026.9.0).
- `pytest tests/ -q` → **22 passed** (models, device, coordinator,
  config_flow). Vollständig gegen ein selbstgebautes Fake-`Phidget22`-Modul
  in `sys.modules`, kein echtes `libphidget22` nötig.
- Während der Testläufe wurde ein echter Bug gefunden und gefixt: der über
  `async_dispatcher_connect` registrierte State-Update-Callback in
  `entity.py` lief ohne `@callback`-Dekorator, wodurch Home Assistant ihn in
  einen Executor-Thread verschob → `async_write_ha_state()` außerhalb des
  Event-Loops → `RuntimeError` (thread-safety guard). Fix: `@callback` auf
  `PhidgetRfidEntity._handle_update`. Test lief danach grün.
- JSON-Validität von `manifest.json`, `strings.json`,
  `translations/{en,de}.json` geprüft (`python3 -m json.tool`).

## NICHT verifiziert (ehrlich gekennzeichnet, nicht verschwiegen)

- **Echte Hardware**: kein echter PhidgetRFID 1024_0B in dieser Session
  angeschlossen/getestet. Insbesondere ungeprüft:
  - Ob `import Phidget22` unter Home Assistant OS / im HA-Core-Prozess auf
    Raspberry Pi tatsächlich das native `libphidget22` korrekt lädt und der
    Reader per libusb enumeriert (AppArmor-Konfinement des Core-Containers).
  - Ob USB-Abziehen/Wiedereinstecken tatsächlich sauber `onDetach`/
    `onAttach` auslöst und der Reconnect in der Praxis funktioniert.
  - Exakte Groß-/Kleinschreibung und Modulpfad (`Phidget22.Devices.RFID` vs.
    z. B. `phidget22.Devices.RFID`) der echten installierten
    `phidget22`-PyPI-Distribution.
  - Ob `write()` auf T5577-Tags mit echter 1024_0B-Firmware tatsächlich
    erfolgreich ist.
  - Modell-Erkennung (`identify_model`) — Heuristik über `getDeviceVersion()`
    ist nicht gegen echte Geräte-Versionsnummern verschiedener Modelle
    verifiziert.
- Kein `ruff`/`mypy`/`hassfest`-Lauf durchgeführt (nicht installiert in
  dieser Session) — nur manuelle Code-Durchsicht.
- Kein Test der Config-Flow-UI im echten Frontend (nur über
  `hass.config_entries.flow` programmatisch getestet).

## Empfehlung vor produktivem Einsatz

Vor dem produktiven Einsatz auf dem echten Raspberry Pi: die Hardware-Test-
Checkliste in README.md komplett durchgehen, insbesondere Schritt 9
(USB-Wiedereinstecken).
