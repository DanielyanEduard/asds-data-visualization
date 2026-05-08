import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output

from data import (df, ALL_YEARS, ALL_REGIONS, ALL_CATEGORIES,
                  COLOR_SALES, COLOR_PROFIT, COLOR_DISCOUNT, TEMPLATE)


def categories_layout():
    return dbc.Container([
        html.H4('Category & Regional Analysis', className='mb-3'),

        dbc.Row([
            dbc.Col([
                dbc.Label('Region'),
                dcc.Dropdown(
                    id='cat-region-dropdown',
                    options=[{'label': 'All Regions', 'value': 'All'}]
                            + [{'label': r, 'value': r} for r in ALL_REGIONS],
                    value='All',
                    clearable=False,
                ),
            ], md=3),
            dbc.Col([
                dbc.Label('Category'),
                dcc.Dropdown(
                    id='cat-category-dropdown',
                    options=[{'label': 'All Categories', 'value': 'All'}]
                            + [{'label': c, 'value': c} for c in ALL_CATEGORIES],
                    value='All',
                    clearable=False,
                ),
            ], md=3),
            dbc.Col([
                dbc.Label('Year Range'),
                dcc.RangeSlider(
                    id='cat-year-slider',
                    min=ALL_YEARS[0], max=ALL_YEARS[-1], step=1,
                    value=[ALL_YEARS[0], ALL_YEARS[-1]],
                    marks={y: str(y) for y in ALL_YEARS},
                ),
            ], md=6),
        ], className='mb-4'),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Revenue vs Profit by Category', className='card-title'),
                dcc.Graph(id='cat-revenue-profit'),
            ]), className='shadow-sm'), md=6),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Profit Margin by Category', className='card-title'),
                dcc.Graph(id='cat-margin'),
            ]), className='shadow-sm'), md=6),
        ], className='mb-4'),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Category & Sub-Category Treemap', className='card-title'),
                html.P('Size = Sales, Color = Profit Margin %', className='text-muted small'),
                dcc.Graph(id='cat-treemap'),
            ]), className='shadow-sm'), md=12),
        ], className='mb-4'),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Sales Composition by Region & Category', className='card-title'),
                dcc.Graph(id='cat-region-stack'),
            ]), className='shadow-sm'), md=6),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5('Regional Performance', className='card-title'),
                dcc.Graph(id='cat-region-metrics'),
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
    Output('cat-revenue-profit', 'figure'),
    Output('cat-margin', 'figure'),
    Output('cat-treemap', 'figure'),
    Output('cat-region-stack', 'figure'),
    Output('cat-region-metrics', 'figure'),
    Input('cat-region-dropdown', 'value'),
    Input('cat-category-dropdown', 'value'),
    Input('cat-year-slider', 'value'),
)
def update_categories(region, category, year_range):
    dff = _filter(region, 'All', year_range)

    cat = dff.groupby('Category').agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum')
    ).reset_index()
    cat['Profit_Margin'] = (cat['Profit'] / cat['Sales'] * 100).round(2)
    cat = cat.sort_values('Sales', ascending=True)

    # revenue vs profit
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(y=cat['Category'], x=cat['Sales'], name='Sales',
                             orientation='h', marker_color=COLOR_SALES))
    fig_rev.add_trace(go.Bar(y=cat['Category'], x=cat['Profit'], name='Profit',
                             orientation='h', marker_color=COLOR_PROFIT))
    fig_rev.update_layout(template=TEMPLATE, height=350, margin=dict(t=10, b=40),
                          barmode='group',
                          legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

    # margin
    fig_margin = go.Figure(go.Bar(
        y=cat['Category'], x=cat['Profit_Margin'], orientation='h', marker_color=COLOR_PROFIT,
    ))
    fig_margin.update_layout(template=TEMPLATE, height=350, margin=dict(t=10, b=40),
                             xaxis_title='Profit Margin (%)')

    # treemap
    dff_cat = _filter(region, category, year_range)
    sub_cat = dff_cat.groupby(['Category', 'Sub Category']).agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum')
    ).reset_index()
    sub_cat['Profit_Margin'] = (sub_cat['Profit'] / sub_cat['Sales'] * 100).round(2)

    fig_tree = px.treemap(sub_cat, path=['Category', 'Sub Category'], values='Sales',
                          color='Profit_Margin', color_continuous_scale='RdYlGn',
                          color_continuous_midpoint=sub_cat['Profit_Margin'].median())
    fig_tree.update_layout(template=TEMPLATE, height=420, margin=dict(t=10, b=10))

    # region × category stack
    dff_all = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    region_cat = dff_all.groupby(['Region', 'Category']).agg(Sales=('Sales', 'sum')).reset_index()
    fig_stack = px.bar(region_cat, x='Region', y='Sales', color='Category',
                       color_discrete_sequence=px.colors.qualitative.Set2)
    fig_stack.update_layout(template=TEMPLATE, height=350, margin=dict(t=10, b=40),
                            barmode='stack',
                            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

    # regional metrics — two separate bars side by side
    reg = dff_all.groupby('Region').agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum'), Orders=('Order ID', 'count')
    ).reset_index()
    reg['Profit_Margin'] = (reg['Profit'] / reg['Sales'] * 100).round(2)

    fig_reg = go.Figure()
    fig_reg.add_trace(go.Bar(x=reg['Region'], y=reg['Sales'], name='Sales', marker_color=COLOR_SALES))
    fig_reg.add_trace(go.Bar(x=reg['Region'], y=reg['Profit'], name='Profit', marker_color=COLOR_PROFIT))
    fig_reg.update_layout(template=TEMPLATE, height=350, margin=dict(t=10, b=40),
                          barmode='group', yaxis_title='Amount',
                          legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

    return fig_rev, fig_margin, fig_tree, fig_stack, fig_reg
