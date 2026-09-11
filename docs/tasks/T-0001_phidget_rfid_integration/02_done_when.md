# Done When

- [ ] `custom_components/phidget_rfid/manifest.json` gültig, `phidget22` als
      gepinnte Dependency.
- [ ] Config Flow erkennt/verbindet Reader über Seriennummer, legt Device an.
- [ ] Capability-Layer liefert für jedes der 5 Modelle korrekte Fähigkeiten
      (read-only vs. read-write, unterstützte Protokolle/Chipsätze, LED).
- [ ] Bei Tag-Erkennung wird HA-Event `phidget_rfid_tag` gefeuert und Sensor/
      Binary-Sensor aktualisiert.
- [ ] Write-Service nur registriert, wenn Gerät `can_write` unterstützt.
- [ ] LED-Service nur registriert, wenn Gerät `has_led` unterstützt.
- [ ] USB-Trennung/-Wiedereinstecken führt zu Status "unavailable"/Reconnect
      ohne manuellen Neustart der Integration (so weit ohne echte Hardware
      verifizierbar — Rest als "nicht vollständig verifiziert" markiert).
- [ ] Unit-Tests grün, `phidget22` vollständig gemockt, kein Hardware nötig.
- [ ] README + Hardware-Test-Anleitung vorhanden.
- [ ] Git-Historie mit sinnvollen Commits, kein Squash.
