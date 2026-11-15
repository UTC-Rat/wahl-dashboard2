import itertools
import re

import pandas as pd
import plotly.express as px
import streamlit as st

from data import (
    VERGLEICHS_EBENEN,
    WAHLEN,
    lade_ergebnisse,
    lade_von_url,
    partei_farbe,
    verfuegbare_ebenen,
    vergleich_url,
)
from referenz import REFERENZEN, REFERENZ_LABELS, REFERENZ_TYPEN, WAHL_REFERENZ, referenz_schluessel

st.set_page_config(page_title="Wahlergebnisse Wuppertal", page_icon="🗳️", layout="wide")
st.title("🗳️ Wahlergebnisse Wuppertal")
st.caption("Datenquelle: wahlen.wuppertal.de (Open Data) · Bundestags-, Landtags-, Rats-, Europa- und Oberbürgermeisterwahlen")


@st.cache_data(ttl=86400, show_spinner="Lade Wahlergebnisse ...")
def ergebnisse(wahlname: str, ebene: str) -> pd.DataFrame:
    return lade_ergebnisse(WAHLEN[wahlname], ebene)


@st.cache_data(ttl=86400, show_spinner=False)
def ebenen_fuer(wahlname: str) -> list[str]:
    return list(verfuegbare_ebenen(WAHLEN[wahlname]))


@st.cache_data(ttl=86400, show_spinner="Lade Vergleichsdaten ...")
def vergleichsdaten(wahlname: str, level: str) -> pd.DataFrame | None:
    url = vergleich_url(WAHLEN[wahlname], level)
    if url is None:
        return None
    return lade_von_url(WAHLEN[wahlname], url)


def farben_fuer(parteien: list[str]) -> dict[str, str]:
    rest = itertools.cycle(px.colors.qualitative.Prism)
    zuordnung = {}
    for partei in parteien:
        farbe = partei_farbe(partei)
        zuordnung[partei] = farbe if farbe else next(rest)
    zuordnung["Sonstige"] = "#9E9E9E"
    return zuordnung


def jahr(name: str) -> int:
    treffer = re.search(r"(20\d{2})", name)
    return int(treffer.group(1)) if treffer else 0


modus = st.radio("Ansicht", ["Einzelwahl", "Wahlvergleich", "Überregional"], horizontal=True)

if modus == "Einzelwahl":
    wahlname = st.selectbox("Wahl", list(WAHLEN))
    try:
        ebenen = ebenen_fuer(wahlname)
    except Exception as e:
        st.error(
            "Die Daten von wahlen.wuppertal.de konnten nicht geladen werden. "
            f"Bitte später erneut versuchen. (Fehler: {type(e).__name__}: {e})"
        )
        st.stop()

    ebene = st.radio("Ebene", ebenen, horizontal=True)
    df = ergebnisse(wahlname, ebene)

    if ebene == "Stadt gesamt":
        daten = df
        gebiet = df["gebiet-name"].iloc[0]
    else:
        gebiet = st.selectbox("Gebiet", sorted(df["gebiet-name"].unique()))
        daten = df[df["gebiet-name"] == gebiet]

    gesamt = daten.groupby("Partei", as_index=False)["Stimmen"].sum()
    gesamt["Anteil %"] = (gesamt["Stimmen"] / gesamt["Stimmen"].sum() * 100).round(1)
    gesamt = gesamt.sort_values("Stimmen", ascending=False)

    titel = f"{wahlname} – {daten['Stimmart'].iloc[0]} – {gebiet}"
    farben = farben_fuer(list(gesamt["Partei"]))

    links, rechts = st.columns([2, 1])
    with links:
        fig = px.bar(
            gesamt.iloc[::-1], x="Stimmen", y="Partei", color="Partei", text="Anteil %",
            title=titel, labels={"Stimmen": "Stimmen"},
            color_discrete_map=farben,
        )
        fig.update_layout(showlegend=False, height=460)
        st.plotly_chart(fig, use_container_width=True)

        kleine = gesamt[gesamt["Anteil %"] < 2]
        torten_daten = gesamt[gesamt["Anteil %"] >= 2]
        if len(kleine) > 0:
            torten_daten = pd.concat(
                [torten_daten, pd.DataFrame([{"Partei": "Sonstige", "Stimmen": kleine["Stimmen"].sum()}])],
                ignore_index=True,
            )
        fig_torte = px.pie(
            torten_daten, names="Partei", values="Stimmen", hole=0.35,
            title=f"Stimmenanteile – {gebiet}",
            color="Partei", color_discrete_map=farben,
        )
        fig_torte.update_traces(textinfo="percent", textposition="inside")
        fig_torte.update_layout(height=460, legend_title_text="Partei")
        st.plotly_chart(fig_torte, use_container_width=True)
    with rechts:
        st.metric("Gebiete in der Auswahl", daten["gebiet-name"].nunique())
        st.metric("Parteien / Kandidaturen", len(gesamt))
        st.metric("Stimmen insgesamt", f"{gesamt['Stimmen'].sum():,}".replace(",", "."))
        st.dataframe(
            gesamt[["Partei", "Stimmen", "Anteil %"]],
            use_container_width=True, hide_index=True, height=420,
        )

elif modus == "Wahlvergleich":
    st.subheader("Wahlvergleich")
    st.caption("Mehrere Wahlen, eine Ebene, ein Gebiet – Stimmen und Anteile im Zeitverlauf")

    auswahl = st.multiselect(
        "Wahlen (mehrfach auswählbar)",
        list(WAHLEN),
        default=["Ratswahl 2025", "Ratswahl 2020", "Ratswahl 2014", "Ratswahl 2009"],
    )
    level = st.radio("Ebene", VERGLEICHS_EBENEN, horizontal=True)

    if not auswahl:
        st.info("Bitte mindestens eine Wahl auswählen.")
        st.stop()

    rohdaten: dict[str, pd.DataFrame] = {}
    fehlend: list[str] = []
    for wahlname in auswahl:
        df = vergleichsdaten(wahlname, level)
        if df is None:
            fehlend.append(wahlname)
            continue
        rohdaten[wahlname] = df

    if fehlend:
        st.warning(f"Für die Ebene „{level}“ keine Daten verfügbar: {', '.join(fehlend)}")
    if not rohdaten:
        st.info("Für diese Kombination aus Wahlen und Ebene liegen keine Daten vor. Wähle eine andere Ebene.")
        st.stop()

    sortierte_wahlen = sorted(rohdaten, key=lambda w: (jahr(w), w))

    if level == "Stadt gesamt":
        gebiet = "Stadt Wuppertal"
    else:
        gemeinsame = set.intersection(*[set(df["gebiet-name"].unique()) for df in rohdaten.values()])
        if not gemeinsame:
            st.error("Die gewählten Wahlen haben auf dieser Ebene keine gemeinsamen Gebiete (z. B. Stimmbezirke vs. Kommunalwahlbezirke). Bitte Ebene wechseln.")
            st.stop()
        gebiet = st.selectbox("Gebiet", sorted(gemeinsame))

    pro_wahl: dict[str, pd.Series] = {}
    for wahlname, df in rohdaten.items():
        ausschnitt = df if level == "Stadt gesamt" else df[df["gebiet-name"] == gebiet]
        pro_wahl[wahlname] = ausschnitt.groupby("Partei")["Stimmen"].sum()

    stimmen_matrix = pd.DataFrame({
        w: pro_wahl[w] for w in sortierte_wahlen
    }).reindex(sortierte_wahlen, axis=1)

    alle_parteien = sorted(stimmen_matrix.index)
    letzte = sortierte_wahlen[-1]
    vorschlag = [p for p in stimmen_matrix[letzte].sort_values(ascending=False).head(5).index if p in alle_parteien]
    parteien = st.multiselect("Parteien im Vergleich", alle_parteien, default=vorschlag)

    if not parteien:
        st.info("Bitte mindestens eine Partei auswählen.")
        st.stop()

    farben = farben_fuer(parteien)

    lang = stimmen_matrix.loc[parteien].stack().rename("Stimmen").reset_index()
    lang.columns = ["Partei", "Wahl", "Stimmen"]
    gesamt_je_wahl = stimmen_matrix.sum(axis=0)
    lang["Anteil %"] = lang.apply(
        lambda z: round(z["Stimmen"] / gesamt_je_wahl[z["Wahl"]] * 100, 1) if gesamt_je_wahl[z["Wahl"]] else 0.0,
        axis=1,
    )

    st.markdown(f"### Gebiet: {gebiet}")
    b1, b2 = st.columns(2)
    with b1:
        fig_balken = px.bar(
            lang, x="Wahl", y="Stimmen", color="Partei", barmode="group",
            title=f"Stimmen je Partei – {gebiet}",
            color_discrete_map=farben,
            category_orders={"Wahl": sortierte_wahlen, "Partei": parteien},
        )
        fig_balken.update_layout(height=460, legend_title_text="Partei")
        st.plotly_chart(fig_balken, use_container_width=True)
    with b2:
        fig_linie = px.line(
            lang, x="Wahl", y="Anteil %", color="Partei", markers=True,
            title=f"Anteil in % – {gebiet}",
            color_discrete_map=farben,
            category_orders={"Wahl": sortierte_wahlen, "Partei": parteien},
        )
        fig_linie.update_layout(height=460, legend_title_text="Partei", yaxis_ticksuffix=" %")
        st.plotly_chart(fig_linie, use_container_width=True)

    st.markdown("#### Tabelle: Stimmen (Anteil %)")
    tabelle = stimmen_matrix.loc[parteien].copy()
    anteile = (tabelle / tabelle.sum(axis=0) * 100).round(1)
    formatiert = pd.DataFrame(index=tabelle.index, columns=tabelle.columns, dtype=object)
    for w in tabelle.columns:
        formatiert[w] = [
            f"{int(tabelle.loc[p, w]):,} ({anteile.loc[p, w]:.1f} %)".replace(",", ".")
            if tabelle.loc[p, w] > 0 else "–"
            for p in tabelle.index
        ]
    formatiert.index.name = "Partei"
    st.dataframe(formatiert, use_container_width=True, height=420)

else:
    st.subheader("Überregionaler Vergleich")
    st.caption("Wuppertaler Stadtergebnis vs. überregionales Ergebnis – Abstand in Prozentpunkten (pp)")

    auswahl = st.multiselect(
        "Wahlen (mehrfach auswählbar)",
        list(WAHLEN),
        default=["Bundestagswahl 2025", "Bundestagswahl 2021", "Bundestagswahl 2017"],
    )
    if not auswahl:
        st.info("Bitte mindestens eine Wahl auswählen.")
        st.stop()

    kommunal = [w for w in auswahl if len(WAHL_REFERENZ[w]) > 1]
    if kommunal:
        typ_label = st.radio(
            "Referenz für Kommunalwahlen",
            [REFERENZ_LABELS[t] for t in REFERENZ_TYPEN],
            horizontal=True,
        )
        typ = next(t for t, label in REFERENZ_LABELS.items() if label == typ_label)
    else:
        typ = "Bund/Europa"

    zeilen = []
    for wahlname in sorted(auswahl, key=lambda w: (jahr(w), w)):
        df = ergebnisse(wahlname, "Stadt gesamt")
        stimmen = df.groupby("Partei")["Stimmen"].sum()
        gesamt = stimmen.sum()
        referenz = REFERENZEN[WAHL_REFERENZ[wahlname][typ]]
        for partei, stimme in stimmen.items():
            schluessel = referenz_schluessel(partei)
            if schluessel is None or schluessel not in referenz["ergebnis"]:
                continue
            wuppertal_pct = stimme / gesamt * 100
            zeilen.append({
                "Wahl": wahlname,
                "Partei": schluessel,
                "Wuppertal %": round(wuppertal_pct, 1),
                "Überregional %": referenz["ergebnis"][schluessel],
                "Abstand (pp)": round(wuppertal_pct - referenz["ergebnis"][schluessel], 1),
            })

    if not zeilen:
        st.info("Für diese Wahlen liegen keine vergleichbaren Parteien vor.")
        st.stop()

    daten = pd.DataFrame(zeilen)
    sortierte_wahlen = sorted(daten["Wahl"].unique(), key=lambda w: (jahr(w), w))

    alle_parteien = sorted(daten["Partei"].unique())
    letzte = sortierte_wahlen[-1]
    in_allen = [p for p in alle_parteien if len(daten[daten["Partei"] == p]) == len(sortierte_wahlen)]
    basis = daten[(daten["Wahl"] == letzte) & (daten["Partei"].isin(in_allen))]
    if basis.empty:
        basis = daten[daten["Wahl"] == letzte]
    vorschlag = list(basis.sort_values("Wuppertal %", ascending=False).head(3)["Partei"])
    parteien = st.multiselect("Parteien im Vergleich", alle_parteien, default=vorschlag)
    if not parteien:
        st.info("Bitte mindestens eine Partei auswählen.")
        st.stop()

    ansicht = daten[daten["Partei"].isin(parteien)]
    farben = farben_fuer(parteien)

    b1, b2 = st.columns(2)
    with b1:
        lang = ansicht.melt(
            id_vars=["Wahl", "Partei"],
            value_vars=["Wuppertal %", "Überregional %"],
            var_name="Ebene", value_name="Prozent",
        )
        lang["Ebene"] = lang["Ebene"].replace({"Wuppertal %": "Wuppertal", "Überregional %": "Überregional"})
        fig_balken = px.bar(
            lang, x="Wahl", y="Prozent", color="Partei", pattern_shape="Ebene", barmode="group",
            title="Wuppertal vs. Überregional (Prozent) – schraffiert = überregional",
            color_discrete_map=farben,
            category_orders={"Wahl": sortierte_wahlen, "Partei": parteien},
        )
        fig_balken.update_layout(height=460)
        st.plotly_chart(fig_balken, use_container_width=True)
    with b2:
        fig_abstand = px.line(
            ansicht, x="Wahl", y="Abstand (pp)", color="Partei", markers=True,
            title="Abstand in Prozentpunkten (Wuppertal minus Überregional)",
            color_discrete_map=farben,
            category_orders={"Wahl": sortierte_wahlen, "Partei": parteien},
        )
        fig_abstand.add_hline(y=0, line_dash="dot", line_color="grey")
        fig_abstand.update_layout(height=460, legend_title_text="Partei")
        st.plotly_chart(fig_abstand, use_container_width=True)

    st.markdown("#### Tabelle: Wuppertal % / Überregional % / Abstand (pp)")
    tabelle = pd.DataFrame(index=parteien, columns=sortierte_wahlen, dtype=object)
    for _, z in ansicht.iterrows():
        tabelle.loc[z["Partei"], z["Wahl"]] = (
            f"{z['Wuppertal %']:.1f} / {z['Überregional %']:.1f} ({z['Abstand (pp)']:+.1f})"
        )
    tabelle.index.name = "Partei"
    st.dataframe(tabelle, use_container_width=True, height=420)

    st.caption(
        "Referenzdaten: Bundestags-/Europawahlen bundesweit (Der Bundeswahlleiter) und "
        "Landtagswahlen NRW (Landeswahlleiterin), jeweils Zweitstimmenanteile; "
        "CDU und CSU zusammengefasst. Landtagswahlen werden mit ihrem NRW-Landesergebnis "
        "verglichen, Kommunalwahlen mit der zeitlich nächsten überregionalen Wahl."
    )
