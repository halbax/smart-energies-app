# app.py - hlavní spouštěcí skript Streamlit aplikace

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from src import optimizer, pdf_generator
import os

st.set_page_config(page_title="Smart Energies - Cenová nabídka", layout="wide")
st.title("Smart Energies | Optimalizace nákupu elektřiny")

uploaded_file = st.file_uploader("Nahraj odběrový diagram (Excel nebo CSV)", type=["xlsx", "csv"])

with st.form("inputs"):
    st.subheader("Parametry nabídky")
    client_name = st.text_input("Jméno klienta")

    col1, col2 = st.columns(2)
    with col1:
        cal_price = st.number_input("Cena CAL [€/MWh]", min_value=0.0)
        q_price = st.number_input("Cena Q [€/MWh]", min_value=0.0)
        m_price = st.number_input("Cena M [€/MWh]", min_value=0.0)
        spot_price = st.number_input("Cena SPOT [€/MWh]", min_value=0.0)

    with col2:
        marze_fix = st.number_input("Marže fixní produkty [€/MWh]", min_value=0.0, value=2.0)
        marze_spot = st.number_input("Marže SPOT [€/MWh]", min_value=0.0, value=2.5)
        spot_avg = st.number_input("Průměrná SPOT cena [€/MWh]", min_value=0.0)
        validity = st.date_input("Platnost nabídky do")

    submit = st.form_submit_button("Vypočítat nabídku")

if uploaded_file and submit:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = [col.strip() for col in df.columns]
    date_col = [col for col in df.columns if 'date' in col.lower() or 'čas' in col.lower()][0]
    mwh_col = [col for col in df.columns if 'mwh' in col.lower() or 'spotřeba' in col.lower()][0]

    df['datetime'] = pd.to_datetime(df[date_col])
    df['MWh'] = df[mwh_col].astype(str).str.replace(',', '.').astype(float)
    df = df[['datetime', 'MWh']].dropna()
    df = df.set_index('datetime')

    result = optimizer.optimize(df)

    st.success("Optimalizace dokončena")
    st.dataframe(result['summary'])

    fig, ax = plt.subplots(figsize=(12, 4))
    df['MWh'].plot(ax=ax, label="Spotřeba")
    plt.title("Pokrytí odběru")
    plt.legend()
    st.pyplot(fig)

    if st.button("Generovat PDF nabídku"):
        pdf_generator.create_pdf(client_name, result, cal_price, q_price, m_price, spot_price, marze_fix, marze_spot, spot_avg, validity)
        st.success("PDF nabídka byla vygenerována do složky outputs/")

    result['summary'].to_excel(f"archive/{client_name}_nabidka.xlsx")
    st.info("Výsledek byl uložen i do archivu.")
