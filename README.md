# bildungslogin

## Getting started:

[Installation and usage](getting_started.md)

# Architecture
The bildungslogin- module is made up of the following main components:
- a udm- module with currently three methods: bildungslogin/assignments, bildungslogin/licenses, bildungslogin/metadata
- a GUI- part for the UCS@School- UMC
- a server API for the BILDUNGSLOGIN to query assigned licenses
- a schema- extension to store licenses, metadata and assignments in the LDAP

## Schema- Extension
The gross of the license- handling is done in the ldap under the module- storage `cn=licenses,cn=bildungslogin,cn=vbm,cn=univention,$LDAP_BASE`

Directly underneath this DN, the actual licenses are stored. Under the licenses, the actual assignments are then stored:
- for single- and volume licenses with one assignment entry per available license
- for group- licenses with only one single assignment entry

The assignment entry is then amended with the EntryUUID of the assigned unit, which is either
- for single- and volume licenses the **EntryUUID of the User** or
- for group- licenses with the **EntryUUID of the Group**

Hence the tree looks as follows:
```
LICENSE_MODULE_BASE
|
 -- licenses
   |
    -- assignments --> EntryUUID of Assignee (or Group)
```

## Logging

- The UMC- Module logs to `/var/log/univention/management-console-module-licenses.log`, the HTTP-API Log for UCSScrools also logs to `/var/log/univention/ucsschool-apis/http.log`
- there is a specific logfile for the mediaupdate- actions: `/var/log/univention/bildungslogin-media-update.log`

# Development

## Debugging
TODO

### Coverage

#### in host

Create a `.coveragerc` with the following content:

```ini
[run]
branch = False
parallel = True
source = univention.bildungslogin
        univention.udm.modules
        univention.admin.handlers.bildungslogin
[report]
ignore_errors = False
show_missing = True
omit = handlers/ucstest
        syntax.d/*
        hooks.d/*
include = /usr/lib/python2.7/dist-packages/univention/bildungslogin/*
        /usr/lib/python2.7/dist-packages/univention/admin/handlers/bildungslogin/*.py
        /usr/lib/python2.7/dist-packages/univention/udm/modules/bildungslogin_*.py
```

Then run (from the directory where `.coveragerc` is):

```bash
python -m coverage run /usr/bin/pytest -lvvx /usr/share/ucs-test/*_bildungslogin_*/*_*.py && /usr/share/ucs-test/selenium-pytest && \
  python -m coverage combine && \
  python -m coverage report && \
  python -m coverage html --directory=./htmlcov
```

#### In Docker container

TODO

# Tests und Verifizierungen

## Lizenzen importieren

Mit dem Tool `bildungslogin-license-import` lassen sich Lizenzen importieren.

### Beispiel Lizenz

Die json-Datei mit Dummy-Codes enh??lt g??ltige Lizenzdatens??tze, aber mit frei erfundene Lizenzcodes. Sie dient dazu, in schulischen Testsystemen die internen Funktionen des Lizenzmanagers (ohne Medienzugriff in den Verlagssystemen) zu testen, ohne dass daf??r echte Lizenzcodes ben??tigt werden. Die Datei wird zusammen mit den Paketen des ucs-Lizenzmanagers und einer Anleitung ausgeliefert.

```json
[
  {
    "lizenzcode": "WES-DEMO-CODE-0000",
    "product_id": "urn:bilo:medium:WEB-14-124227",
    "lizenzanzahl": 60,
    "lizenzgeber": "WES",
    "kaufreferenz": "Lizenzmanager-Testcode",
    "nutzungssysteme": "Testcode ohne Medienzugriff",
    "gueltigkeitsbeginn": "",
    "gueltigkeitsende": "",
    "gueltigkeitsdauer": "Schuljahreslizenz",
    "sonderlizenz": ""
  },
  {
    "lizenzcode": "CCB-DEMO-CODE-0000",
    "product_id": "urn:bilo:medium:610081",
    "lizenzanzahl": 60,
    "lizenzgeber": "CCB",
    "kaufreferenz": "Lizenzmanager-Testcode",
    "nutzungssysteme": "Testcode ohne Medienzugriff",
    "gueltigkeitsbeginn": "",
    "gueltigkeitsende": "",
    "gueltigkeitsdauer": "397 Tage",
    "sonderlizenz": ""
  }
]
```

### Beispiel Import

Ein Import wird wie folgt durchgef??hrt:

`bildungslogin-license-import --license-file $PFAD_ZUR_LIZENZ --school $SCHUL_K??RZEL`

## Metadaten importieren

Der Metadatenimport erfolgt automatisch.
Bei Bedarf kann er jedoch manuell ??ber das CLI Tool `bildungslogin-media-import` ausgef??hrt werden.
F??r den automatischen Import m??ssen die Zugangsdaten konfiguriert werden.

### Konfiguration

In die Datei `/etc/bildungslogin/config.ini` m??ssen die Zugangsdaten f??r die Metadaten API eingetragen werden.
Alternativ k??nnen diese dem CLI Tool auch direkt ??bergeben werden (`bildungslogin-media-import --help`).

### Manueller import

Ein Metadatenimport f??r eine Produkt ID kann nun wie folgt gestartet werden:

`bildungslogin-media-import --config-file /etc/bildungslogin/config.ini urn:bilo:medium:COR-9783060658336`

## Verwendung der Provisioning API

Mit dem Usernamen `bildungslogin-api-user` und dem Passwort kann die API genutzt werden.

Der Zugriff erfolgt in zwei Schritten:

1) Authorization

Der Token kann folgenderma??en geholt werden:

```bash
curl -X 'POST'   'https://FQDN/ucsschool/apis/auth/token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=bildungslogin-api-user&password=v3r7s3cr3t'
```

Die Antwort ist:

```json
{
  "access_token":"eyJ0eXAiOiJKV1...",
  "token_type":"bearer"
}
```

2) Provisionierung von Nutzerdaten

Die Daten des Users `demo_student` k??nnen mit folgendem Befehl abgerufen werden:

```bash
curl -X 'GET' \
  'https://FQDN/ucsschool/apis/bildungslogin/v1/user/demo_student' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJ0eXAiOiJKV1...'
```

Zur interaktiven Erforschung der API findet sich eine Swagger UI sich unter https://FQDN/ucsschool/apis/docs.


### Beispiel Lizenzzuweisung via CLI

Um eine Zuweisung durchzuf??hren, m??ssen wir ein Assignment-Objekt der Lizenz editieren. Nach einem initialen Lizenzimport sind noch alle "assignments" verf??gbar. Daher nehmen wir uns ein beliebiges Objekt, welches in `assignments` referenziert ist und weisen es einem Nutzer zu. Dies geschieht mittels der EntryUUID eines Nutzers, die wir mit dem folgenden Befehl ermitteln k??nnen:

```shell
root@dc0:~# univention-ldapsearch -LLL uid=demo_student entryUUID
dn: uid=demo_student,cn=schueler,cn=users,ou=DEMOSCHOOL,dc=realm4,dc=intranet
entryUUID: bc2d0d2a-224f-103b-9f8a-1587660bcd6c
```

Mit diesen Informationen k??nnen wir nun eine Zuweisung durchf??hren:

```shell
root@dc0:~# udm bildungslogin/assignment modify --dn cn=09d1834b-d238-466a-90f2-8c52c4b1cd07,cn=c23df3f1b32e0e78a8a98e7ea2eacd5ad90447be01643d87bb34ceba942e9a39,cn=licenses,cn=bildungslogin,cn=vbm,cn=univention,dc=realm4,dc=intranet --set assignee=bc2d0d2a-224f-103b-9f8a-1587660bcd6c --set time_of_assignment="$(date -I)" --set status=ASSIGNED
Object modified: cn=09d1834b-d238-466a-90f2-8c52c4b1cd07,cn=c23df3f1b32e0e78a8a98e7ea2eacd5ad90447be01643d87bb34ceba942e9a39,cn=licenses,cn=bildungslogin,cn=vbm,cn=univention,dc=realm4,dc=intranet
root@dc0:~# udm bildungslogin/assignment list --filter cn=09d1834b-d238-466a-90f2-8c52c4b1cd07
cn=09d1834b-d238-466a-90f2-8c52c4b1cd07
DN: cn=09d1834b-d238-466a-90f2-8c52c4b1cd07,cn=c23df3f1b32e0e78a8a98e7ea2eacd5ad90447be01643d87bb34ceba942e9a39,cn=licenses,cn=bildungslogin,cn=vbm,cn=univention,dc=realm4,dc=intranet
  assignee: bc2d0d2a-224f-103b-9f8a-1587660bcd6c
  cn: 09d1834b-d238-466a-90f2-8c52c4b1cd07
  status: ASSIGNED
  time_of_assignment: 2021-08-12
```

Wenn man diesen Nutzer nun ??ber die Provisioning API abruft, erkennt man, dass ihm die Lizenz `VHT-7bd46a45-345c-4237-a451-4444736eb011`
zugeordnet ist.

## Beispiel Lizenz l??schen

Das ??ndern der Lizenzzuweisung im "Provisioned" Status wird unterbunden, da diese bereits im Medienregal eingel??st wurden. Es ist aber m??glich eine komplette Lizenz zu l??schen, damit werden alle Zuordungen auch entfernt, da diese im LDAP Kind-Objekte sind.

Anzeige aller Informationen und Zuordungen einer Lizenz:

```shell
root@dc0:~# udm bildungslogin/license list --filter code="WES-TEST-CODE-LZL07"
code=WES-TEST-CODE-LZL07
DN: cn=0fb9155c27655c172f2b2149108ed7736da6595eef302c8b160b95ee6112a0f8,cn=licenses,cn=bildungslogin,cn=vbm,cn=univention,dc=vbm,dc=schule-univention,dc=de
```

L??schen einer Lizenz

```shell
root@dc1:~# udm bildungslogin/license remove --dn cn=0fb9155c27655c172f2b2149108ed7736da6595eef302c8b160b95ee6112a0f8,cn=licenses,cn=bildungslogin,cn=vbm,cn=univention,dc=vbm,dc=schule-univention,dc=de
...
```

## Beispiel alle Daten l??schen

Zum Aufr??umen einer Testumgebung (Achtung: dies l??scht s??mtliche Lizenzen aller Schulen des Systems!)

Alle Lizenzen l??schen:

```shell
root@dc0:~# for dn in $(udm bildungslogin/license list | sed -n 's/DN: //p'); do udm bildungslogin/license remove --dn $dn; done
```
