import io

import pandas as pd
import requests

WAHLEN = {
    "Bundestag 2025": "bw2025",
    "Ratswahl 2025": "kw2025",
    "Europawahl 2024": "EW2024",
}

PARTYEI = {
    "F1": "SPD", "F2": "CDU", "F3": "Gruene", "F4": "FDP",
    "F5": "AfD", "F6": "Linke", "F7": "Tierschutzpartei",
    "F8": "Die PARTEI", "F9": "Basis", "F10": "Team Todenhoefer",
    "F11": "Freie Waehler", "F12": "Volt", "F16": "BSW",
}

AGS = "05124000"


def csv_url(wahlcode: str, ebene: str = "Wahlbezirk") -> str:
    datei = f"Open-Data-{AGS}-Wahlbezirk.csv"
    return f"https://wahlen.wuppertal.de/{wahlcode}/{AGS}/daten/opendata/{datei}"


def lade_ergebnisse(wahlcode: str) -> pd.DataFrame:
    url = csv_url(wahlcode)
    roh = requests.get(url, timeout=30)
    roh.raise_for_status()
    df = pd.read_csv(io.StringIO(roh.text), sep=";", encoding="utf-8")
    spalten = [c for c in PARTYEI if c in df.columns]
    stimmen = df[["gebiet-name"] + spalten].rename(columns=PARTYEI)
    lang = stimmen.melt(id_vars="gebiet-name", var_name="Partei", value_name="Stimmen")
    return lang[lang["Stimmen"].notna()]
