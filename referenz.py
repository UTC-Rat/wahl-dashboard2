from data import partei_kanonisch

# Ueberregionale Referenz-Ergebnisse in Prozent der gueltigen Stimmen.
# Quellen: Der Bundeswahlleiter (Bundestags-/Europawahlen, Zweitstimmen
# bundesweit, CDU und CSU zusammengefasst) und die Landeswahlleiterin NRW
# (Landtagswahlen, Zweitstimmen). Alle Werte wurden gegen die amtlichen
# Endergebnisse verifiziert.
REFERENZEN = {
    "BT 2009": {
        "typ": "Bundestagswahl 2009 (bundesweit)",
        "ergebnis": {"CDU/CSU": 33.8, "SPD": 23.0, "FDP": 14.6, "Die Linke": 11.9, "GRÜNE": 10.7, "PIRATEN": 2.0},
    },
    "BT 2013": {
        "typ": "Bundestagswahl 2013 (bundesweit)",
        "ergebnis": {"CDU/CSU": 41.5, "SPD": 25.7, "Die Linke": 8.6, "GRÜNE": 8.4, "FDP": 4.8, "AfD": 4.7, "PIRATEN": 2.2},
    },
    "BT 2017": {
        "typ": "Bundestagswahl 2017 (bundesweit)",
        "ergebnis": {"CDU/CSU": 32.9, "SPD": 20.5, "AfD": 12.6, "FDP": 10.7, "Die Linke": 9.2, "GRÜNE": 8.9},
    },
    "BT 2021": {
        "typ": "Bundestagswahl 2021 (bundesweit)",
        "ergebnis": {"SPD": 25.7, "CDU/CSU": 24.1, "GRÜNE": 14.8, "FDP": 11.5, "AfD": 10.3, "Die Linke": 4.9, "FREIE WÄHLER": 2.4},
    },
    "BT 2025": {
        "typ": "Bundestagswahl 2025 (bundesweit)",
        "ergebnis": {"CDU/CSU": 28.5, "AfD": 20.8, "SPD": 16.4, "GRÜNE": 11.6, "Die Linke": 8.8, "BSW": 4.97, "FDP": 4.3},
    },
    "EU 2009": {
        "typ": "Europawahl 2009 (bundesweit)",
        "ergebnis": {"CDU/CSU": 37.9, "SPD": 20.8, "GRÜNE": 12.1, "FDP": 11.0, "Die Linke": 7.5},
    },
    "EU 2014": {
        "typ": "Europawahl 2014 (bundesweit)",
        "ergebnis": {"CDU/CSU": 35.3, "SPD": 27.3, "GRÜNE": 10.7, "Die Linke": 7.4, "AfD": 7.1, "FDP": 3.4},
    },
    "EU 2019": {
        "typ": "Europawahl 2019 (bundesweit)",
        "ergebnis": {"CDU/CSU": 28.9, "GRÜNE": 20.5, "SPD": 15.8, "AfD": 11.0, "Die Linke": 5.5, "FDP": 5.4, "Die PARTEI": 2.4, "FREIE WÄHLER": 2.2},
    },
    "EU 2024": {
        "typ": "Europawahl 2024 (bundesweit)",
        "ergebnis": {"CDU/CSU": 30.0, "AfD": 15.9, "SPD": 13.9, "GRÜNE": 11.9, "BSW": 6.2, "FDP": 5.2, "FREIE WÄHLER": 2.7, "Die Linke": 2.7, "Volt": 2.6},
    },
    "LT NRW 2005": {
        "typ": "Landtagswahl NRW 2005",
        "ergebnis": {"CDU/CSU": 44.8, "SPD": 37.1, "GRÜNE": 6.2, "FDP": 6.2},
    },
    "LT NRW 2010": {
        "typ": "Landtagswahl NRW 2010",
        "ergebnis": {"CDU/CSU": 34.6, "SPD": 34.5, "GRÜNE": 12.1, "FDP": 6.7, "Die Linke": 5.6},
    },
    "LT NRW 2012": {
        "typ": "Landtagswahl NRW 2012",
        "ergebnis": {"SPD": 39.1, "CDU/CSU": 26.3, "GRÜNE": 11.3, "FDP": 8.6, "Die Linke": 2.5},
    },
    "LT NRW 2017": {
        "typ": "Landtagswahl NRW 2017",
        "ergebnis": {"CDU/CSU": 33.0, "SPD": 31.2, "FDP": 12.6, "AfD": 7.4, "GRÜNE": 6.4, "Die Linke": 4.9},
    },
    "LT NRW 2022": {
        "typ": "Landtagswahl NRW 2022",
        "ergebnis": {"CDU/CSU": 35.7, "SPD": 26.7, "GRÜNE": 18.2, "FDP": 5.9, "AfD": 5.4, "Die Linke": 2.1},
    },
}

# Zuordnung der Wuppertaler Wahlen zu zeitlich naehen Referenzwahlen.
# BT-/EU-Wahlen werden mit ihrem eigenen bundesweiten Ergebnis verglichen.
REFERENZ_TYPEN = ["Bund/Europa", "Landtagswahl NRW"]

WAHL_REFERENZ = {
    "Bundestagswahl 2025": {"Bund/Europa": "BT 2025"},
    "Bundestagswahl 2021": {"Bund/Europa": "BT 2021"},
    "Bundestagswahl 2017": {"Bund/Europa": "BT 2017"},
    "Bundestagswahl 2013": {"Bund/Europa": "BT 2013"},
    "Bundestagswahl 2009": {"Bund/Europa": "BT 2009"},
    "Europawahl 2024": {"Bund/Europa": "EU 2024"},
    "Europawahl 2019": {"Bund/Europa": "EU 2019"},
    "Europawahl 2014": {"Bund/Europa": "EU 2014"},
    "Europawahl 2009": {"Bund/Europa": "EU 2009"},
    "Ratswahl 2009": {"Bund/Europa": "BT 2009", "Landtagswahl NRW": "LT NRW 2010"},
    "Ratswahl 2014": {"Bund/Europa": "EU 2014", "Landtagswahl NRW": "LT NRW 2012"},
    "Ratswahl 2020": {"Bund/Europa": "BT 2021", "Landtagswahl NRW": "LT NRW 2022"},
    "Ratswahl 2025": {"Bund/Europa": "BT 2025", "Landtagswahl NRW": "LT NRW 2022"},
    "Integrationsratswahl 2014": {"Bund/Europa": "EU 2014", "Landtagswahl NRW": "LT NRW 2012"},
    "Integrationsratswahl 2020": {"Bund/Europa": "BT 2021", "Landtagswahl NRW": "LT NRW 2022"},
    "Integrationsratswahl 2025": {"Bund/Europa": "BT 2025", "Landtagswahl NRW": "LT NRW 2022"},
    "Oberbürgermeisterwahl 2009": {"Bund/Europa": "BT 2009", "Landtagswahl NRW": "LT NRW 2010"},
    "Oberbürgermeisterwahl 2015": {"Bund/Europa": "BT 2013", "Landtagswahl NRW": "LT NRW 2017"},
    "OB-Stichwahl 2015": {"Bund/Europa": "BT 2013", "Landtagswahl NRW": "LT NRW 2017"},
    "Oberbürgermeisterwahl 2020": {"Bund/Europa": "BT 2021", "Landtagswahl NRW": "LT NRW 2022"},
    "OB-Stichwahl 2020": {"Bund/Europa": "BT 2021", "Landtagswahl NRW": "LT NRW 2022"},
}

REFERENZ_LABELS = {
    "Bund/Europa": "Bund/Europa (zeitlich nächste Wahl)",
    "Landtagswahl NRW": "Landtagswahl NRW (zeitlich nächste)",
}


def referenz_schluessel(name: str) -> str | None:
    """Uebersetzt ein Wuppertaler Parteien-Label in den Referenz-Schluessel.

    OB-Kandidaten ('Andreas Mucke, SPD') liefern den Parteienteil; lokale
    Listen ohne bundesweites Pendant (z. B. WfW/FW) ergeben None.
    """
    name = name.strip()
    if "," in name:
        name = name.rsplit(",", 1)[1].strip()
    if name == "CDU/GRÜNE":
        return None
    if name in ("CDU", "CDU Europaliste"):
        return "CDU/CSU"
    return partei_kanonisch(name)

