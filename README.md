## Comdirect Postbox Downloader in Python
* Getestet unter MX-Linux 18.3 (Debian9-Derivat), python 3.5
### Notwendige Pakete
* python3-selenium
* chromedriver
* chromium
### Bedienung
* Im Script oben Download-Pfad und Zugangsnummer eintragen
* Im Terminal starten mit:

      > ./cddl.py
* Alternativ für den interaktiven Modus (s.u.), im Terminal starten mit:

      > ./cddl.py -i

* Im Python-Terminal (nicht im Browser) die PIN eingeben  
(Die PIN wird während der Eingabe nicht angezeigt, um ein Auto-cachen auf dem Rechner zu verhindern)
* Alternativ: Option `-l` mitgeben und nach Öffnen des Browsers dort selbständig einloggen.
* Im Browser dann Photo-TAN eingeben

Heruntergeladen werden alle PDFs im Posteingang mit Ausnahme der Links, die "Termingebundenes" enthalten, weil hier die Comdirect trotz .pdf-Endung manchmal einen HTML-Link versteckt und das Script dann durcheinanderkäme.
 
Wer sein gesamtes Archiv herunterladen möchte, kann auch im Script oben

    gotoArchive = True

setzen, oder die Option `-a` mitgeben.

### Interaktiver Modus
Nach Beendigung wird die Python-Shell nicht geschlossen. Man kann beliebig in der Postbox suchen und dann die letzte Script-Zeile
 
    cddlGetPdf(drv)
 
nochmals eingeben, um weitere PDFs herunterzuladen.
