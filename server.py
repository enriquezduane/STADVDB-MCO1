import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

engine = create_engine(
    URL.create(
        "mysql+mysqlconnector",
        username="root",
        password="rootpassword",
        host="localhost",
        port=3306,
        database="steam_games_data_warehouse",
        query={"connect_timeout": "10"}
    )
)

roll_up_query = """
SELECT 
    dt.year,
    AVG(dg.metacritic_score) AS avg_metacritic_score,
    SUM(fgs.recommendations) AS total_recommendations
FROM 
    fact_game_sales fgs
JOIN dim_game dg ON fgs.game_key = dg.game_key
JOIN dim_time dt ON fgs.time_key = dt.time_key
GROUP BY 
    dt.year
ORDER BY 
    dt.year;
"""

drill_down_query = """
SELECT 
    dt.year,
    dt.month,
    COUNT(DISTINCT fgs.game_key) AS games_released,
    AVG(dg.price) AS avg_price
FROM 
    fact_game_sales fgs
JOIN dim_game dg ON fgs.game_key = dg.game_key
JOIN dim_time dt ON fgs.time_key = dt.time_key
WHERE 
    dt.year = 2022
GROUP BY 
    dt.year, dt.month
ORDER BY 
    dt.month;
"""

slice_dice_query = """
SELECT 
    CASE 
        WHEN dg.price < 10 THEN 'Under $10'
        WHEN dg.price >= 10 AND dg.price < 30 THEN '$10 - $29.99'
        ELSE '$30 and above'
    END AS price_range,
    CASE 
        WHEN dg.metacritic_score < 50 THEN 'Low'
        WHEN dg.metacritic_score >= 50 AND dg.metacritic_score < 75 THEN 'Medium'
        ELSE 'High'
    END AS metacritic_range,
    COUNT(*) AS game_count
FROM 
    fact_game_sales fgs
JOIN dim_game dg ON fgs.game_key = dg.game_key
JOIN dim_platform dp ON fgs.platform_key = dp.platform_key
WHERE 
    dp.windows = TRUE
GROUP BY 
    price_range, metacritic_range
ORDER BY 
    price_range, metacritic_range;
"""

pivot_query = """
SELECT 
    dt.year,
    SUM(CASE WHEN dp.windows = TRUE AND dp.mac = FALSE AND dp.linux = FALSE THEN 1 ELSE 0 END) AS windows_only,
    SUM(CASE WHEN dp.windows = FALSE AND dp.mac = TRUE AND dp.linux = FALSE THEN 1 ELSE 0 END) AS mac_only,
    SUM(CASE WHEN dp.windows = FALSE AND dp.mac = FALSE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS linux_only,
    SUM(CASE WHEN dp.windows = TRUE AND dp.mac = TRUE AND dp.linux = FALSE THEN 1 ELSE 0 END) AS windows_mac,
    SUM(CASE WHEN dp.windows = TRUE AND dp.mac = FALSE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS windows_linux,
    SUM(CASE WHEN dp.windows = FALSE AND dp.mac = TRUE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS mac_linux,
    SUM(CASE WHEN dp.windows = TRUE AND dp.mac = TRUE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS all_platforms
FROM 
    fact_game_sales fgs
JOIN dim_time dt ON fgs.time_key = dt.time_key
JOIN dim_platform dp ON fgs.platform_key = dp.platform_key
GROUP BY 
    dt.year
ORDER BY 
    dt.year;
"""

df_roll_up = pd.read_sql(roll_up_query, engine)
df_drill_down = pd.read_sql(drill_down_query, engine)
df_slice_dice = pd.read_sql(slice_dice_query, engine)
df_pivot = pd.read_sql(pivot_query, engine)

external_stylesheets = ['https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1("Steam Games OLAP Dashboard", className="text-center my-4"),
    dcc.Tabs([
        dcc.Tab(label='Roll Up', children=[
            html.Div([
                html.Div([
                    html.Label("Start Year:", className="form-label"),
                    dcc.Input(id='roll-up-start-year', type='number', value=2010, className="form-control"),
                ], className="col-md-3"),
                html.Div([
                    html.Label("End Year:", className="form-label"),
                    dcc.Input(id='roll-up-end-year', type='number', value=2022, className="form-control"),
                ], className="col-md-3"),
                html.Div([
                    html.Button('Update', id='roll-up-update-button', n_clicks=0, className="btn btn-primary mt-4"),
                ], className="col-md-2"),
            ], className="row g-3 mb-3"),
            dcc.Graph(id='roll-up-graph')
        ]),
        dcc.Tab(label='Drill Down', children=[
            html.Div([
                html.Div([
                    html.Label("Year:", className="form-label"),
                    dcc.Input(id='drill-down-year', type='number', value=2022, className="form-control"),
                ], className="col-md-3"),
                html.Div([
                    html.Button('Update', id='drill-down-update-button', n_clicks=0, className="btn btn-primary mt-4"),
                ], className="col-md-2"),
            ], className="row g-3 mb-3"),
            dcc.Graph(id='drill-down-graph')
        ]),
        dcc.Tab(label='Slice and Dice', children=[
            html.Div([
                html.Div([
                    html.Label("Platform:", className="form-label"),
                    dcc.Dropdown(
                        id='slice-dice-platform',
                        options=[
                            {'label': 'Windows', 'value': 'windows'},
                            {'label': 'Mac', 'value': 'mac'},
                            {'label': 'Linux', 'value': 'linux'}
                        ],
                        value='windows',
                        className="form-select"
                    ),
                ], className="col-md-3"),
                html.Div([
                    html.Button('Update', id='slice-dice-update-button', n_clicks=0, className="btn btn-primary mt-4"),
                ], className="col-md-2"),
            ], className="row g-3 mb-3"),
            dcc.Graph(id='slice-dice-graph')
        ]),
        dcc.Tab(label='Pivot', children=[
            html.Div([
                html.Div([
                    html.Label("Start Year:", className="form-label"),
                    dcc.Input(id='pivot-start-year', type='number', value=2010, className="form-control"),
                ], className="col-md-3"),
                html.Div([
                    html.Label("End Year:", className="form-label"),
                    dcc.Input(id='pivot-end-year', type='number', value=2022, className="form-control"),
                ], className="col-md-3"),
                html.Div([
                    html.Button('Update', id='pivot-update-button', n_clicks=0, className="btn btn-primary mt-4"),
                ], className="col-md-2"),
            ], className="row g-3 mb-3"),
            dcc.Graph(id='pivot-graph')
        ])
    ], className="nav nav-tabs")
], className="container")

@app.callback(
    Output('roll-up-graph', 'figure'),
    Input('roll-up-update-button', 'n_clicks'),
    State('roll-up-start-year', 'value'),
    State('roll-up-end-year', 'value')
)
def update_roll_up_graph(n_clicks, start_year, end_year):
    roll_up_query = f"""
    SELECT 
        dt.year,
        AVG(dg.metacritic_score) AS avg_metacritic_score,
        SUM(fgs.recommendations) AS total_recommendations
    FROM 
        fact_game_sales fgs
    JOIN dim_game dg ON fgs.game_key = dg.game_key
    JOIN dim_time dt ON fgs.time_key = dt.time_key
    WHERE
        dt.year BETWEEN {start_year} AND {end_year}
    GROUP BY 
        dt.year
    ORDER BY 
        dt.year;
    """
    df_roll_up = pd.read_sql(roll_up_query, engine)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_roll_up['year'], y=df_roll_up['avg_metacritic_score'], name='Avg Metacritic Score'))
    fig.add_trace(go.Bar(x=df_roll_up['year'], y=df_roll_up['total_recommendations'], name='Total Recommendations'))
    fig.update_layout(title='Yearly Average Metacritic Score and Total Recommendations', xaxis_title='Year')
    return fig

@app.callback(
    Output('drill-down-graph', 'figure'),
    Input('drill-down-update-button', 'n_clicks'),
    State('drill-down-year', 'value')
)
def update_drill_down_graph(n_clicks, year):
    drill_down_query = f"""
    SELECT 
        dt.year,
        dt.month,
        COUNT(DISTINCT fgs.game_key) AS games_released,
        AVG(dg.price) AS avg_price
    FROM 
        fact_game_sales fgs
    JOIN dim_game dg ON fgs.game_key = dg.game_key
    JOIN dim_time dt ON fgs.time_key = dt.time_key
    WHERE 
        dt.year = {year}
    GROUP BY 
        dt.year, dt.month
    ORDER BY 
        dt.month;
    """
    df_drill_down = pd.read_sql(drill_down_query, engine)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_drill_down['month'], y=df_drill_down['games_released'], name='Games Released'))
    fig.add_trace(go.Scatter(x=df_drill_down['month'], y=df_drill_down['avg_price'], name='Avg Price', yaxis='y2'))
    fig.update_layout(title=f'Monthly Games Released and Average Price ({year})',
                      xaxis_title='Month', yaxis_title='Games Released', yaxis2=dict(title='Avg Price', overlaying='y', side='right'))
    return fig

@app.callback(
    Output('slice-dice-graph', 'figure'),
    Input('slice-dice-update-button', 'n_clicks'),
    State('slice-dice-platform', 'value')
)
def update_slice_dice_graph(n_clicks, platform):
    slice_dice_query = f"""
    SELECT 
        CASE 
            WHEN dg.price < 10 THEN 'Under $10'
            WHEN dg.price >= 10 AND dg.price < 30 THEN '$10 - $29.99'
            ELSE '$30 and above'
        END AS price_range,
        CASE 
            WHEN dg.metacritic_score < 50 THEN 'Low'
            WHEN dg.metacritic_score >= 50 AND dg.metacritic_score < 75 THEN 'Medium'
            ELSE 'High'
        END AS metacritic_range,
        COUNT(*) AS game_count
    FROM 
        fact_game_sales fgs
    JOIN dim_game dg ON fgs.game_key = dg.game_key
    JOIN dim_platform dp ON fgs.platform_key = dp.platform_key
    WHERE 
        dp.{platform} = TRUE
    GROUP BY 
        price_range, metacritic_range
    ORDER BY 
        price_range, metacritic_range;
    """
    df_slice_dice = pd.read_sql(slice_dice_query, engine)
    
    fig = px.treemap(df_slice_dice, path=['price_range', 'metacritic_range'], values='game_count')
    fig.update_layout(title=f'Game Count by Price Range and Metacritic Score ({platform.capitalize()} Games)')
    return fig

@app.callback(
    Output('pivot-graph', 'figure'),
    Input('pivot-update-button', 'n_clicks'),
    State('pivot-start-year', 'value'),
    State('pivot-end-year', 'value')
)
def update_pivot_graph(n_clicks, start_year, end_year):
    pivot_query = f"""
    SELECT 
        dt.year,
        SUM(CASE WHEN dp.windows = TRUE AND dp.mac = FALSE AND dp.linux = FALSE THEN 1 ELSE 0 END) AS windows_only,
        SUM(CASE WHEN dp.windows = FALSE AND dp.mac = TRUE AND dp.linux = FALSE THEN 1 ELSE 0 END) AS mac_only,
        SUM(CASE WHEN dp.windows = FALSE AND dp.mac = FALSE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS linux_only,
        SUM(CASE WHEN dp.windows = TRUE AND dp.mac = TRUE AND dp.linux = FALSE THEN 1 ELSE 0 END) AS windows_mac,
        SUM(CASE WHEN dp.windows = TRUE AND dp.mac = FALSE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS windows_linux,
        SUM(CASE WHEN dp.windows = FALSE AND dp.mac = TRUE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS mac_linux,
        SUM(CASE WHEN dp.windows = TRUE AND dp.mac = TRUE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS all_platforms
    FROM 
        fact_game_sales fgs
    JOIN dim_time dt ON fgs.time_key = dt.time_key
    JOIN dim_platform dp ON fgs.platform_key = dp.platform_key
    WHERE
        dt.year BETWEEN {start_year} AND {end_year}
    GROUP BY 
        dt.year
    ORDER BY 
        dt.year;
    """
    df_pivot = pd.read_sql(pivot_query, engine)
    
    fig = go.Figure()
    for column in df_pivot.columns[1:]:  # Skip the 'year' column
        fig.add_trace(go.Bar(x=df_pivot['year'], y=df_pivot[column], name=column))
    fig.update_layout(title='Games Released by Platform Combination', xaxis_title='Year', yaxis_title='Number of Games', barmode='stack')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
