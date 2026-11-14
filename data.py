import io

import pandas as pd
import requests

AGS = "05124000"
BASIS = f"https://wahlen.wuppertal.de/{{wahl}}/{AGS}/daten"

WAHLEN = {
    "Bundestagswahl 2025": "bw2025",
    "Ratswahl 2025": "kw2025",
    "Europawahl 2024": "EW2024",
}

STIMMENTYP = {"bw2025": ("F", "Zweitstimmen"), "kw2025": ("D", "Stimmen"), "EW2024": ("D", "Stimmen")}

PARTYEI = {
    "bw2025": {
        "D1": "SPD", "D2": "CDU", "D3": "GRÜNE", "D4": "FDP", "D5": "AfD",
        "D6": "Die Linke", "D7": "Tierschutzpartei", "D8": "Die PARTEI",
        "D9": "dieBasis", "D10": "Team Todenhöfer", "D11": "FREIE WÄHLER",
        "D12": "Volt", "D13": "MLPD", "D14": "Partei des Fortschritts",
        "D15": "BÜNDNIS DEUTSCHLAND", "D16": "BSW", "D17": "MERA25",
        "D18": "WerteUnion", "D19": "Versöhnen statt spalten (Füllmich)",
        "D20": "Die Gerechtigkeitspartei", "D21": "Dialog statt Aufrüstung",
        "F1": "SPD", "F2": "CDU", "F3": "GRÜNE", "F4": "FDP", "F5": "AfD",
        "F6": "Die Linke", "F7": "Tierschutzpartei", "F8": "Die PARTEI",
        "F9": "dieBasis", "F10": "Team Todenhöfer", "F11": "FREIE WÄHLER",
        "F12": "Volt", "F13": "MLPD", "F14": "Partei des Fortschritts",
        "F15": "BÜNDNIS DEUTSCHLAND", "F16": "BSW", "F17": "MERA25",
        "F18": "WerteUnion", "F19": "Versöhnen statt spalten (Füllmich)",
        "F20": "Die Gerechtigkeitspartei", "F21": "Dialog statt Aufrüstung",
    },
    "kw2025": {
        "D1": "SPD", "D2": "CDU", "D3": "GRÜNE", "D4": "FDP", "D5": "Die Linke",
        "D6": "AfD", "D7": "WfW/Freie Wähler", "D8": "Die PARTEI", "D9": "dieBasis",
        "D10": "BSW", "D11": "DAVA", "D12": "GfW", "D13": "Volt", "D14": "Gathe für alle!",
    },
    "EW2024": {
        "D1": "CDU", "D2": "GRÜNE", "D3": "SPD", "D4": "AfD", "D5": "FDP",
        "D6": "DIE LINKE", "D7": "Die PARTEI", "D8": "Tierschutzpartei",
        "D9": "PIRATEN", "D10": "Volt", "D11": "FAMILIE", "D12": "FREIE WÄHLER",
        "D13": "ÖDP", "D14": "BIG", "D15": "MERA25", "D16": "TIERSCHUTZ hier!",
        "D17": "PdH", "D18": "HEIMAT", "D19": "Bündnis C", "D20": "Verjüngungsforschung",
        "D21": "MENSCHLICHE WELT", "D22": "MLPD", "D23": "DKP", "D24": "SGP",
        "D25": "ABG", "D26": "dieBasis", "D27": "BÜNDNIS DEUTSCHLAND", "D28": "BSW",
        "D29": "DAVA", "D30": "KLIMALISTE", "D31": "LETZTE GENERATION", "D32": "PDV",
        "D33": "PdF", "D34": "V-Partei³",
    },
}

EBENEN = {"Gemeinde": "Gemeinde", "Stadtbezirke": "Stadtbezirk", "Wahlbezirke": "Wahlbezirk"}


def _hole(url: str) -> requests.Response:
    antwort = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 (Wahl-Dashboard)"})
    antwort.raise_for_status()
    return antwort


def verfuegbare_ebenen(wahl: str) -> dict[str, str]:
    open_data = _hole(f"{BASIS.format(wahl=wahl)}/opendata/open_data.json").json()
    urls = {}
    for eintrag in open_data.get("csvs", []):
        for label, muster in EBENEN.items():
            if eintrag["url"].endswith(f"-{muster}.csv"):
                urls[label] = f"{BASIS.format(wahl=wahl)}/opendata/{eintrag['url']}"
    return urls


def lade_ergebnisse(wahl: str, ebene: str = "Wahlbezirke") -> pd.DataFrame:
    praefix, stimmentyp = STIMMENTYP[wahl]
    urls = verfuegbare_ebenen(wahl)
    if ebene not in urls:
        raise ValueError(f"Ebene '{ebene}' nicht verfügbar für {wahl}: {list(urls)}")
    csv_text = _hole(urls[ebene]).text
    df = pd.read_csv(io.StringIO(csv_text), sep=";", encoding="utf-8", dtype=str)

    mapping = PARTYEI[wahl]
    spalten = [c for c in df.columns if c in mapping]
    if not spalten:
        raise ValueError(f"Keine Parteien-Spalten ({praefix}1, {praefix}2, ...) in der CSV gefunden")

    df[spalten] = df[spalten].replace({"---": None, "": None}).fillna(0).astype(int)
    stimmen = df[["gebiet-name"] + spalten].rename(columns=mapping)
    lang = stimmen.melt(id_vars="gebiet-name", var_name="Partei", value_name="Stimmen")
    lang["Stimmart"] = stimmentyp
    return lang[lang["Stimmen"] > 0]
