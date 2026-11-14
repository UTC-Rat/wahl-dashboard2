# Wahl-Dashboard Wuppertal

Interaktives Dashboard für Wahlergebnisse von [wahlen.wuppertal.de](https://wahlen.wuppertal.de) (Open-Data-CSVs).

Enthaltene Wahlen (2009–2025, je nach Verfügbarkeit der Open-Data-Archive):

- **Bundestagswahlen**: 2009, 2013, 2017, 2021, 2025 (Zweitstimmen)
- **Ratswahlen**: 2009, 2014, 2020, 2025
- **Europawahlen**: 2009, 2014, 2019, 2024
- **Integrationsratswahlen**: 2014, 2020, 2025
- **Oberbürgermeisterwahlen**: 2009, 2015 (+ Stichwahl), 2020 (+ Stichwahl)

Je Wahl stehen — soweit vom Rathaus veröffentlicht — die Ebenen Stadt gesamt, Stadtbezirke, Kommunalwahlbezirke und Wahlbezirke zur Verfügung. Alle Parteien-Zuordnungen wurden gegen die amtlichen Endergebnisse verifiziert.

## Lokal starten

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    streamlit run app.py

## Deployment

Auf [Streamlit Community Cloud](https://share.streamlit.io) mit GitHub-Konto anmelden, Repo und `app.py` auswählen, deployen.

## Datenlage

- Quelle: `wahlen.wuppertal.de/<wahlcode>/05124000/daten/opendata/` (UTF-8, Semikolon-getrennt)
- Die verfügbaren CSV-Dateien je Wahl werden dynamisch aus `open_data.json` gelesen
- Vor 2009 bzw. für Landtagswahlen stellt die Stadt keine Open-Data-CSVs bereit; ältere Ergebnisse gibt es nur interaktiv über die [Wahl-Datenbank](https://statistik.wuppertal.de/wahl_statistik/) (per Cloudflare gegen automatisierten Abruf geschützt)
