import pandas as pd
import plotly.express as px
import streamlit as st

from data import WAHLEN, lade_ergebnisse, verfuegbare_ebenen

st.set_page_config(page_title="Wahlergebnisse Wuppertal", page_icon="🗳️", layout="wide")
st.title("🗳️ Wahlergebnisse Wuppertal")
st.caption("Datenquelle: wahlen.wuppertal.de (Open Data) · Bundestags-, Rats-, Europa-, Integrationsrats- und Oberbürgermeisterwahlen")


@st.cache_data(ttl=600, show_spinner="Lade Wahlergebnisse ...")
def ergebnisse(wahlname: str, ebene: str) -> pd.DataFrame:
    return lade_ergebnisse(WAHLEN[wahlname], ebene)


@st.cache_data(ttl=600, show_spinner=False)
def ebenen_fuer(wahlname: str) -> list[str]:
    return list(verfuegbare_ebenen(WAHLEN[wahlname]))


wahlname = st.selectbox("Wahl", list(WAHLEN))
try:
    ebenen = ebenen_fuer(wahlname)
except Exception:
    st.error("Die Daten von wahlen.wuppertal.de konnten nicht geladen werden. Bitte später erneut versuchen.")
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

links, rechts = st.columns([2, 1])
with links:
    fig = px.bar(
        gesamt.iloc[::-1], x="Stimmen", y="Partei", color="Partei", text="Anteil %",
        title=titel, labels={"Stimmen": "Stimmen"},
        color_discrete_sequence=px.colors.qualitative.Prism,
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
        color_discrete_sequence=px.colors.qualitative.Prism,
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
