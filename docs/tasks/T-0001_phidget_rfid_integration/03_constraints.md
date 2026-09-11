# Constraints (aus Recherche, mit Quellen)

## Phidget22 API (verifiziert gegen phidgets.com + offizielle Header/Python-Quellen)

- Channel-Klasse: `Phidget22.Devices.RFID.RFID`.
- Events: `setOnTagHandler(fn)`, `setOnTagLostHandler(fn)` — Callback läuft auf
  Phidget22-internem C-Thread, NICHT im HA-Event-Loop. Muss über
  `loop.call_soon_threadsafe(...)` zurück in den Event-Loop gebracht werden.
- Lesen: `getLastTag()`, `getTagPresent()`.
- Schreiben: `write(tagString, protocol, lockTag)` — nur wenn Modell
  Schreiben unterstützt (s. Capability-Matrix unten).
- Antenne: `setAntennaEnabled(bool)` / `getAntennaEnabled()`.
- Adressierung: `setDeviceSerialNumber()`, `setHubPort()`, `setChannel()`,
  `open()` / `openWaitForAttachment(ms)`, `close()`,
  `setOnAttachHandler()` / `setOnDetachHandler()` / `setOnErrorHandler()`.
- Protokoll-Enum (`RFIDProtocol`), bestätigte Werte: `EM4100 = 0x1`,
  `ISO11785_FDX_B = 0x2`, `PHIDGETS = 0x3` (PhidgetTAG). Werte für HID 26-bit /
  HID Generic (nur 1024_1) sind aus Primärquelle NICHT verifiziert — vor
  Implementierung von HID-Support gegen echtes SDK/Hardware prüfen.
- LED-Steuerung: **nicht** als Methode auf der RFID-Channel-Klasse gefunden.
  Vermutlich separater `DigitalOutput`-Channel auf denselben Board. Nicht aus
  Primärquelle verifiziert — LED-Feature entsprechend vorsichtig/optional
  implementieren und als "needs hardware verification" kennzeichnen.
- Alle blockierenden Phidget22-Aufrufe (insb. `open`/`close`/`write`) über
  `hass.async_add_executor_job(...)` ausführen — nie im Event-Loop blockieren.

## USB / Native Library

- Vendor-ID `0x06c2` (alle Phidgets-Geräte), Produkt-IDs im Bereich
  `0x0030`–`0x00af`. Exakte PID für 1024_0B nicht öffentlich dokumentiert.
- Kein udev-Rule-Setup durch die Integration selbst nötig/möglich (kein
  Root-Zugriff aus dem HA-Core-Prozess) — Home-Assistant-Core-Container erhält
  laut Supervisor-Quellcode bereits cgroup-Policy `PolicyGroup.USB`
  (Major 189 = `/dev/bus/usb/*`).
- `phidget22` (PyPI) bringt vorkompilierte Wheels für `manylinux_2_28`
  (x86_64, aarch64, armv7l) — deckt Raspberry Pi ab, kein Kompilieren zur
  Laufzeit nötig.
- **Nicht verifiziert, braucht echten Hardware-Test:** ob der Reader
  tatsächlich per libusb aus dem HA-Core-Container enumeriert (AppArmor-
  Konfinement des Core-Containers könnte greifen).

## Capability-Matrix (dokumentiert, siehe `phidget_rfid/models.py` für Code)

| Modell | Lesen | Schreiben | Status |
|---|---|---|---|
| 1023_0 | EM4100 | nein | discontinued |
| 1023_1 | EM4100 | nein | discontinued |
| 1024_0 | EM4100, ISO11785 FDX-B, PhidgetTAG | T5577 | NRND |
| 1024_0B | EM4100, ISO11785 FDX-B, PhidgetTAG | T5577 | NRND (Referenzgerät) |
| 1024_1 | EM4100, ISO11785 FDX-B, PhidgetTAG, HID 26-bit*, HID Generic* | T5577, EM4305 | aktuell |

`*` HID-Protokoll-Enum-Werte nicht primärquellen-verifiziert.

## Home Assistant Core Dependency-Regeln

- "Dependency Transparency"-Regel (No-Exceptions): PyPI-Dependency muss aus
  öffentlichem Repo mit öffentlicher CI stammen, getaggtes Release sein.
  `phidget22`/`phidget22native` erfüllen das nicht (nur Vendor-Wheels ohne
  öffentliches Repo) → **Integration kann nie in HA Core aufgenommen werden,
  bleibt dauerhaft HACS-Custom-Integration.**
- Blockierende Calls müssen über `hass.async_add_executor_job` laufen.
