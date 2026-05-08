import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Supermart Grocery Sales - Retail Analytics Dataset.csv')

COLOR_SALES = '#2196F3'
COLOR_PROFIT = '#4CAF50'
COLOR_DISCOUNT = '#FF9800'
COLOR_NEGATIVE = '#F44336'
TEMPLATE = 'plotly_white'


def load_data():
    df = pd.read_csv(DATA_PATH)
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='mixed', dayfirst=False)
    df['Year'] = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.month
    df['Month_Name'] = df['Order Date'].dt.month_name()
    df['Year_Month'] = df['Order Date'].dt.to_period('M').dt.to_timestamp()
    df['Profit_Margin'] = (df['Profit'] / df['Sales'] * 100).round(2)
    df['Discount_Bin'] = pd.cut(
        df['Discount'], bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5],
        labels=['0-10%', '10-20%', '20-30%', '30-40%', '40-50%']
    )
    return df


df = load_data()

ALL_YEARS = sorted(int(y) for y in df['Year'].unique())
ALL_CATEGORIES = sorted(df['Category'].unique().tolist())
ALL_REGIONS = sorted(df['Region'].unique().tolist())
