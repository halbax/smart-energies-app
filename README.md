# Smart Energies App

This Streamlit application calculates LDS margins and provides basic analysis.

## Installation

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Launching the App

Run the application with Streamlit:

```bash
streamlit run app.py
```

In the sidebar you can upload an Excel/CSV file with consumption data.  Optionally fill in the *DB URL* and *SQL query* fields if you want to load data from a database instead of uploading a file.

A small sample dataset is available in `src/kfc_spotreba_import.xlsx` which you can use for testing.
