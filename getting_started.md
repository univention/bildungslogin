# Überblick und Vorbereitung

Bildungslogin.de bietet ein zentrales Medienregal, über das sich viele verschiedene digitale Anwendungen deutscher Bildungsmedienverlage nutzen lassen. Mit dieser Implementierung wird der Aufbau und die Anbindung eines Lizenzmanagers auf Basis von Univention Corporate Server (UCS) mit Single-Sign-On für das Angebot von bildungslogin.de ermöglicht.

UCS und die Erweiterung UCS@school stellen für Schulträger und Bildungsministerien schulische Infrastruktur vornehmlich als Identity and Accessmanagement (IAM) bereit. Die dort bereits vorhandenen Benutzerkonten sollen für die Nutzung von bildungslogin.de verwendet werden können, inkl. Zuweisung und Übertragung von Lizenzen, sodass zum einen eine doppelte Pflege entfällt und zum anderen Lehrkräfte und SuS direkt aus der schulischen IT-Infrastruktur heraus mit ihren gewohnten Zugangsdaten auch bildungslogin.de nutzen können.

Die Implementierung ist aktuell mit `UCS 4.4` (über rpm- files) sowie `UCS 5.0` (als Univention- APP) kompatibel.

## Abstimmung mit bildungslogin.de

Für den Betrieb des Plugins ist eine Abstimmung mit dem [Bildungslogin](https://www.bildungslogin.de/) notwendig. Sämtliche benötigten Parameter werden durch ein Onboarding erörtert.

## Übersicht der Installation

Das Lizenzmanager- Plugin für UCS besteht grundlegend aus zwei Modulen, welche bei einer Installation über die UCS-App gemeinsam installiert werden:
- einer GUI- Komponente, um Produkte und Lizenzen einsehen, sowie Zuweisungen vornehmen zu können.
- einer Schnittstelle, welche die Zuweisungen für BILDUNGSLOGIN zur Verfügung stellt.

Bei einer Installation über mehrere Server betrachten Sie bitte diese Komponenten und verteilen diese Komponenten entsprechend. Beachten Sie bitte, dass die Installation nur auf Master- oder Backup - Servern möglich ist. Die API benötigt (stark limitierten) Schreibzugriff, daher ist eine funktionierende Kommunikation zwischen den Servern sicherzustellen.

### Grundsätzliches

Auf dem UCS- Server muss SSO, sowie die UCS@School- API eingerichtet sein und von extern erreichbar sein. Dies ist notwendig, da BILDUNGSLOGIN die Zuweisungen abrufen muss.

# Installation

## Voraussetzungen

### 1. Single-Sign-On und Portal

- Für SSO wird der `OpenID Connect Provider` benötigt. Die Installation und Konfiguration ist im [UCS Handbuch](https://docs.software-univention.de/handbuch-4.4.html#domain:oidc) beschrieben.
- Für die gesicherte und verschlüsselte Datenübertragung kann [Let’s Encrypt aus dem App Center](https://www.univention.de/produkte/univention-app-center/app-katalog/letsencrypt/) verwendet werden.
- Ein Blick in den Hilfe-Artikel ist hilfreich, wenn das [Portal und SSO umkonfiguriert](https://help.univention.com/t/reconfigure-ucs-single-sign-on/16161) wird.
- Stellen Sie sicher, dass die SSO- Authentifizierung aus dem Internet erreichbar ist - und führen Sie ggf. notwendige Absicherungsmassnahmen durch.

### 2. UCS@School- Komponenten installieren

1. Als erstes muss UCS@school installiert sein: Melden Sie sich an der UCS Management Konsole an, öffnen Sie den App Center und Installieren Sie die [UCS@school app](https://www.univention.de/produkte/univention-app-center/app-katalog/ucsschool/).
2. Anschließend muss die UCS@school APIs app installiert werden. Dies können Sie auf der Kommandozeile mit root- Berechtigungen wie folgt erledigen:
 `univention-app install ucsschool-apis` oder `univention-app install ucsschool-apis --username <GUI-Admin-Benutzername>`.
3. Stellen Sie sicher, dass die UCS@School- API aus dem Internet erreichbar ist - und führen Sie ggf. notwendige Absicherungsmassnahmen durch.


Überprüfen Sie dass alle Skripte erfolgreich durchlaufen wurden: GUI-> Domain -> Domain join: alle erfolgreich?
## Lizenzmanagermodul- Installation

### 1. Pakete installieren

Zur Konfiguration des UDM REST API Clients wird eine Java Runtime in den Docker Container installiert. Dafür muss dieser auf den deutschen Debian Mirror zugreifen. Ausgehende HTTP-Verbindungen - zumindest zur IP `141.76.2.4` (`ftp.de.debian.org`) - müssen dafür während der Installation erlaubt sein.

**ACHTUNG**: auf Primary und Backup nodes (DC Master und DC Backup) installiert das Joinscript `68udm-bildungslogin.inst` des Pakets `udm-bildungslogin` LDAP-Indices. Dafür wird der LDAP Server temporär angehalten. Bei großen Installationen kann dies eine Weile dauern.

Zur Installation führen Sie folgende Schritte aus:
- Einrichten des Repositories (Details erhalten Sie beim Onboarding)
- `apt install bildungslogin-plugin python-bildungslogin udm-bildungslogin ucs-school-umc-licenses` 

Beschreibung der Pakete:
- `python-bildungslogin` (Programmbibliothek und CLI Lizenzimport)
- `udm-bildungslogin` (UDM Module)
- `ucs-school-umc-licenses` (UMC Modul)
- `bildungslogin-plugin` (Provisionierungs REST API Plugin für die `ucsschool-apis` App.)

Ebenso ist ein API- Benutzer mit der ID **bildungslogin-api-user** eingerichtet. Diesem muss noch ein Passwort vergeben werden (siehe [Konfiguration](#1-setup-der-provisioning-api)).

Bei einer Deinstallation wird dieser Nutzer deaktiviert.

## Verifizierung der Installation

### 1. Prüfen des `memberOf` overlays

Die UMC-Module setzen das LDAP-overlay `memberOf` voraus.
Ob das LDAP-overlay aktiviert ist lässt sich über die Systemdiagnose oder `ucr get ldap/overlay/memberof` prüfen.
Sollte es nicht aktiviert sein, sind die nötigen Schritte, zur Aktivierung, in folgendem Artikel beschrieben: [memberOf attribute: Group memberships of user and computer objects](https://help.univention.com/t/memberof-attribute-group-memberships-of-user-and-computer-objects/6439)

### 2. Einstellung der `sizelimit` UCR Variable

Einige der neuen UMC Module nutzen ein Limit um zu bestimmen, wie viele Ergebnisse sie maximal anzeigen, bevor sie eine
Einschränkung durch Suchparameter verlangen. Dieses Limit kann durch die UCR Variable `directory/manager/web/sizelimit`
gesetzt werden und ist standardmäßig auf 2000 eingestellt. Aktuell enmpfiehlt es sich dieses Limit für das Lizenzmanagement
auf 500 zu setzen. Dies kann mit dem Befehl `ucr set directory/manager/web/sizelimit=500` erreicht werden.

### 3. Vorhandensein aller UDM- Module

Zur Sicherstellung, dass alle relevanten [UDM-Module](#univention-directory-manager) installiert wurden, kann der folgende Befehl verwendet werden: `udm modules | grep bildungslogin`.

Hierbei sollten die folgenden Module ausgegeben werden:
- bildungslogin/assignment
- bildungslogin/license
- bildungslogin/metadata

## Installationsprobleme

Probleme bei der Installation können häufig durch das erneute Ausführen der Join Skripte behoben werden:

```bash
univention-run-join-scripts --run-scripts --force 68udm-bildungslogin.inst
univention-run-join-scripts --run-scripts --force 69bildungslogin-plugin-openapi-client.inst
univention-run-join-scripts --run-scripts --force 70bildungslogin-plugin.inst
```

## Konfiguration

Wenn alles erfolgreich konfiguriert wurde, sind die beiden Joinskripte `69bildungslogin-plugin-openapi-client.inst` und `70bildungslogin-plugin.inst` ohne Fehler durchgelaufen (siehe Logfile: `/var/log/univention/join.log`).

### 1. Setup der Provisioning API

Zur Verwendung der Provisioning API ist beim Installationsprozess bereits ein Benutzer erstellt worden. Dieser muss nun noch aktiviert, und ein Passwort gesetzt werden.

Der Nutzer inkl. Passwort muss dann dem BILDUNGSLOGIN mitgeteilt werden, damit dieser die API abfragen kann:

```bash
udm users/user modify \
  --dn "uid=bildungslogin-api-user,cn=users,$(ucr get ldap/base)" \
  --set disabled=0 \
  --set password="<geheimes passwort hier einsetzen>"
```

### 2. Anbindungsdetails zum BILDUNGSLOGIN konfigurieren
Die Datei /etc/bildungslogin/config.ini enthält notwendige Daten, um sich mit dem BILDUNGSLOGIN zu verbinden. Sie erhalten diese beim Onboarding:

**Auth**
- **clientId**: ID für den Bezug von AccessTokens zur Nutzung der Bildungslogin-API, für `  `.
- **clientSecret**: Secret für den Bezug von AccessTokens zur Nutzung der Bildungslogin-API.
- **Scope**: Verwendetes Scope für die Anbindung

**APIEndpoint**
- **AuthServer**: Der Authentifizierungsserver des BILDUNGSLOGINs, welcher Token ausstellt
- **ResourceServer**:  Der API- Endpunkt des BILDUNGSLOGIN, um einen Lizenz- bzw. Medienabruf durchzuführen

#### Anpassen der Zeit der Metadatenaktualisierung

Die Metadaten werden jeden Tag zwischen 20 und 6 Uhr aktualisiert.

Das kann durch zwei Variablen angepasst werden:
- cron/bildungslogin-meta-data/time kann die Startzeit angegeben werden
- cron/bildungslogin-meta-data/command kann über den Parameter von /usr/sbin/jitter die Zeitspanne angegeben werden, in der zufällig der Befehl ausgeführt wird. Der Default-Wert ist 36000, was 10 Stunden entspricht.

### 3. Portal-Eintrag hinzufügen

Auf der Portalseite wird eine Kachel mit den folgenden Werten eingerichtet, um direkt vom UCS@School- System auf das Medienregal zugreifen zu können. Den Wert von <idp_name> erhalten Sie zusammen mit den Anbindungsdetails (2.) beim Onboarding. Details siehe auch [UCS Handbuch](https://docs.software-univention.de/handbuch-4.4.html#central:portal).

**Relevante Konfiguration:**
- Logo: 
- Link (Test): https://www.bildungslogin-test.de/app/#/sso/bilob?idp_hint=<idp_name>
- Link (Produktion): https://www.bildungslogin.de/app/#/sso/bilob?idp_hint=<idp_name>

Den **idp_name** erhalten Sie vom Bildungslogin beim Onboarding.

### 4. API- Caching Konfiguration überprüfen/anpassen

Um auch bei größeren Systemen eine optimale Performance zu erreichen, werden die Lizenzzuweisungen für die API grundsätzlich gecached.
Dies geschieht standardmäßig einmal täglich um 5 Uhr morgens.

Um dies anzupassen, bzw. die Zeiten für einen Cache-Rebuild/-Refresh anzupassen, gibt es die folgenden UCR-Variablen:
- bildungslogin/rebuild-cache
- bildungslogin/refresh-cache

#### bildungslogin/rebuild-cache

Diese Variable ist für den eigentlichen Rebuild des Caches verantwortlich. Die aktuellen Zuweisungen werden zu den hier hinterlegten Zeitpunkt(en) ausgelesen und in einer Cache-Datei hinterlegt.

Die Variable muss einen validen Cron-Zeitplanausdruck enthalten.

#### bildungslogin/refresh-cache

Diese Variable ist für den Neustart der UCS@School-API zuständig. Wenn die UCS@School-API neu gestartet wird, wird auch das Cache-File neu eingelesen, und somit sind sämtliche Daten aktuell.

Ein Neustart ist allerdings nicht zwingend notwendig: wenn das Cache-File aktualisiert wird, wird beim ersten Aufruf (pro Worker) das Cache-File eingelesen und verwendet.
Da bei größeren Systemen das Einlesen einige Zeit benötigt, wird empfohlen, die API anstattdessen neu zu starten, um Timeouts oder längere Wartezeiten für die Nutzer zu verhindern.

Die Variable kann zwei unterschiedliche Werte enthalten:
- den Wert `after-rebuild` - dieser startet die UCS@School-API neu sobald das Cachefile neu erstellt wurde,
- einen validen Cron-Zeitplanausdruck.

#### Überwachung der Cache- Generation
Die Logs der Cache- Generierung werden in das syslog/journald geschrieben (bildungslogin-rebuild-cache), und sollten entsprechend überwacht werden - speziell auf "WARNING" oder "ERROR"- Nachrichten.

# Benutzung 

## Univention Management Console

In der UMC werden drei neue Module unter `Unterricht` angezeigt

- **Lizensierte Medien** LizensierteMedien im BILDUNGSLOGIN-Lizenzmanager anzeigen und durchsuchen
- **Medienlizenz- Übersicht** 
Medien-Lizenzen im BILDUNGSLOGIN-Lizenzmanager anzeigen, suchen, entziehen
- **Medienlizenzen zuweisen** 
Medien-Lizenzen im BILDUNGSLOGIN-Lizenzmanager zuweisen
- **Medienlizenzen importieren** Medien-Lizenzen in den BILDUNGSLOGIN-Lizenzmanager importieren
- **Klassenlisten** Generieren von Listen für Klassen und Arbeitsgruppen

## Univention Directory Manager
Über das bildungslogin-udm- Modul können u.a. die untenstehenden Vorgänge auf der Kommandozeile vorgenommen werden. Eine Auflistung sämtlicher Kommandos der Methoden des "bildungslogin"- UDM-Moduls findet man mit dem Help- Befehl, also:
- `udm bildungslogin/assignments help`
- `udm bildungslogin/license help`
- `udm bildungslogin/metadata help`

Beispiele:
- Lizenzen importieren: `bildungslogin-license-import --license-file ./sample_license.json --school "DEMOSCHOOL"`
- Auflisten aller Lizenzen: `udm bildungslogin/license list`
- Auflisten der Lizenzen mit einem bestimmten Lizenzcode: `udm bildungslogin/license list --filter code=CCB-DEMO-CODE-0000`
- Löschen einer spezifischen Lizenz (benötigt die DN): `udm bildungslogin/license remove --dn <DN Der Lizenz, z.B. vom obigen Abruf>`
- Anzeige aller zugewiesenen Lizenzen: `udm bildungslogin/assignment list --filter status=ASSIGNED`

## Bekannte Einschränkungen und Probleme

**Die Konfiguration enthält Zugänge für die Testumgebung**

Problemumgehung: Die Datei `/etc/bildungslogin/config.ini` muss für den Produktivbetrieb angepasst werden. Einzelheiten erhalten Sie beim Onboarding:

**Der Cronjob zum Medien-Abruf ergibt einen Fehler `ValueError: No JSON object could be decoded`**

Problemumgehung: Die für initiale Tests enthaltenen Dummy-Codes werden keine Mediendaten bereitgestellt. Nach dem Einspielen von richtigen Codes wird der Fehler behoben sein.

**Der Single-Sign-On Login läuft ab und die UMC ist in einer Ladeschleife**

Problemumgehung: Das klingt nach dem bekannten [Bug 52888](https://forge.univention.org/bugzilla/show_bug.cgi?id=52888). Als Lösung bitte die erlaubte Zeitdifferenz der SAML Gültigkeit bei der Authentifizierung auf 12 Stunden setzen, wodurch der Login an einem Arbeitstag nicht mehr vorzeitig abläuft.

```bash
ucr set umc/saml/grace_time=43200
```

## Performance
Wenn Sie eine große Anzahl von Lizenzen importieren (mehrere Tausend) kann der Importvorgang mehrere Minuten dauern.

## Logging
- UDM- Modul- Log: `/var/log/univention/management-console-module-licenses.log`
- UCSSchools-API- Log (nicht exklusiv): `/var/log/univention/ucsschool-apis/http.log`
- Log des Medienupdates: `/var/log/univention/bildungslogin-media-update.log`

## APIs
Für den Abruf der Lizenzzuweisungen muss die API des Moduls für den BiLo- Broker erreichbar sein.

**Basis- URL des UCS- Systems**
- `https://<FQDN des Schulservers>/ucsschool/apis/`

**Eingehende Aufrufe**
- POST: `auth/token`
- GET: `bildungslogin/v1/user/`

# Deinstallation

## Schulserver

Auf Schulservern sind nur die UMC Module zur Lizenzverwaltung und ihre Abhängigkeiten installiert.
Sie können folgendermaßen restlos entfernt werden:

```bash
apt purge udm-bildungslogin-encoders python-bildungslogin ucs-school-umc-licenses
```

Zur Kontrolle ob noch andere Pakete installiert sind, kann folgendes ausgeführt werden:

```bash
dpkg -l | grep -E 'bildungslogin|umc-licenses'
```

## Primary (DC Master) und Backup Server

Auf dem Primary (DC Master) bzw. Backup Servern sind die UDM Modulpakete, LDAP Schema und die Provisionierungs API installiert.
Außerdem liegen auf ihnen die LDAP Daten.


### Deaktivierung bzw. Entfernung des API- Nutzers

Bei einer Deinstallation der Provisionierungs API- Pakete wird der API- Nutzer deaktiviert. Dies ist bei einer Neuinstallation oder kompletten Entfernung zu beachten.

### Pakete und Metadaten-Cache

Die Paketdeinstallation entfernt neben allen Programmdateien optional auch die Konfigurationsdateien, sowie den Metadatencache - nicht jedoch die Lizenzdaten.

Alle installierten Pakete können wir folgt angezeigt werden:

```bash
dpkg -l | grep -E 'bildungslogin|umc-licenses'
```

Zur Deinstallation unter Beibehaltung der Konfigurationsdateien `apt remove ...` verwenden.
Um die Konfigurationsdateien ebenfalls zu löschen `apt purge ...` ausführen:

```bash
apt purge bildungslogin-plugin bildungslogin-plugin-openapi-client python-bildungslogin ucs-school-umc-licenses udm-bildungslogin udm-bildungslogin-encoders
```

Die Unjoin Skripte sollten automatisch ausgeführt worden sein.
Falls nicht, können sie gestartet werden mit:

```bash
univention-run-join-scripts
```

### Lizenz-Daten

Um zusätzlich alle Lizenz-LDAP-Objekte zu löschen, kann der gesamte LDAP-Container für das Lizenzmanagement gelöscht werden:

```bash
ldapdelete -D "uid=Administrator,cn=users,$(ucr get ldap/base)" -H "ldap://$(ucr get ldap/master)" -W -x -r "cn=vbm,cn=univention,$(ucr get ldap/base)"
```

Dieser Befehl löscht ebenfalls die Lizenzzuweisungen und Lizenzmetadaten aus dem LDAP.

Der folgende Befehl sollte keine Objekte mehr finden (`such object (32)`):

```bash
univention-ldapsearch -LLL -b "cn=vbm,cn=univention,$(ucr get ldap/base)" dn
```

### LDAP Schemata und ACLs

Sind **alle** LDAP Objekte (Lizenzen, Zuweisungen und Metadaten) entfernt worden auf die sich die LDAP Schemata und ACLs beziehen, dürfen auch diese entfernt werden.

Wenn bei diesem Schritt etwas schiefgeht, startet u.U. der LDAP-Server nicht mehr, bis das Problem behoben wurde.
Wegen dieses Risokos und weil LDAP-Schemata und ACLs weder Platz noch Performance kosten, werden sie üblicherweise nicht gelöscht.

Folgendermaßen können LDAP ACLs und Schemata gelöscht werden:

```bash
. /usr/share/univention-lib/ldap.sh
ucs_unregisterLDAPExtension --acl 64bildungslogin-metadata
ucs_unregisterLDAPExtension --acl 64bildungslogin-license
ucs_unregisterLDAPExtension --schema bildungslogin
ucr commit /etc/ldap/slapd.conf
service slapd restart
```
