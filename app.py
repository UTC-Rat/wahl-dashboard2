import streamlit as st
import plotly.express as px

from data import WAHLEN, lade_ergebnisse

st.title("Wahlergebnisse Wuppertal")

wahl = st.selectbox("Wahl wählen", list(WAHLEN))
df = lade_ergebnisse(WAHLEN[wahl])

gebiet = st.selectbox("Gebiet", ["Alle"] + sorted(df["gebiet-name"].unique()))
daten = df if gebiet == "Alle" else df[df["gebiet-name"] == gebiet]

gesamt = daten.groupby("Partei", as_index=False)["Stimmen"].sum()
gesamt["Anteil %"] = (gesamt["Stimmen"] / gesamt["Stimmen"].sum() * 100).round(1)

fig = px.bar(gesamt.sort_values("Anteil %"), x="Anteil %", y="Partei",
             text="Anteil %", title=f"{wahl} – {gebiet}")
st.plotly_chart(fig, use_container_width=True)
st.dataframe(gesamt, use_container_width=True, hide_index=True)
