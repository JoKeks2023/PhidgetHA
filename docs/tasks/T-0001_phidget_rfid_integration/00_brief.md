# T-0001 — PhidgetHA: Native Phidgets RFID Integration für Home Assistant

## Auftrag

Native, saubere Home-Assistant-Lösung für Phidgets-RFID-Reader (USB-Anschluss an
Raspberry Pi mit Home Assistant OS). Primäres Zielgerät: PhidgetRFID Read-Write
1024_0B. Architektur muss generisch für die gesamte Phidgets-RFID-Produktfamilie
sein (1023_0, 1023_1, 1024_0, 1024_0B, 1024_1), über eine Capability-Abstraktion.

## Architekturentscheidung (nach Recherche, vom Nutzer bestätigt)

**Reine Home-Assistant Custom Integration, kein Add-on.**

Begründung (siehe `03_constraints.md` für Details):

- Der Home-Assistant-Core-Container erhält unter Home Assistant OS bereits
  rohen USB-Zugriff (`PolicyGroup.USB`, Major 189 = `/dev/bus/usb/*`) — kein
  Add-on nötig für USB-Hardwarezugriff.
- Das `phidget22`-PyPI-Paket kann wegen fehlendem öffentlichem Source-Repo /
  öffentlicher CI ("Dependency Transparency"-Regel) ohnehin **nie** in Home
  Assistant Core aufgenommen werden — unabhängig von Add-on oder nicht. Der
  einzige verbleibende Vorteil eines Add-ons (Crash-Isolation) wird stattdessen
  durch defensives Error-Handling/Reconnect-Logik in der Integration selbst
  abgefedert.

## Ursprüngliche Anforderungen

Siehe Projekt-Systemprompt (vollständiger Anforderungstext des Nutzers) für:
RFID-Events, Entities, Schreib-Service, LED-Service, Fehlerbehandlung,
Mehrgeräte-Unterstützung, Config Flow, Diagnostics, Tests, Hardware-Test-Doku,
Git-Workflow (kein Squash-Merge), Repository-Struktur.
