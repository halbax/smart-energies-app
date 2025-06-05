import pandas as pd
import logging
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('app.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

REQUIRED_COLUMNS = {
    'LDS': 'Název lokální distribuční sítě',
    'Consumption': 'Celková spotřeba (MWh)',
    'PurchaseCost': 'Celkové náklady na nákup energie (EUR/CZK)',
    'Revenue': 'Výnosy z prodeje energie (EUR/CZK)',
    'OpCostFixed': 'Náklady na provoz LDS (fixní – EUR/CZK)',
    'OpCostVariable': 'Náklady na provoz LDS (variabilní – EUR/CZK)',
    'Type': 'Typ LDS',
    'Year': 'Rok'
}


def load_data(file_path=None, db_url=None, query=None):
    """Load data from Excel, CSV or database."""
    try:
        if file_path:
            logger.info("Loading data from file %s", file_path)
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                raise ValueError('Unsupported file format')
        elif db_url and query:
            logger.info("Loading data from database")
            engine = create_engine(db_url)
            df = pd.read_sql(query, engine)
        else:
            raise ValueError('No data source provided')
    except Exception as e:
        logger.error("Failed loading data: %s", e)
        raise
    return df


def validate_data(df):
    missing = [col for col in REQUIRED_COLUMNS.values() if col not in df.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    # Clean numeric columns
    num_cols = [REQUIRED_COLUMNS[k] for k in ['Consumption', 'PurchaseCost', 'Revenue', 'OpCostFixed', 'OpCostVariable']]
    for col in num_cols:
        df[col] = (df[col]
                   .astype(str)
                   .str.replace(',', '.')
                   .str.replace(' ', '')
                   .astype(float))
    return df


def compute_margin(df):
    df = df.copy()
    df['OperatingCost'] = df[REQUIRED_COLUMNS['OpCostFixed']] + df[REQUIRED_COLUMNS['OpCostVariable']]
    df['Margin'] = (df[REQUIRED_COLUMNS['Revenue']] - (df[REQUIRED_COLUMNS['PurchaseCost']] + df['OperatingCost'])) / df[REQUIRED_COLUMNS['Revenue']] * 100
    return df


def average_margin_by_type(df):
    return df.groupby(REQUIRED_COLUMNS['Type'])['Margin'].mean().reset_index(name='AverageMargin')


def train_margin_prediction(df):
    features = df[[REQUIRED_COLUMNS['Consumption'], REQUIRED_COLUMNS['PurchaseCost'], REQUIRED_COLUMNS['OpCostFixed'], REQUIRED_COLUMNS['OpCostVariable']]]
    target = df['Margin']
    model = LinearRegression()
    model.fit(features, target)
    return model


def predict_margin(model, consumption, purchase_cost, op_fixed, op_variable):
    X = np.array([[consumption, purchase_cost, op_fixed, op_variable]])
    return model.predict(X)[0]

