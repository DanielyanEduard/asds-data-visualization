import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, callback, Input, Output

from data import df
from pages.overview import overview_layout
from pages.categories import categories_layout
from pages.performance import performance_layout

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
)

PAGES = {
    '/': ('Overview', overview_layout),
    '/categories': ('Categories & Regions', categories_layout),
    '/performance': ('Discounts & Performance', performance_layout),
}

navbar = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand('Supermart Grocery Sales', className='fs-4 fw-bold'),
        dbc.Nav([
            dbc.NavItem(dbc.NavLink(name, href=path, id=f'nav-{path}'))
            for path, (name, _) in PAGES.items()
        ], navbar=True),
    ], fluid=True),
    color='primary',
    dark=True,
    className='mb-4',
)

app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content'),
], fluid=True, className='px-4 pb-4')


@callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname in PAGES:
        return PAGES[pathname][1]()
    return PAGES['/'][1]()


if __name__ == '__main__':
    app.run(debug=True)
