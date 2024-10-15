import dash
from dash import dcc, html
from dash.dependencies import Input, Output
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

app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div([
    html.H1("Game Sales Dashboard"),
    
    dcc.Tabs([
        dcc.Tab(label='Roll Up', children=[
            dcc.Graph(id='roll-up-graph')
        ]),
        dcc.Tab(label='Drill Down', children=[
            dcc.Graph(id='drill-down-graph')
        ]),
        dcc.Tab(label='Slice and Dice', children=[
            dcc.Graph(id='slice-dice-graph')
        ]),
        dcc.Tab(label='Pivot', children=[
            dcc.Graph(id='pivot-graph')
        ])
    ])
])

# Callbacks for each graph
@app.callback(Output('roll-up-graph', 'figure'),
              Input('roll-up-graph', 'id'))
def update_roll_up_graph(id):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_roll_up['year'], y=df_roll_up['avg_metacritic_score'], name='Avg Metacritic Score'))
    fig.add_trace(go.Bar(x=df_roll_up['year'], y=df_roll_up['total_recommendations'], name='Total Recommendations'))
    fig.update_layout(title='Yearly Average Metacritic Score and Total Recommendations', xaxis_title='Year')
    return fig

@app.callback(Output('drill-down-graph', 'figure'),
              Input('drill-down-graph', 'id'))
def update_drill_down_graph(id):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_drill_down['month'], y=df_drill_down['games_released'], name='Games Released'))
    fig.add_trace(go.Scatter(x=df_drill_down['month'], y=df_drill_down['avg_price'], name='Avg Price', yaxis='y2'))
    fig.update_layout(title='Monthly Games Released and Average Price (2022)',
                      xaxis_title='Month', yaxis_title='Games Released', yaxis2=dict(title='Avg Price', overlaying='y', side='right'))
    return fig

@app.callback(Output('slice-dice-graph', 'figure'),
              Input('slice-dice-graph', 'id'))
def update_slice_dice_graph(id):
    fig = px.treemap(df_slice_dice, path=['price_range', 'metacritic_range'], values='game_count')
    fig.update_layout(title='Game Count by Price Range and Metacritic Score (Windows Games)')
    return fig

@app.callback(Output('pivot-graph', 'figure'),
              Input('pivot-graph', 'id'))
def update_pivot_graph(id):
    fig = go.Figure()
    for column in df_pivot.columns[1:]:  # Skip the 'year' column
        fig.add_trace(go.Bar(x=df_pivot['year'], y=df_pivot[column], name=column))
    fig.update_layout(title='Games Released by Platform Combination', xaxis_title='Year', yaxis_title='Number of Games', barmode='stack')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
