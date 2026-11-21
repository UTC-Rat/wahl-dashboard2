"""Aggregation der Wahlergebnisse auf die Landtagswahlkreise 2027.

Amtlicher Zuschnitt zur Landtagswahl am 25.04.2027 (identisch zu 2022,
Quelle: Anlage zu § 13 LWahlG NRW):
- 32 Wuppertal I: Barmen 51, 53; Bezirke Heckinghausen, Langerfeld-Beyenburg,
  Oberbarmen, Ronsdorf (KWB 61-92)
- 33 Wuppertal II: Elberfeld 01-05, Uellendahl-Katernberg (21-24),
  Barmen 52, 54, 55
- 34 Wuppertal III - Solingen II: von Wuppertal Elberfeld-KWB 06
  Friedrichsberg sowie die Stadtbezirke Elberfeld-West (11-13), Vohwinkel
  (31-33) und Cronenberg (41-42); von Solingen der Stadtbezirk Gräfrath
  (KWB 51-53) sowie von Mitte die KWB 15 und 16. Vom KWB 12 Innenstadt-Süd
  gehoert nur der Stimmbezirk 123 zum Wahlkreis; auf
  Kommunalwahlbezirks-Ebene kann er nicht abgetrennt werden und wird daher
  nicht beruecksichtigt (kleine Abweichung).

Die Aggregation der Landtagswahl 2022 wird gegen die amtlichen
Wahlkreis-Ergebnisse des Wahlleiters NRW kontrolliert (siehe _KONTROLLE).
"""
from __future__ import annotations

import io
import re

import pandas as pd

from data import WAHLEN, _hole, partei_kanonisch, verfuegbare_ebenen

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
        "solingen_nummern": None,
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
        "solingen_nummern": None,
    },
    "Wuppertal III - Solingen II (Wahlkreis 34)": {
        "beschreibung": (
            "Von **Wuppertal**: Stadtbezirk **Elberfeld-West** (11 Brill-Arrenberg, "
            "12 Nützenberg-Zoo, 13 Sonnborn-Varresbeck), **Vohwinkel** (31-33), "
            "**Cronenberg** (41-42) sowie vom Stadtbezirk Elberfeld der KWB "
            "06 Friedrichsberg. Von **Solingen** (Quelle: wahlen.kdvz.nrw): "
            "Stadtbezirk **Gräfrath** (KWB 51-53) sowie vom Stadtbezirk Mitte "
            "die KWB 15 Klauberg-Hasseldelle-Kohlfurth und 16 "
            "Kannenhof-Meigen-Halfeshof. Vom KWB 12 Innenstadt-Süd gehoert nur "
            "der Stimmbezirk 123 zum Wahlkreis und bleibt auf Bezirksebene "
            "unberücksichtigt."
        ),
        "teile": [
            "06 Friedrichsberg (W)", "11 Brill-Arrenberg (W)", "12 Nützenberg-Zoo (W)",
            "13 Sonnborn-Varresbeck (W)", "31 Vohwinkel-Ost (W)", "32 Vohwinkel-West (W)",
            "33 Vohwinkel-Nord (W)", "41 Cronenberg-Süd (W)", "42 Cronenberg-Nord (W)",
            "15 Klauberg-Hasseldelle-Kohlfurth (So)", "16 Kannenhof-Meigen-Halfeshof (So)",
            "51-53 Gräfrath (So)",
        ],
        "nummern": ["06", "11", "12", "13", "31", "32", "33", "41", "42"],
        "solingen_nummern": ["15", "16", "51", "52", "53"],
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

# ---------------------------------------------------------------- Solingen
# Solingen wird von der kdvz Rhein-Erft-Rur gehostet
# (wahlen.kdvz.nrw, AGS 05122000, Portalsystem identisch zu Wuppertal).
SOLINGEN_BASIS = "https://wahlen.kdvz.nrw/production/{wahlcode}/05122000/daten/opendata/"

# Nur Wahlen mit gesicherter Partei-Zuordnung; die Spalten-Zuordnung
# fuer bw2025/EW2024 wird zur Laufzeit gegen amtliche Referenzwerte
# kalibriert (votemanager-Spaltenreihenfolge weicht je Stadt ab).
_SOLINGEN_QUELLEN = {
    "lw2022": "Open-Data-05122000-Landtagswahl-Kommunalwahlbezirk.csv",
    "bw2025": "Open-Data-05122000-Wahl-zum-Deutschen-Bundestag-Kommunalwahlbezirk.csv",
    "EW2024": "Open-Data-05122000-Europawahl-Kommunalwahlbezirk.csv",
}

# Amtliche Referenz: (Partei, Spaltensumme) bzw. (Partei, Anteil in %).
# LW2022: feste Zuordnung wie Wuppertal (durch amtliche WK-34-Kontrolle
# bestaetigt). BW2025: Prozentanteile der gueltigen Zweitstimmen lt.
# Wahlbericht der Stadt Solingen. EW2024: Stimmen lt. kdvz-Ergebnisseite.
_SOLINGEN_REF = {
    "bw2025": [
        ("CDU", 28.02), ("SPD", 19.70), ("AfD", 17.48), ("GRÜNE", 12.01),
        ("Die Linke", 8.85), ("FDP", 4.72), ("BSW", 4.63),
    ],
    "EW2024": [
        ("CDU", 19283), ("GRÜNE", 9031), ("SPD", 11103),
        ("AfD", 8710), ("FDP", 4435), ("Die Linke", 1539),
    ],
}

# Amtliche Kontrollwerte (gültige Zweitstimmen, Wahlleiter NRW):
# Wahlkreis 34 Wuppertal III - Solingen II, Landtagswahl 2022.
_KONTROLLE_WK34 = {
    "lw2022": {
        "gültige Zweitstimmen": 45429,
        "CDU": 14339, "SPD": 12693, "GRÜNE": 8767, "FDP": 2760,
        "AfD": 2701, "Die Linke": 1165,
    },
}
# Amtliches Endergebnis Europawahl 2024, Stadt Solingen gesamt (kdvz) -
# kontrolle der Solinger Spaltenzuordnung.
_KONTROLLE_SOLINGEN = {
    "EW2024": {
        "CDU": 19283, "GRÜNE": 9031, "SPD": 11103, "AfD": 8710,
        "FDP": 4435, "Die Linke": 1539,
    },
}


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


def _pruefe(summen: dict[str, int], kontrolle: dict[str, int], kontext: str,
            toleranz: int = 5) -> None:
    """Vergleicht Summen mit amtlichen Werten."""
    for merkmal, soll in kontrolle.items():
        if merkmal == "gültige Zweitstimmen":
            continue
        hat = int(summen.get(merkmal, 0))
        if abs(hat - soll) > toleranz:
            raise ValueError(
                f"Kontrolle fehlgeschlagen ({kontext}): {merkmal} "
                f"berechnet {hat}, amtlich {soll}"
            )


def _kalibriere_zuordnung(summen: dict[str, int], refs: list[tuple[str, float]],
                          gesamt: int | None) -> dict[str, str]:
    """Ordnet CSV-Spalten Parteien anhand amtlicher Referenzwerte zu.

    refs: (Partei, Spaltensumme absolut) oder (Partei, Anteil in Prozent,
    wenn gesamt angegeben). Erfordert eindeutige Zuordnung, sonst Fehler.
    """
    zuordnung: dict[str, str] = {}
    belegt: set[str] = set()
    for partei, wert in refs:
        kandidaten: list[str] = []
        for spalte, st in summen.items():
            if spalte in belegt:
                continue
            if gesamt is None:
                if abs(st - wert) <= 5:
                    kandidaten.append(spalte)
            else:
                anteil = st / gesamt * 100
                if abs(anteil - wert) <= 0.2:
                    kandidaten.append(spalte)
        if len(kandidaten) != 1:
            if gesamt is None:
                diagnose = " | ".join(
                    f"{spalte}={st}" for spalte, st in sorted(summen.items())
                )
            else:
                diagnose = " | ".join(
                    f"{spalte}={st} ({st / gesamt * 100:.2f} %)"
                    for spalte, st in sorted(summen.items())
                )
            raise ValueError(
                f"Spaltenkalibrierung fehlgeschlagen für {partei} "
                f"({len(kandidaten)} Kandidaten: {kandidaten}); gesamt={gesamt}; "
                f"Spalten: {diagnose}"
            )
        zuordnung[kandidaten[0]] = partei
        belegt.add(kandidaten[0])
    return zuordnung


def _lade_solingen(wahlname: str) -> pd.DataFrame:
    """Solinger Ergebnisse auf KWB-Ebene aus dem kdvz-Archiv.

    Liefert ein Langformat (gebiet-nr, Partei, Stimmen) über alle 26 KWBs
    oder wirft einen Fehler, wenn keine gesicherte Quelle vorliegt.
    """
    wahl = WAHLEN[wahlname]
    datei = _SOLINGEN_QUELLEN.get(wahl["wahlcode"])
    if datei is None:
        raise ValueError(
            f"Keine gesicherte Solingen-Quelle für {wahlname} "
            "(nur Wahlen mit amtlich gesicherter Spaltenzuordnung verfügbar)"
        )
    url = SOLINGEN_BASIS.format(wahlcode=wahl["wahlcode"]) + datei
    csv_text = _hole(url).text
    df = pd.read_csv(io.StringIO(csv_text), sep=";", encoding="utf-8", dtype=str)
    if wahl["wahlcode"] == "lw2022":
        # Feste Zuordnung (NRW-Landeslisten-Reihenfolge, wie Wuppertal);
        # bestaetigt durch die amtliche WK-34-Kontrolle unten.
        zuordnung = {
            "F1": "CDU", "F2": "SPD", "F3": "FDP", "F4": "AfD", "F5": "GRÜNE",
            "F6": "Die Linke", "F7": "PIRATEN", "F8": "Die PARTEI",
            "F9": "FREIE WÄHLER", "F10": "BIG", "F11": "ÖDP",
            "F12": "Volksabstimmung", "F13": "MLPD", "F14": "DIE VIOLETTEN",
            "F15": "Gesundheitsforschung", "F16": "ZENTRUM", "F17": "DKP",
            "F18": "dieBasis", "F19": "DSP", "F20": "Die Urbane.",
            "F21": "LIEBE", "F22": "FAMILIE", "F23": "neo",
            "F24": "Die Humanisten", "F25": "PdF", "F26": "LfK",
            "F27": "Tierschutzpartei", "F28": "Team Todenhöfer", "F29": "Volt",
        }
        spalten = [c for c in df.columns if c in zuordnung]
        if len(spalten) != len(zuordnung):
            raise ValueError(
                f"Solingen-CSV für {wahlname} hat unerwartete Spalten "
                f"({len(spalten)}/{len(zuordnung)} gefunden)"
            )
        df_stimmen = df[spalten].replace({"---": "0", "": "0"}).fillna("0").astype(int)
        gesamt = None
    else:
        spalten = [c for c in df.columns if re.fullmatch(r"[DF][0-9]+", c)]
        if not spalten:
            raise ValueError(f"Keine Stimmen-Spalten für {wahlname} gefunden")
        df_stimmen = df[spalten].replace({"---": "0", "": "0"}).fillna("0").astype(int)
        summen = {Spalte: int(df_stimmen[Spalte].sum()) for Spalte in spalten}
        gesamt = sum(summen.values())
        if gesamt <= 0:
            raise ValueError(f"Solingen-CSV für {wahlname} ohne Stimmen")
        zuordnung = _kalibriere_zuordnung(
            summen, _SOLINGEN_REF[wahl["wahlcode"]], gesamt
        )
        spalten = list(zuordnung)

    for Spalte in spalten:
        if int(df_stimmen[Spalte].sum()) <= 0:
            raise ValueError(
                f"Solingen-CSV für {wahlname}: Spalte {Spalte} ohne Stimmen "
                "(Spaltenzuordnung prüfen)"
            )
    df_stimmen = df_stimmen.copy()
    kontrolle = _KONTROLLE_SOLINGEN.get(wahl["wahlcode"])
    if kontrolle:
        _pruefe(
            {partei: int(df_stimmen[spalte].sum())
             for spalte, partei in zuordnung.items()},
            kontrolle,
            f"Solingen gesamt, {wahlname}",
        )
    df_stimmen["gebiet-nr"] = df["gebiet-nr"]
    lang = df_stimmen.rename(
        columns={code: partei_kanonisch(name) for code, name in zuordnung.items()}
    ).melt(id_vars="gebiet-nr", var_name="Partei", value_name="Stimmen")
    return lang[lang["Stimmen"] > 0]


def lade_wahlkreis_ergebnisse(wahlname: str) -> pd.DataFrame:
    """Aggregiert die Ergebnisse einer Wahl auf die Landtagswahlkreise 2027.

    Liefert ein Langformat mit den Spalten Wahl, Wahlkreis, Partei, Stimmen.
    """
    lang = _lade_bezirksebene(wahlname)
    lang["gebiet-nr"] = lang["gebiet-nr"].str.strip()
    solingen_vorhanden = WAHLEN[wahlname]["wahlcode"] in _SOLINGEN_QUELLEN
    sol_lang = _lade_solingen(wahlname) if solingen_vorhanden else None
    if sol_lang is not None:
        sol_lang["gebiet-nr"] = sol_lang["gebiet-nr"].str.strip()

    teile: list[pd.DataFrame] = []
    for wk, info in WAHLKREISE.items():
        zug = lang[lang["gebiet-nr"].isin(info["nummern"])]
        if info.get("solingen_nummern"):
            if sol_lang is None:
                raise ValueError(
                    f"Solingen-Daten für {wahlname} nicht verfügbar - "
                    "Wahlkreis 34 wird für diese Wahl übersprungen"
                )
            zug_so = sol_lang[sol_lang["gebiet-nr"].isin(info["solingen_nummern"])]
            zug_so = zug_so.groupby("Partei", as_index=False)["Stimmen"].sum()
            zug = pd.concat([zug, zug_so], ignore_index=True)
        gesamt = zug.groupby("Partei", as_index=False)["Stimmen"].sum()
        gesamt["Wahlkreis"] = wk
        gesamt["Wahl"] = wahlname
        teile.append(gesamt)
    ergebnis = pd.concat(teile, ignore_index=True)

    kontrolle = _KONTROLLE_WK34.get(WAHLEN[wahlname]["wahlcode"])
    if kontrolle and ergebnis["Wahlkreis"].str.contains("Wahlkreis 34").any():
        wk34 = ergebnis[ergebnis["Wahlkreis"].str.contains("Wahlkreis 34")]
        # Toleranz: der nicht abtrennbare Stimmbezirk 123 (KWB 12) verursacht
        # eine kleine planmaessige Abweichung; Zeilenvertauschungen (Tausende
        # Stimmen) fallen weiterhin auf.
        _pruefe(
            dict(zip(wk34["Partei"], wk34["Stimmen"])),
            kontrolle,
            f"Wahlkreis 34, {wahlname}",
            toleranz=1200,
        )
        wk34_summe = int(wk34["Stimmen"].sum())
        soll = kontrolle.get("gültige Zweitstimmen")
        if soll and abs(wk34_summe - soll) > 1500:
            raise ValueError(
                f"Kontrolle fehlgeschlagen (Wahlkreis 34, {wahlname}): "
                f"gültige Zweitstimmen {wk34_summe}, amtlich {soll}"
            )
    return ergebnis
