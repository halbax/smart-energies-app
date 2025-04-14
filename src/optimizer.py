# src/optimizer.py

import pandas as pd

def optimize(df):
    result = {}
    df = df.copy()
    df['residual'] = df['MWh']

    # CAL
    cal_value = df['MWh'].min()
    cal_total = cal_value * len(df)
    if cal_total >= 1000:
        df['residual'] -= cal_value
        result['CAL'] = cal_total
    else:
        result['CAL'] = 0

    # Q
    result['Q'] = {}
    for q in range(1, 5):
        q_mask = df.index.quarter == q
        if q_mask.sum() == 0:
            result['Q'][f'Q{q}'] = 0
            continue
        q_min = df.loc[q_mask, 'residual'].min()
        q_total = q_min * q_mask.sum()
        if q_total >= 1000:
            df.loc[q_mask, 'residual'] -= q_min
            result['Q'][f'Q{q}'] = q_total
        else:
            result['Q'][f'Q{q}'] = 0

    # M
    result['M'] = {}
    for m in range(1, 13):
        m_mask = df.index.month == m
        if m_mask.sum() == 0:
            result['M'][f'M{m:02d}'] = 0
            continue
        m_min = df.loc[m_mask, 'residual'].min()
        m_total = m_min * m_mask.sum()
        if m_total >= 720:
            df.loc[m_mask, 'residual'] -= m_min
            result['M'][f'M{m:02d}'] = m_total
        else:
            result['M'][f'M{m:02d}'] = 0

    # SPOT
    result['SPOT'] = df['residual'].sum()

    # Výstupní shrnutí
    summary = []
    summary.append(['CAL', result['CAL']])
    summary += [[k, v] for k, v in result['Q'].items()]
    summary += [[k, v] for k, v in result['M'].items()]
    summary.append(['SPOT', result['SPOT']])
    result['summary'] = pd.DataFrame(summary, columns=["Produkt", "Objem [MWh]"])

    return result
