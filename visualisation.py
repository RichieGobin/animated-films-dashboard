import dash
from dash import html, dcc, Input, Output, dash_table
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import os

# Helper function to create a MongoClient after forking
def get_mongo_collection():
    """Creates a new MongoClient for each process."""
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["AnimatedFilms"]
    return db["Films"]

# Define Dash app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "Animated Films Dashboard"

# App layout
app.layout = html.Div([
    html.H1('Animated Films Web Application connected to a Live Database', style={'textAlign': 'center'}),
    dcc.Interval(id='interval_db', interval=86400000 * 7, n_intervals=0),  # Weekly refresh
    html.Div(id='mongo-datatable', children=[]),
    html.Div([
        html.Div(id='scatter-graph', className='six columns'),
        html.Div(id='hist-graph', className='six columns'),
    ], className='row')
])

# Populate DataTable from MongoDB
@app.callback(Output('mongo-datatable', 'children'),
              Input('interval_db', 'n_intervals'))
def populate_datatable(n_intervals):
    try:
        collection = get_mongo_collection()
        df = pd.DataFrame(list(collection.find()))
        df['_id'] = df['_id'].astype(str)  # Convert ObjectId to string for display
        if df.empty:
            return html.Div("No data available in the collection.")
        return [
            dash_table.DataTable(
                id='our-table',
                data=df.to_dict('records'),
                columns=[{'id': col, 'name': col, 'editable': col != '_id'} for col in df.columns],
            )
        ]
    except Exception as e:
        print("Error fetching data:", e)
        return html.Div("Error loading data table.")

# Update MongoDB and generate visualizations
@app.callback(
    Output("scatter-graph", "children"),
    Output("hist-graph", "children"),
    Input("our-table", "data"),
)
def update_graphs(tabledata):
    try:
        if not tabledata:
            return html.Div("No data available for scatter plot"), html.Div("No data available for histogram")

        scatter_fig = px.scatter(tabledata, x='Title', y='Worldwide gross', title="Title vs Worldwide Gross")
        hist_fig = px.histogram(tabledata, x='Year', y='Worldwide gross', title="Year vs Worldwide Gross")

        return dcc.Graph(figure=scatter_fig), dcc.Graph(figure=hist_fig)
    except Exception as e:
        print("Error creating visualizations:", e)
        return html.Div("Error creating scatter plot"), html.Div("Error creating histogram")

# Expose the server for deployment
server = app.server

if __name__ == '__main__':
    app.run_server(debug=False)