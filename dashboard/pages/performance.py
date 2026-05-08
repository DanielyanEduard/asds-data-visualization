import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output

from data import (df, ALL_YEARS, ALL_REGIONS, ALL_CATEGORIES,
                  COLOR_SALES, COLOR_PROFIT, COLOR_DISCOUNT, COLOR_NEGATIVE, TEMPLATE)


def performance_layout():
    return dbc.Container([
        html.H4('Discount Strategy & Top Performers', className='mb-3'),

        dbc.Row([
            dbc.Col([
                dbc.Label('Region'),
                dcc.Dropdown(
                    id='perf-region-dropdown',
                    options=[{'label': 'All Regions', 'value': 'All'}]
                            + [{'label': r, 'value': r} for r in ALL_REGIONS],
                    value='All',
                    clearable=False,
                ),
            ], md=3),
            dbc.Col([
                dbc.Label('Category'),
                dcc.Dropdown(
                    id='perf-category-dropdown',
                    options=[{'label': 'All Categories', 'value': 'All'}]
                            + [{'label': c, 'value': c} for c in ALL_CATEGORIES],
                    value='All',
                    clearable=False,
                ),
            ], md=3),
            dbc.Col([
                dbc.Label('Number of Top Results'),
                dcc.Input(id='perf-top-n', type='number', value=10, min=5, max=30, step=1,
                          className='form-control'),
            ], md=2),
            dbc.Col([
                dbc.Label('Year Range'),
                dcc.RangeSlider(
                    id='perf-year-slider',
                    min=ALL_YEARS[0], max=ALL_YEARS[-1], step=1,
                    value=[ALL_YEARS[0], ALL_YEARS[-1]],
                    marks={y: str(y) for y in ALL_YEARS},
                ),
            ], md=4),
        ], className='mb-4'),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Avg Profit by Discount Level', className='card-title'),
                dcc.Graph(id='perf-discount-profit'),
            ]), className='shadow-sm'), md=6),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Avg Margin by Discount Level', className='card-title'),
                dcc.Graph(id='perf-discount-margin'),
            ]), className='shadow-sm'), md=6),
        ], className='mb-4'),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Discount Impact on Margin by Region', className='card-title'),
                dcc.Graph(id='perf-discount-region'),
            ]), className='shadow-sm'), md=12),
        ], className='mb-4'),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Top Customers by Sales', className='card-title'),
                dcc.Graph(id='perf-top-customers'),
            ]), className='shadow-sm'), md=6),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Top Cities: Sales vs Profit Margin', className='card-title'),
                dcc.Graph(id='perf-top-cities'),
            ]), className='shadow-sm'), md=6),
        ]),
    ], fluid=True)


def _filter(region, category, year_range):
    dff = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    if region != 'All':
        dff = dff[dff['Region'] == region]
    if category != 'All':
        dff = dff[dff['Category'] == category]
    return dff


@callback(
    Output('perf-discount-profit', 'figure'),
    Output('perf-discount-margin', 'figure'),
    Output('perf-discount-region', 'figure'),
    Output('perf-top-customers', 'figure'),
    Output('perf-top-cities', 'figure'),
    Input('perf-region-dropdown', 'value'),
    Input('perf-category-dropdown', 'value'),
    Input('perf-top-n', 'value'),
    Input('perf-year-slider', 'value'),
)
def update_performance(region, category, top_n, year_range):
    top_n = top_n or 10
    dff = _filter(region, category, year_range)

    # discount bins
    disc = dff.groupby('Discount_Bin', observed=True).agg(
        Avg_Profit=('Profit', 'mean'),
        Avg_Margin=('Profit_Margin', 'mean'),
    ).reset_index()

    # avg profit by discount
    profit_colors = [COLOR_PROFIT if v > 0 else COLOR_NEGATIVE for v in disc['Avg_Profit']]
    fig_profit = go.Figure(go.Bar(
        x=disc['Discount_Bin'].astype(str), y=disc['Avg_Profit'],
        marker_color=profit_colors,
    ))
    fig_profit.update_layout(template=TEMPLATE, height=370, margin=dict(t=10, b=40),
                             xaxis_title='Discount Level', yaxis_title='Avg Profit')

    # avg margin by discount
    fig_margin = go.Figure(go.Bar(
        x=disc['Discount_Bin'].astype(str), y=disc['Avg_Margin'],
        marker_color=COLOR_PROFIT,
    ))
    fig_margin.update_layout(template=TEMPLATE, height=370, margin=dict(t=10, b=40),
                             xaxis_title='Discount Level', yaxis_title='Avg Margin (%)')

    # discount × region
    dff_all_cat = _filter(region, 'All', year_range)
    disc_region = dff_all_cat.groupby(['Region', 'Discount_Bin'], observed=True).agg(
        Avg_Margin=('Profit_Margin', 'mean')
    ).reset_index()
    fig_disc_reg = px.bar(disc_region, x='Discount_Bin', y='Avg_Margin', color='Region',
                          barmode='group', color_discrete_sequence=px.colors.qualitative.Set2)
    fig_disc_reg.add_hline(y=0, line_dash='dash', line_color='red')
    fig_disc_reg.update_layout(template=TEMPLATE, height=370, margin=dict(t=10, b=40),
                               xaxis_title='Discount Level', yaxis_title='Avg Profit Margin (%)')

    # top customers
    top_cust = dff.groupby('Customer Name').agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum')
    ).nlargest(top_n, 'Sales').reset_index()

    fig_cust = go.Figure()
    fig_cust.add_trace(go.Bar(y=top_cust['Customer Name'], x=top_cust['Sales'],
                              name='Sales', orientation='h', marker_color=COLOR_SALES))
    fig_cust.add_trace(go.Bar(y=top_cust['Customer Name'], x=top_cust['Profit'],
                              name='Profit', orientation='h', marker_color=COLOR_PROFIT))
    fig_cust.update_layout(template=TEMPLATE, height=370, margin=dict(t=10, b=40),
                           barmode='group', yaxis=dict(autorange='reversed'),
                           legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

    # top cities bubble
    top_city = dff.groupby('City').agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum'), Orders=('Order ID', 'count')
    ).reset_index()
    top_city['Profit_Margin'] = (top_city['Profit'] / top_city['Sales'] * 100).round(2)
    top_city = top_city.nlargest(top_n, 'Sales')

    fig_city = px.scatter(top_city, x='Sales', y='Profit_Margin', size='Orders',
                          text='City', color='Profit_Margin',
                          color_continuous_scale='RdYlGn')
    fig_city.update_traces(textposition='top center')
    fig_city.update_layout(template=TEMPLATE, height=370, margin=dict(t=10, b=40),
                           xaxis_title='Total Sales', yaxis_title='Profit Margin (%)')

    return fig_profit, fig_margin, fig_disc_reg, fig_cust, fig_city
