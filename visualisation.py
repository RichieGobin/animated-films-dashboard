import dash
from dash import html, dcc, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import os

# MongoDB connection with environment variable
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://richiegobin:Password123@animatedfilms.rinmj.mongodb.net/AnimatedFilms?retryWrites=true&w=majority&appName=AnimatedFilms&maxPoolSize=20&minPoolSize=1&heartbeatFrequencyMS=10000")

def get_connection():
    for attempt in range(3):  # Retry up to 3 times
        try:
            client = MongoClient(MONGO_URI)
            db = client["AnimatedFilms"]
            collection = db["Films"]
            return collection
        except Exception as e:
            print(f"Retry {attempt + 1}: {e}")
    raise Exception("Failed to connect to MongoDB after 3 attempts")

collection = get_connection()  # Initialize connection globally

# Test MongoDB connection
print("Testing MongoDB connection...")
try:
    sample = list(collection.find().limit(1))
    print("Sample Data:", sample)
except Exception as e:
    print("Error during initial connection:", e)

# Define Dash app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "Animated Films Dashboard"

# App layout
app.layout = html.Div([
    html.H1('Animated Films Dashboard connected to a Live Database', style={'textAlign': 'center'}),
    dcc.Interval(id='interval_db', interval=86400000 * 7, n_intervals=0),  # Weekly refresh
    html.Div(id='mongo-datatable', children=[]),
    html.Div([
        html.Div(id='scatter-graph', className='six columns'),
        html.Div(id='hist-graph', className='six columns'),
    ], className='row'),
    dcc.Store(id='changed-cell')
])

# Test MongoDB connection route
@app.server.route('/test-connection')
def test_connection():
    try:
        sample_data = list(collection.find().limit(1))
        if sample_data:
            return f"Connected to MongoDB. Sample Data: {sample_data}", 200
        else:
            return "Connected to MongoDB, but no data found in the collection.", 200
    except Exception as e:
        return f"Error connecting to MongoDB: {e}", 500

# Populate DataTable from MongoDB
@app.callback(Output('mongo-datatable', 'children'),
              Input('interval_db', 'n_intervals'))
def populate_datatable(n_intervals):
    try:
        # Fetch data from MongoDB
        df = pd.DataFrame(list(collection.find()))
        print("Fetched DataFrame:", df.head())  # Debug: Print data
        if df.empty:
            return html.Div("No data available in the collection.")
        
        # Convert MongoDB _id to string for DataTable
        df['_id'] = df['_id'].astype(str)
        return [
            dash_table.DataTable(
                id='our-table',
                data=df.to_dict('records'),
                columns=[{'id': col, 'name': col, 'editable': col != '_id'} for col in df.columns],
            ),
        ]
    except Exception as e:
        print("Error fetching data:", e)
        return html.Div("Error loading data table.")

# Update MongoDB and generate visualizations
@app.callback(
    Output("scatter-graph", "children"),
    Output("hist-graph", "children"),
    Input("changed-cell", "data"),
    Input("our-table", "data"),
)
def update_d(cc, tabledata):
    try:
        # Debug: Print table data
        print("Table Data Received:", tabledata)
        if not tabledata:
            return html.Div("No data available for scatter plot"), html.Div("No data available for histogram")

        # Create visualizations
        scatter_fig = px.scatter(tabledata, x='Title', y='Worldwide gross', title="Title vs Worldwide Gross")
        hist_fig = px.histogram(tabledata, x='Year', y='Worldwide gross', title="Year vs Worldwide Gross")

        return dcc.Graph(figure=scatter_fig), dcc.Graph(figure=hist_fig)
    except Exception as e:
        print("Error creating visualizations:", e)  # Debugging
        return html.Div("Error creating scatter plot"), html.Div("Error creating histogram")

# Expose the server for deployment
server = app.server

if __name__ == '__main__':
    app.run_server(debug=False)
