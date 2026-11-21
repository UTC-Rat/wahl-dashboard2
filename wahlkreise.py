"""Aggregation der Wahlergebnisse auf die Landtagswahlkreise 2027.

Die Landtagswahlkreise 32 Wuppertal I und 33 Wuppertal II bestehen aus
kommunalen Wahlbezirken (Kommunalwahlbezirken bzw. bei Rats-/OB-Archiven
"Wahlbezirken"). Zur Landtagswahl 2027 ist der Zuschnitt identisch zu 2022.
Die Aggregation wurde gegen die amtlichen Wahlkreis-Ergebnisse der
Landtagswahl 2022 verifiziert (Wahlleiter NRW).
"""
from __future__ import annotations

import io

import pandas as pd

from data import WAHLEN, _hole, partei_kanonisch, verfuegbare_ebenen

# Amtlicher Zuschnitt zur Landtagswahl am 25.04.2027
WAHLKREISE = {
    "Wuppertal I (Wahlkreis 32)": {
        "beschreibung": (
            "**Stadtbezirk Oberbarmen** (ganz), **Stadtbezirk Heckinghausen** (ganz), "
            "**Stadtbezirk Langerfeld-Beyenburg** (ganz), **Stadtbezirk Ronsdorf** (ganz), "
            "vom **Stadtbezirk Barmen**: 51 Barmen-Mitte, 53 Loh-Unterbarmen"
        ),
        "teile": [
            "61 Oberbarmen", "62 Wichlinghausen-Süd", "63 Wichlinghausen-Nord",
            "64 Nächstebreck", "71 Heckinghausen-West", "72 Heckinghausen-Ost",
            "81 Langerfeld-Nord", "82 Langerfeld-Süd-Beyenburg", "91 Ronsdorf-Ost",
            "92 Ronsdorf-West", "51 Barmen-Mitte", "53 Loh-Unterbarmen",
        ],
        "nummern": ["51", "53", "61", "62", "63", "64", "71", "72", "81", "82", "91", "92"],
    },
    "Wuppertal II (Wahlkreis 33)": {
        "beschreibung": (
            "**Stadtbezirk Uellendahl-Katernberg** (ganz), vom **Stadtbezirk Elberfeld**: "
            "01 Elberfeld-Mitte, 02 Hombüchel, 03 Höchsten, 04 Ostersbaum, 05 Grifflenberg, "
            "vom **Stadtbezirk Barmen**: 52 Sedansberg-Rott, 54 Clausen-Hatzfeld, "
            "55 Kothen-Lichtenplatz"
        ),
        "teile": [
            "01 Elberfeld-Mitte", "02 Hombüchel", "03 Höchsten", "04 Ostersbaum",
            "05 Grifflenberg", "21 Uellendahl-Ost", "22 Uellendahl-Mitte",
            "23 Uellendahl-West", "24 Katernberg", "52 Sedansberg-Rott",
            "54 Clausen-Hatzfeld", "55 Kothen-Lichtenplatz",
        ],
        "nummern": ["01", "02", "03", "04", "05", "21", "22", "23", "24", "52", "54", "55"],
    },
}

_TYP_REIHENFOLGE = ["Landtagswahl", "Bundestagswahl", "Ratswahl", "Europawahl"]


def _sortierschluessel(wahlname: str) -> tuple[int, int]:
    """Wahlen nach Typ (LT, BT, Rat, Europa) und Jahr absteigend sortieren."""
    for idx, praefix in enumerate(_TYP_REIHENFOLGE):
        if wahlname.startswith(praefix):
            jahr = int(wahlname.rsplit(" ", 1)[-1])
            return (idx, -jahr)
    return (9, -int(wahlname.rsplit(" ", 1)[-1]))


# Alle im Dashboard hinterlegten Bundestags-, Rats-, Europa- und
# Landtagswahlen (Oberbürgermeister-/Stichwahlen ausgeschlossen).
WAHLKREIS_WAHLEN = sorted(
    [
        w
        for w in WAHLEN
        if not w.startswith(("Oberbürgermeisterwahl", "OB-Stichwahl"))
    ],
    key=_sortierschluessel,
)


def _lade_bezirksebene(wahlname: str) -> pd.DataFrame:
    """Ergebnisse auf Kommunalwahlbezirks-Ebene (Nummer bleibt erhalten)."""
    wahl = WAHLEN[wahlname]
    urls = verfuegbare_ebenen(wahl)
    url = urls.get("Kommunalwahlbezirke")
    if url is None:
        # Rats-/OB-Archive nennen ihre Kommunalwahlbezirke "Wahlbezirke"
        url = urls.get("Wahlbezirke")
    if url is None:
        raise ValueError(f"Keine Bezirksebene verfügbar für {wahlname}")
    csv_text = _hole(url).text
    df = pd.read_csv(io.StringIO(csv_text), sep=";", encoding="utf-8", dtype=str)
    spalten = [c for c in df.columns if c in wahl["parteien"]]
    if not spalten:
        raise ValueError(f"Keine Parteien-Spalten in der CSV gefunden für {wahlname}")
    df[spalten] = df[spalten].replace({"---": None, "": None}).fillna(0).astype(int)
    lang = df[["gebiet-nr"] + spalten].rename(
        columns={code: partei_kanonisch(name) for code, name in wahl["parteien"].items()}
    ).melt(id_vars="gebiet-nr", var_name="Partei", value_name="Stimmen")
    return lang[lang["Stimmen"] > 0]


def lade_wahlkreis_ergebnisse(wahlname: str) -> pd.DataFrame:
    """Aggregiert die Ergebnisse einer Wahl auf die Landtagswahlkreise 2027.

    Liefert ein Langformat mit den Spalten Wahl, Wahlkreis, Partei, Stimmen.
    """
    lang = _lade_bezirksebene(wahlname)
    lang["gebiet-nr"] = lang["gebiet-nr"].str.strip()
    teile: list[pd.DataFrame] = []
    for wk, info in WAHLKREISE.items():
        zug = lang[lang["gebiet-nr"].isin(info["nummern"])]
        gesamt = zug.groupby("Partei", as_index=False)["Stimmen"].sum()
        gesamt["Wahlkreis"] = wk
        gesamt["Wahl"] = wahlname
        teile.append(gesamt)
    return pd.concat(teile, ignore_index=True)
