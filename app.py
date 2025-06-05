import streamlit as st
import pandas as pd
import plotly.express as px
import logging
from io import BytesIO
from src import lds_margin

# Session state for manual data entry
if 'manual_data' not in st.session_state:
    st.session_state['manual_data'] = pd.DataFrame(
        columns=lds_margin.REQUIRED_COLUMNS.values()
    )

logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(page_title="LDS Margin Calculator", layout="wide")
st.title("Výpočet marže lokálních distribučních sítí")

with st.sidebar:
    st.header("Konfigurace")
    country = st.selectbox("Země", ["ČR", "SK"])
    year = st.number_input("Rok výpočtu", min_value=2000, max_value=2100, value=2024)
    lds_type = st.selectbox("Typ LDS", ["bytová", "průmyslová", "komerční", "všechny"])
    input_method = st.selectbox(
        "Způsob zadání dat", ["Soubor/DB", "Ruční zadání"], index=0
    )

uploaded_file = st.file_uploader(
    "Vstupní data (Excel nebo CSV)", type=["xlsx", "csv"]
)
db_url = st.text_input("DB URL (nepovinné)")
query = st.text_area("SQL dotaz (nepovinné)")

if input_method == "Ruční zadání":
    st.subheader("Ruční zadání dat")
    with st.form("manual_data_form"):
        name = st.text_input("Název LDS")
        m_year = st.number_input(
            "Rok", min_value=2000, max_value=2100, value=int(year), key="year_manual"
        )
        type_row = st.selectbox(
            "Typ LDS (řádek)", ["bytová", "průmyslová", "komerční"], key="type_manual"
        )
        consumption = st.number_input("Celková spotřeba (MWh)", value=0.0)
        purchase = st.number_input("Náklady na nákup energie", value=0.0)
        revenue = st.number_input("Výnosy z prodeje energie", value=0.0)
        op_fixed = st.number_input("Náklady na provoz LDS (fixní)", value=0.0)
        op_variable = st.number_input("Náklady na provoz LDS (variabilní)", value=0.0)
        add_row = st.form_submit_button("Přidat řádek")
    if add_row:
        new_row = {
            lds_margin.REQUIRED_COLUMNS['LDS']: name,
            lds_margin.REQUIRED_COLUMNS['Consumption']: consumption,
            lds_margin.REQUIRED_COLUMNS['PurchaseCost']: purchase,
            lds_margin.REQUIRED_COLUMNS['Revenue']: revenue,
            lds_margin.REQUIRED_COLUMNS['OpCostFixed']: op_fixed,
            lds_margin.REQUIRED_COLUMNS['OpCostVariable']: op_variable,
            lds_margin.REQUIRED_COLUMNS['Type']: type_row,
            lds_margin.REQUIRED_COLUMNS['Year']: m_year,
        }
        st.session_state['manual_data'] = pd.concat(
            [st.session_state['manual_data'], pd.DataFrame([new_row])],
            ignore_index=True,
        )

    if not st.session_state['manual_data'].empty:
        st.dataframe(st.session_state['manual_data'])
        if st.button("Vymazat zadaná data"):
            st.session_state['manual_data'] = st.session_state['manual_data'][0:0]

if st.button("Načíst a analyzovat"):
    try:
        if input_method == "Ruční zadání":
            if st.session_state['manual_data'].empty:
                st.error("Nejsou zadaná žádná data")
                st.stop()
            df = st.session_state['manual_data']
        elif uploaded_file is not None:
            df = lds_margin.load_data(file_path=uploaded_file)
        elif db_url and query:
            df = lds_margin.load_data(db_url=db_url, query=query)
        else:
            st.error("Není k dispozici žádný zdroj dat")
            st.stop()
        df = lds_margin.validate_data(df)
        df = df[df[lds_margin.REQUIRED_COLUMNS['Year']] == year]
        if lds_type != "všechny":
            df = df[df[lds_margin.REQUIRED_COLUMNS['Type']] == lds_type]
        df = lds_margin.compute_margin(df)

        st.subheader("Výsledná tabulka")
        st.dataframe(df)

        avg = lds_margin.average_margin_by_type(df)
        st.subheader("Průměrná marže podle typu")
        st.dataframe(avg)

        fig = px.bar(df, x=lds_margin.REQUIRED_COLUMNS['LDS'], y='Margin', title='Marže podle LDS')
        st.plotly_chart(fig, use_container_width=True)

        # Export
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("Stáhnout výsledky (XLSX)", output.getvalue(), file_name="vysledky.xlsx")
        st.download_button("Stáhnout výsledky (CSV)", df.to_csv(index=False).encode('utf-8'), file_name="vysledky.csv")

        # Predikce (jednoduchá lineární regrese)
        model = lds_margin.train_margin_prediction(df)
        st.subheader("Predikce marže")
        with st.form("predict"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                p_cons = st.number_input("Spotřeba [MWh]", value=0.0)
            with c2:
                p_purch = st.number_input("Náklady na nákup energie", value=0.0)
            with c3:
                p_fixed = st.number_input("Fixní provozní náklady", value=0.0)
            with c4:
                p_var = st.number_input("Variabilní provozní náklady", value=0.0)
            submit = st.form_submit_button("Predikovat")
        if submit:
            pred = lds_margin.predict_margin(model, p_cons, p_purch, p_fixed, p_var)
            st.info(f"Odhadovaná marže: {pred:.2f} %")
    except Exception as e:
        st.error(f"Chyba při zpracování dat: {e}")
        logging.exception("Processing failed")

