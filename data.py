import io
import json
import time
from pathlib import Path

import pandas as pd
import requests

AGS = "05124000"
BASIS = "https://wahlen.wuppertal.de/{wahlcode}/" + AGS + "/daten/opendata"

# Statische Fallback-Kopien der Open-Data-Dateien: Wahlergebnisse sind
# historisch unveraenderlich, daher kann das Dashboard bei Netzwerkproblemen
# komplett offline aus dem Repo arbeiten.
FALLBACK = Path(__file__).parent / "daten"

EBENEN = {"Stadt gesamt": "Gemeinde", "Stadtbezirke": "Stadtbezirk",
          "Kommunalwahlbezirke": "Kommunalwahlbezirk", "Wahlbezirke": "Wahlbezirk",
          "Stimmbezirke": "Stimmbezirk"}

# Alle Parteien-Zuordnungen wurden gegen die amtlichen Endergebnisse
# (Gemeinde-Summen der CSVs vs. Praesentations-JSONs) verifiziert.
WAHLEN = {
    "Bundestagswahl 2025": {
        "wahlcode": "bw2025",
        "slug": "Wahl-zum-Deutschen-Bundestag",
        "stimmentyp": "Zweitstimmen",
        "parteien": {
        "F1": "SPD",
        "F2": "CDU",
        "F3": "GRÜNE",
        "F4": "FDP",
        "F5": "AfD",
        "F6": "Die Linke",
        "F7": "Tierschutzpartei",
        "F8": "Die PARTEI",
        "F9": "dieBasis",
        "F10": "Team Todenhöfer",
        "F11": "FREIE WÄHLER",
        "F12": "Volt",
        "F13": "MLPD",
        "F14": "Partei des Fortschritts",
        "F15": "BÜNDNIS DEUTSCHLAND",
        "F16": "BSW",
        "F17": "MERA25",
        "F18": "WerteUnion",
        "F19": "Versöhnen statt spalten (Füllmich)",
        "F20": "Die Gerechtigkeitspartei",
        "F21": "Dialog statt Aufrüstung"
},
    },
    "Bundestagswahl 2021": {
        "wahlcode": "BW2021",
        "slug": "Wahl-zum-Deutschen-Bundestag",
        "stimmentyp": "Zweitstimmen",
        "parteien": {
        "F1": "CDU",
        "F2": "SPD",
        "F3": "FDP",
        "F4": "AfD",
        "F5": "GRÜNE",
        "F6": "DIE LINKE",
        "F7": "Die PARTEI",
        "F8": "Tierschutzpartei",
        "F9": "PIRATEN",
        "F10": "FREIE WÄHLER",
        "F11": "NPD",
        "F12": "ÖDP",
        "F13": "V-Partei³",
        "F14": "Gesundheitsforschung",
        "F15": "MLPD",
        "F16": "Die Humanisten",
        "F17": "DKP",
        "F18": "SGP",
        "F19": "dieBasis",
        "F20": "Bündnis C",
        "F21": "du.",
        "F22": "LIEBE",
        "F23": "LKR",
        "F24": "PdF",
        "F25": "LfK",
        "F26": "Team Todenhöfer",
        "F27": "Volt",
        "F28": "Ehrensache"
},
    },
    "Bundestagswahl 2017": {
        "wahlcode": "BW2017",
        "slug": "Wahl-zum-Deutschen-Bundestag",
        "stimmentyp": "Zweitstimmen",
        "parteien": {
        "F1": "CDU",
        "F2": "SPD",
        "F3": "GRÜNE",
        "F4": "DIE LINKE",
        "F5": "FDP",
        "F6": "AfD",
        "F7": "PIRATEN",
        "F8": "NPD",
        "F9": "Die PARTEI",
        "F10": "FREIE WÄHLER",
        "F11": "Volksabstimmung",
        "F12": "ÖDP",
        "F13": "MLPD",
        "F14": "SGP",
        "F15": "Allianz Deutscher Demokraten",
        "F16": "BGE",
        "F17": "DiB",
        "F18": "DKP",
        "F19": "DM",
        "F20": "Die Humanisten",
        "F21": "Gesundheitsforschung",
        "F22": "Tierschutzpartei",
        "F23": "V-Partei³"
},
    },
    "Bundestagswahl 2013": {
        "wahlcode": "bw2013",
        "slug": "Wahl-zum-Deutschen-Bundestag",
        "stimmentyp": "Zweitstimmen",
        "parteien": {
        "F1": "CDU",
        "F2": "SPD",
        "F3": "FDP",
        "F4": "GRÜNE",
        "F5": "DIE LINKE",
        "F6": "PIRATEN",
        "F7": "NPD",
        "F8": "REP",
        "F9": "Bündnis 21/RRP",
        "F10": "Volksabstimmung",
        "F11": "ÖDP",
        "F12": "MLPD",
        "F13": "BüSo",
        "F14": "PSG",
        "F15": "AfD",
        "F16": "BIG",
        "F17": "pro Deutschland",
        "F18": "DIE RECHTE",
        "F19": "FREIE WÄHLER",
        "F20": "Partei der Nichtwähler",
        "F21": "PARTEI DER VERNUNFT",
        "F22": "Die PARTEI"
},
    },
    "Bundestagswahl 2009": {
        "wahlcode": "bw2009",
        "slug": "Wahl-zum-Deutschen-Bundestag",
        "stimmentyp": "Zweitstimmen",
        "parteien": {
        "F1": "SPD",
        "F2": "CDU",
        "F3": "FDP",
        "F4": "GRÜNE",
        "F5": "DIE LINKE",
        "F6": "NPD",
        "F7": "Tierschutzpartei",
        "F8": "FAMILIE",
        "F9": "REP",
        "F10": "Volksabstimmung",
        "F11": "MLPD",
        "F12": "PSG",
        "F13": "ZENTRUM",
        "F14": "BüSo",
        "F15": "DVU",
        "F16": "ÖDP",
        "F17": "PIRATEN",
        "F18": "RRP",
        "F19": "RENTNER"
},
    },
    "Ratswahl 2025": {
        "wahlcode": "kw2025",
        "slug": "Ratswahl",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "SPD",
        "D2": "CDU",
        "D3": "GRÜNE",
        "D4": "FDP",
        "D5": "Die Linke",
        "D6": "AfD",
        "D7": "WfW/Freie Wähler",
        "D8": "Die PARTEI",
        "D9": "dieBasis",
        "D10": "BSW",
        "D11": "DAVA",
        "D12": "GfW",
        "D13": "Volt",
        "D14": "Gathe für alle!"
},
    },
    "Ratswahl 2020": {
        "wahlcode": "kw2020",
        "slug": "Ratswahl",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "SPD",
        "D2": "CDU",
        "D3": "GRÜNE",
        "D4": "DIE LINKE",
        "D5": "FDP",
        "D6": "WfW/FW",
        "D7": "AfD",
        "D8": "PRO Wuppertal",
        "D9": "Die PARTEI",
        "D10": "Tierschutzpartei",
        "D11": "V-Partei³"
},
    },
    "Ratswahl 2014": {
        "wahlcode": "kw2014",
        "slug": "Ratswahl",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "CDU",
        "D2": "SPD",
        "D3": "GRÜNE",
        "D4": "FDP",
        "D5": "DIE LINKE",
        "D6": "WfW/FW",
        "D7": "REP",
        "D8": "PRO NRW",
        "D9": "PIRATEN",
        "D10": "AfD"
},
    },
    "Ratswahl 2009": {
        "wahlcode": "kw2009",
        "slug": "Ratswahl",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "CDU",
        "D2": "SPD",
        "D3": "GRÜNE",
        "D4": "WfW/FW",
        "D5": "FDP",
        "D6": "DIE LINKE",
        "D7": "REP",
        "D8": "BILDUNG!",
        "D9": "NPD"
},
    },
    "Europawahl 2024": {
        "wahlcode": "EW2024",
        "slug": "Europawahl",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "CDU",
        "D2": "GRÜNE",
        "D3": "SPD",
        "D4": "AfD",
        "D5": "FDP",
        "D6": "DIE LINKE",
        "D7": "Die PARTEI",
        "D8": "Tierschutzpartei",
        "D9": "PIRATEN",
        "D10": "Volt",
        "D11": "FAMILIE",
        "D12": "FREIE WÄHLER",
        "D13": "ÖDP",
        "D14": "BIG",
        "D15": "MERA25",
        "D16": "TIERSCHUTZ hier!",
        "D17": "PdH",
        "D18": "HEIMAT",
        "D19": "Bündnis C",
        "D20": "Verjüngungsforschung",
        "D21": "MENSCHLICHE WELT",
        "D22": "MLPD",
        "D23": "DKP",
        "D24": "SGP",
        "D25": "ABG",
        "D26": "dieBasis",
        "D27": "BÜNDNIS DEUTSCHLAND",
        "D28": "BSW",
        "D29": "DAVA",
        "D30": "KLIMALISTE",
        "D31": "LETZTE GENERATION",
        "D32": "PDV",
        "D33": "PdF",
        "D34": "V-Partei³"
},
    },
    "Europawahl 2019": {
        "wahlcode": "EW2019",
        "slug": "Europawahl",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "CDU",
        "D2": "SPD",
        "D3": "GRÜNE",
        "D4": "AfD",
        "D5": "DIE LINKE",
        "D6": "FDP",
        "D7": "PIRATEN",
        "D8": "Tierschutzpartei",
        "D9": "NPD",
        "D10": "Die PARTEI",
        "D11": "FAMILIE",
        "D12": "FREIE WÄHLER",
        "D13": "Volksabstimmung",
        "D14": "ÖDP",
        "D15": "DKP",
        "D16": "MLPD",
        "D17": "BP",
        "D18": "SGP",
        "D19": "TIERSCHUTZ hier!",
        "D20": "Tierschutzallianz",
        "D21": "Bündnis C",
        "D22": "BIG",
        "D23": "BGE",
        "D24": "DIE DIREKTE!",
        "D25": "Demokratie in Europa - DiEM25",
        "D26": "III. Weg",
        "D27": "Die Grauen",
        "D28": "DIE RECHTE",
        "D29": "DIE VIOLETTEN",
        "D30": "LIEBE",
        "D31": "DIE FRAUEN",
        "D32": "Graue Panther",
        "D33": "LKR",
        "D34": "MENSCHLICHE WELT",
        "D35": "NL",
        "D36": "ÖkoLinX",
        "D37": "Die Humanisten",
        "D38": "PARTEI FÜR DIE TIERE",
        "D39": "Gesundheitsforschung",
        "D40": "Volt"
},
    },
    "Europawahl 2014": {
        "wahlcode": "kw2014",
        "slug": "Europawahl",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "CDU",
        "D2": "SPD",
        "D3": "GRÜNE",
        "D4": "FDP",
        "D5": "DIE LINKE",
        "D6": "REP",
        "D7": "Tierschutzpartei",
        "D8": "PIRATEN",
        "D9": "FAMILIE",
        "D10": "FREIE WÄHLER",
        "D11": "Volksabstimmung",
        "D12": "PBC",
        "D13": "ÖDP",
        "D14": "CM",
        "D15": "AUF",
        "D16": "DKP",
        "D17": "BP",
        "D18": "PSG",
        "D19": "BüSo",
        "D20": "AfD",
        "D21": "PRO NRW",
        "D22": "MLPD",
        "D23": "NPD",
        "D24": "Die PARTEI"
},
    },
    "Europawahl 2009": {
        "wahlcode": "ew2009",
        "slug": "Europawahl",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "CDU",
        "D2": "SPD",
        "D3": "GRÜNE",
        "D4": "FDP",
        "D5": "DIE LINKE",
        "D6": "REP",
        "D7": "Tierschutzpartei",
        "D8": "FAMILIE",
        "D9": "DIE FRAUEN",
        "D10": "Volksabstimmung",
        "D11": "PBC",
        "D12": "ÖDP",
        "D13": "CM",
        "D14": "DKP",
        "D15": "AUFBRUCH",
        "D16": "PSG",
        "D17": "BüSo",
        "D18": "50Plus",
        "D19": "AUF",
        "D20": "BP",
        "D21": "DVU",
        "D22": "DIE GRAUEN",
        "D23": "DIE VIOLETTEN",
        "D24": "EDE",
        "D25": "FBI/Freie Wähler",
        "D26": "Gerechtigkeit braucht Bürgerrechte - Wir danken für Ihr Vertrauen!",
        "D27": "FW FREIE WÄHLER",
        "D28": "Newropeans",
        "D29": "PIRATEN",
        "D30": "RRP",
        "D31": "RENTNER"
},
    },
    "Landtagswahl 2022": {
        "wahlcode": "lw2022",
        "slug": "Landtagswahl",
        "stimmentyp": "Zweitstimmen",
        "parteien": {
        "F1": "CDU",
        "F2": "SPD",
        "F3": "FDP",
        "F4": "AfD",
        "F5": "GRÜNE",
        "F6": "Die Linke",
        "F7": "PIRATEN",
        "F8": "Die PARTEI",
        "F9": "FREIE WÄHLER",
        "F10": "BIG",
        "F11": "ÖDP",
        "F12": "Volksabstimmung",
        "F13": "MLPD",
        "F14": "DIE VIOLETTEN",
        "F15": "Gesundheitsforschung",
        "F16": "ZENTRUM",
        "F17": "DKP",
        "F18": "dieBasis",
        "F19": "DSP",
        "F20": "Die Urbane.",
        "F21": "LIEBE",
        "F22": "FAMILIE",
        "F23": "neo",
        "F24": "Die Humanisten",
        "F25": "PdF",
        "F26": "LfK",
        "F27": "Tierschutzpartei",
        "F28": "Team Todenhöfer",
        "F29": "Volt"
},
    },
    "Landtagswahl 2017": {
        "wahlcode": "lw2017",
        "slug": "Landtagswahl",
        "stimmentyp": "Zweitstimmen",
        "parteien": {
        "F1": "SPD",
        "F2": "CDU",
        "F3": "GRÜNE",
        "F4": "FDP",
        "F5": "PIRATEN",
        "F6": "Die Linke",
        "F7": "NPD",
        "F8": "Die PARTEI",
        "F9": "FREIE WÄHLER",
        "F10": "BIG",
        "F11": "FBI/FWG",
        "F12": "ÖDP",
        "F13": "Volksabstimmung",
        "F14": "Tierschutzpartei",
        "F15": "Allianz Deutscher Demokraten",
        "F16": "AfD",
        "F17": "AUFBRUCH C",
        "F18": "BGE",
        "F19": "DBD",
        "F20": "DKP",
        "F21": "ZENTRUM",
        "F22": "DIE RECHTE",
        "F23": "REP",
        "F24": "DIE VIOLETTEN",
        "F25": "JED",
        "F26": "MLPD",
        "F27": "PAN",
        "F28": "Gesundheitsforschung",
        "F29": "PARTEILOSE WG „BRD“",
        "F30": "Schöner Leben",
        "F31": "V-Partei³"
},
    },
    "Landtagswahl 2012": {
        "wahlcode": "lw2012",
        "slug": "Landtagswahl",
        "stimmentyp": "Zweitstimmen",
        "parteien": {
        "F1": "CDU",
        "F2": "SPD",
        "F3": "GRÜNE",
        "F4": "FDP",
        "F5": "Die Linke",
        "F6": "PIRATEN",
        "F7": "PRO NRW",
        "F8": "NPD",
        "F9": "Tierschutzpartei",
        "F10": "FAMILIE",
        "F11": "BIG",
        "F12": "Die PARTEI",
        "F13": "ÖDP",
        "F14": "FBI/Freie Wähler",
        "F15": "AUF",
        "F16": "FREIE WÄHLER",
        "F17": "PARTEI DER VERNUNFT"
},
    },
    "Landtagswahl 2010": {
        "wahlcode": "lw2010",
        "slug": "Landtagswahl",
        "stimmentyp": "Zweitstimmen",
        "parteien": {
        "F1": "CDU",
        "F2": "SPD",
        "F3": "GRÜNE",
        "F4": "FDP",
        "F5": "NPD",
        "F6": "Die Linke",
        "F7": "REP",
        "F8": "ÖDP",
        "F9": "BüSo",
        "F10": "PBC",
        "F11": "Tierschutzpartei",
        "F12": "FAMILIE",
        "F13": "Die PARTEI",
        "F14": "ZENTRUM",
        "F15": "BGD",
        "F16": "AUF",
        "F17": "PIRATEN",
        "F18": "ddp",
        "F19": "Freie Union",
        "F20": "RENTNER",
        "F21": "PRO NRW",
        "F22": "DIE VIOLETTEN",
        "F23": "BIG",
        "F24": "Volksabstimmung",
        "F25": "FBI/Freie Wähler"
},
    },
    "Oberbürgermeisterwahl 2020": {
        "wahlcode": "kw2020",
        "slug": "Wahl-des-der-Oberbuergermeisters-in",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "Andreas Mucke, SPD",
        "D2": "Uwe Schneidewind, CDU/GRÜNE",
        "D3": "Bernhard Sander, DIE LINKE",
        "D4": "Marcel Hafke, FDP",
        "D5": "Henrik Dahlmann, WfW/FW",
        "D6": "Mira Lehner, Die PARTEI",
        "D7": "Panagiotis Paschalis, Einzelbewerber Paschalis"
},
    },
    "OB-Stichwahl 2020": {
        "wahlcode": "kw2020",
        "slug": "Stichwahl-des-der-Oberbuergermeisters-in",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "Andreas Mucke, SPD",
        "D2": "Uwe Schneidewind, CDU/GRÜNE"
},
    },
    "Oberbürgermeisterwahl 2015": {
        "wahlcode": "ob2015",
        "slug": "Wahl-des-der-Oberbuergermeisters-in",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "Andreas Mucke, SPD",
        "D2": "Peter Jung, CDU",
        "D3": "Marc Schulz, GRÜNE",
        "D4": "Gunhild Böth, DIE LINKE",
        "D5": "Beate Petersen, WfW/FW",
        "D6": "Markus Stranzenbach, PRO NRW",
        "D7": "Björn Werner, Die PARTEI"
},
    },
    "OB-Stichwahl 2015": {
        "wahlcode": "ob2015",
        "slug": "Stichwahl-des-der-Oberbuergermeisters-in",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "Andreas Mucke, SPD",
        "D2": "Peter Jung, CDU"
},
    },
    "Oberbürgermeisterwahl 2009": {
        "wahlcode": "kw2009",
        "slug": "Wahl-des-der-Oberbuergermeisters-in",
        "stimmentyp": "Stimmen",
        "parteien": {
        "D1": "Peter Jung, CDU",
        "D2": "Dietmar Bell, SPD",
        "D3": "Lorenz Bahr, GRÜNE",
        "D4": "Ralf Streuf, WfW/FW",
        "D5": "Ingrid Pfeiffer, FDP",
        "D6": "Gerd-Peter Zielezinski, DIE LINKE",
        "D7": "Wolfgang Pohlmann, REP",
        "D8": "Michael Schnorr, NPD"
},
    },
}


def _hole(url: str) -> requests.Response:
    fehler: Exception | None = None
    for versuch in range(3):
        try:
            antwort = requests.get(
                url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (Wahl-Dashboard)"}
            )
            antwort.raise_for_status()
            return antwort
        except requests.RequestException as ausnahme:
            fehler = ausnahme
            if versuch < 2:
                time.sleep(2 ** versuch)
    raise fehler


def verfuegbare_ebenen(wahl: dict) -> dict[str, str]:
    basis = BASIS.format(wahlcode=wahl["wahlcode"])
    try:
        open_data = _hole(f"{basis}/open_data.json").json()
    except (requests.RequestException, ValueError):
        lokal = FALLBACK / wahl["wahlcode"] / "open_data.json"
        if not lokal.exists():
            raise
        open_data = json.loads(lokal.read_text(encoding="utf-8"))
    urls = {}
    for eintrag in open_data.get("csvs", []):
        for label, muster in EBENEN.items():
            if eintrag["url"].endswith(f"-{wahl['slug']}-{muster}.csv"):
                urls[label] = f"{basis}/{eintrag['url']}"
    return urls


def lade_von_url(wahl: dict, url: str) -> pd.DataFrame:
    try:
        csv_text = _hole(url).text
    except requests.RequestException:
        teile = url.split("/")
        lokal = FALLBACK / teile[3] / teile[-1]
        if not lokal.exists():
            raise
        csv_text = lokal.read_text(encoding="utf-8")
    df = pd.read_csv(io.StringIO(csv_text), sep=";", encoding="utf-8", dtype=str)

    spalten = [c for c in df.columns if c in wahl["parteien"]]
    if not spalten:
        raise ValueError("Keine Parteien-Spalten in der CSV gefunden")

    df[spalten] = df[spalten].replace({"---": None, "": None}).fillna(0).astype(int)
    stimmen = df[["gebiet-name"] + spalten].rename(
        columns={code: partei_kanonisch(name) for code, name in wahl["parteien"].items()}
    )
    lang = stimmen.melt(id_vars="gebiet-name", var_name="Partei", value_name="Stimmen")
    lang["Stimmart"] = wahl["stimmentyp"]
    return lang[lang["Stimmen"] > 0]


_KANONISCH = {
    "die linke": "Die Linke",
    "die grauen": "Die Grauen",
}


def partei_kanonisch(name: str) -> str:
    """Vereinheitlicht Schreibvarianten (z. B. 'DIE LINKE' vs. 'Die Linke'),
    damit der Wahlvergleich Parteien ueber Jahre hinweg korrekt zusammenfuehrt."""
    return _KANONISCH.get(name.strip().lower(), name)


def lade_ergebnisse(wahl: dict, ebene: str = "Wahlbezirke") -> pd.DataFrame:
    urls = verfuegbare_ebenen(wahl)
    if ebene not in urls:
        raise ValueError(f"Ebene '{ebene}' nicht verfuegbar: {list(urls)}")
    return lade_von_url(wahl, urls[ebene])


VERGLEICHS_EBENEN = ["Stadt gesamt", "Stadtbezirke", "Kommunalwahlbezirke", "Stimmbezirke"]


def vergleich_url(wahl: dict, level: str) -> str | None:
    """Aufloesung der Vergleichs-Ebene je Wahl.

    Rats-/OB-Archive nennen ihre 33 Kommunalwahlbezirke 'Wahlbezirke';
    Bundestags-/Europawahlen haben dort 255 Stimmbezirke. Landtagsarchive
    liefern Kommunalwahlbezirke und Stimmbezirke direkt.
    """
    urls = verfuegbare_ebenen(wahl)
    kommunal_archiv = wahl["wahlcode"].lower().startswith(("kw", "ob"))
    if level == "Stadt gesamt":
        return urls.get("Stadt gesamt")
    if level == "Stadtbezirke":
        return urls.get("Stadtbezirke")
    if level == "Kommunalwahlbezirke":
        if "Kommunalwahlbezirke" in urls:
            return urls["Kommunalwahlbezirke"]
        if kommunal_archiv and "Wahlbezirke" in urls:
            return urls["Wahlbezirke"]
        return None
    if level == "Stimmbezirke":
        if "Stimmbezirke" in urls:
            return urls["Stimmbezirke"]
        if not kommunal_archiv and "Wahlbezirke" in urls:
            return urls["Wahlbezirke"]
        return None
    return None

# Uebliche Parteifarben (medienuebliche Kanonisierung)
PARTEI_FARBEN = {
    "SPD": "#E3000F",
    "CDU": "#000000",
    "GRÜNE": "#46962B",
    "FDP": "#FFED00",
    "AfD": "#009EE3",
    "Die Linke": "#BE3075",
    "BSW": "#8E44AD",
    "Volt": "#502379",
    "Die PARTEI": "#644387",
    "FREIE WÄHLER": "#F58220",
    "Tierschutzpartei": "#0072BC",
    "PIRATEN": "#FF8800",
    "dieBasis": "#696969",
    "NPD": "#7B5B3A",
    "REP": "#5C4033",
    "ÖDP": "#E8A000",
    "MLPD": "#CC0000",
    "DKP": "#D2122E",
    "FAMILIE": "#F49AB5",
    "Sonstige": "#9E9E9E",
}

_FARBREGELN = [
    ("TIERSCHUTZ", "#0072BC"),
    ("DIE PARTEI", "#644387"),
    ("PARTEI DER VERNUNFT", "#B5651D"),
    ("SPD", "#E3000F"),
    ("CDU", "#000000"),
    ("CSU", "#008CA0"),
    ("GRUN", "#46962B"),
    ("FDP", "#FFED00"),
    ("AFD", "#009EE3"),
    ("LINKE", "#BE3075"),
    ("BSW", "#8E44AD"),
    ("VOLT", "#502379"),
    ("FREIE WAHLER", "#F58220"),
    ("WFW", "#F58220"),
    ("PIRATEN", "#FF8800"),
    ("DIEBASIS", "#696969"),
    ("NPD", "#7B5B3A"),
    ("REP", "#5C4033"),
    ("ODP", "#E8A000"),
    ("MLPD", "#CC0000"),
    ("DKP", "#D2122E"),
    ("FAMILIE", "#F49AB5"),
    ("HEIMAT", "#6B8E23"),
    ("SONSTIGE", "#9E9E9E"),
]

_ERSETZUNGEN = str.maketrans({"Ä": "A", "Ö": "O", "Ü": "U", "ß": "ss", "³": "3"})


def partei_farbe(name: str) -> str | None:
    normalisiert = name.upper().translate(_ERSETZUNGEN).strip()
    for muster, farbe in _FARBREGELN:
        if muster in normalisiert:
            return farbe
    return None
