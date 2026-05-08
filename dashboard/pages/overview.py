import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output
from plotly.subplots import make_subplots

from data import df, ALL_YEARS, COLOR_SALES, COLOR_PROFIT, COLOR_NEGATIVE, TEMPLATE


def kpi_card(title, value, color='primary'):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className='text-muted mb-1'),
            html.H3(value, className=f'text-{color} fw-bold mb-0'),
        ]),
        className='shadow-sm h-100',
    )


def overview_layout():
    return dbc.Container([
        html.H4('Business Overview', className='mb-3'),

        dbc.Row([
            dbc.Col([
                dbc.Label('Select Year Range'),
                dcc.RangeSlider(
                    id='overview-year-slider',
                    min=ALL_YEARS[0], max=ALL_YEARS[-1], step=1,
                    value=[ALL_YEARS[0], ALL_YEARS[-1]],
                    marks={y: str(y) for y in ALL_YEARS},
                ),
            ], md=6),
        ], className='mb-4'),

        dbc.Row(id='overview-kpis', className='g-3 mb-4'),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Monthly Sales & Profit Trend', className='card-title'),
                dcc.Graph(id='overview-monthly-trend'),
            ]), className='shadow-sm'), md=12),
        ], className='mb-4'),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Yearly Sales & Profit', className='card-title'),
                dcc.Graph(id='overview-yearly-bars'),
            ]), className='shadow-sm'), md=6),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Yearly Profit Margin', className='card-title'),
                dcc.Graph(id='overview-yearly-margin'),
            ]), className='shadow-sm'), md=6),
        ]),
    ], fluid=True)


@callback(
    Output('overview-kpis', 'children'),
    Output('overview-monthly-trend', 'figure'),
    Output('overview-yearly-bars', 'figure'),
    Output('overview-yearly-margin', 'figure'),
    Input('overview-year-slider', 'value'),
)
def update_overview(year_range):
    dff = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

    total_sales = dff['Sales'].sum()
    total_profit = dff['Profit'].sum()
    margin = (total_profit / total_sales * 100) if total_sales else 0
    total_orders = len(dff)

    kpis = [
        dbc.Col(kpi_card('Total Sales', f'₹{total_sales:,.0f}'), md=3),
        dbc.Col(kpi_card('Total Profit', f'₹{total_profit:,.0f}', color='success'), md=3),
        dbc.Col(kpi_card('Profit Margin', f'{margin:.1f}%', color='warning'), md=3),
        dbc.Col(kpi_card('Total Orders', f'{total_orders:,}', color='info'), md=3),
    ]

    # monthly trend
    monthly = dff.groupby('Year_Month').agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum')
    ).reset_index()

    fig_monthly = make_subplots(specs=[[{'secondary_y': True}]])
    fig_monthly.add_trace(
        go.Scatter(x=monthly['Year_Month'], y=monthly['Sales'], name='Sales',
                   line=dict(color=COLOR_SALES, width=2),
                   fill='tozeroy', fillcolor='rgba(33,150,243,0.1)'),
        secondary_y=False,
    )
    fig_monthly.add_trace(
        go.Scatter(x=monthly['Year_Month'], y=monthly['Profit'], name='Profit',
                   line=dict(color=COLOR_PROFIT, width=2)),
        secondary_y=True,
    )
    fig_monthly.update_layout(
        template=TEMPLATE, height=370, margin=dict(t=10, b=40),
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    )
    fig_monthly.update_yaxes(title_text='Sales', secondary_y=False)
    fig_monthly.update_yaxes(title_text='Profit', secondary_y=True)

    # yearly bars
    yearly = dff.groupby('Year').agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum')
    ).reset_index()
    yearly['Profit_Margin'] = (yearly['Profit'] / yearly['Sales'] * 100).round(2)

    fig_bars = go.Figure()
    fig_bars.add_trace(go.Bar(x=yearly['Year'], y=yearly['Sales'], name='Sales', marker_color=COLOR_SALES))
    fig_bars.add_trace(go.Bar(x=yearly['Year'], y=yearly['Profit'], name='Profit', marker_color=COLOR_PROFIT))
    fig_bars.update_layout(
        template=TEMPLATE, height=350, margin=dict(t=10, b=40), barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    )

    # yearly margin
    fig_margin = go.Figure()
    fig_margin.add_trace(go.Scatter(
        x=yearly['Year'], y=yearly['Profit_Margin'], name='Margin %',
        mode='lines+markers', marker=dict(size=10),
        line=dict(color=COLOR_NEGATIVE, width=2.5),
    ))
    fig_margin.update_layout(
        template=TEMPLATE, height=350, margin=dict(t=10, b=40),
        yaxis_title='Profit Margin (%)',
    )

    return kpis, fig_monthly, fig_bars, fig_margin
