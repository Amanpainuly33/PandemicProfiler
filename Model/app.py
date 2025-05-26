import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import os
from covid_prediction_model import COVIDPredictionModel
from visualization import COVIDVisualizer

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Get the directory of this file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load data
data_path = os.path.join(current_dir, 'timeseries_india.csv')
df = pd.read_csv(data_path)

# Initialize models
model = COVIDPredictionModel()
X_test, y_test = model.train_models(df)

# Initialize visualizer
visualizer = COVIDVisualizer(df)

# Get unique states
states = df['State/UnionTerritory'].unique()

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("COVID-19 India Dashboard", className="text-center mb-4"),
            html.P("Interactive dashboard for COVID-19 data analysis and prediction", className="text-center")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Filters"),
                dbc.CardBody([
                    html.Label("Select State:"),
                    dcc.Dropdown(
                        id='state-dropdown',
                        options=[{'label': state, 'value': state} for state in states],
                        value=None,
                        clearable=True
                    ),
                    html.Br(),
                    html.Label("Date Range:"),
                    dcc.DatePickerRange(
                        id='date-range',
                        start_date=df['Date'].min(),
                        end_date=df['Date'].max()
                    ),
                    html.Br(),
                    html.Button("Update", id="update-button", className="btn btn-primary mt-3")
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Timeline", children=[
                    dcc.Graph(id='timeline-graph')
                ]),
                dbc.Tab(label="Predictions", children=[
                    dcc.Graph(id='prediction-graph')
                ]),
                dbc.Tab(label="Growth Rate", children=[
                    dcc.Graph(id='growth-rate-graph')
                ]),
                dbc.Tab(label="Recovery Rate", children=[
                    dcc.Graph(id='recovery-rate-graph')
                ])
            ])
        ], width=9)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("State Comparison"),
                dbc.CardBody([
                    dcc.Dropdown(
                        id='state-comparison-dropdown',
                        options=[{'label': state, 'value': state} for state in states],
                        value=states[:3],
                        multi=True
                    ),
                    dcc.Graph(id='state-comparison-graph')
                ])
            ])
        ])
    ], className="mt-4")
], fluid=True)

# Callbacks
@app.callback(
    [Output('timeline-graph', 'figure'),
     Output('prediction-graph', 'figure'),
     Output('growth-rate-graph', 'figure'),
     Output('recovery-rate-graph', 'figure')],
    [Input('update-button', 'n_clicks')],
    [State('state-dropdown', 'value'),
     State('date-range', 'start_date'),
     State('date-range', 'end_date')]
)
def update_graphs(n_clicks, selected_state, start_date, end_date):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
        
    # Filter data based on date range
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    filtered_df = df[mask]
    
    # Create visualizations
    timeline = visualizer.create_timeline(selected_state)
    
    if selected_state:
        predictions = model.get_state_predictions(filtered_df, selected_state)
        prediction_plot = visualizer.create_prediction_plot(
            filtered_df[filtered_df['State/UnionTerritory'] == selected_state],
            predictions,
            selected_state
        )
    else:
        predictions = model.predict(filtered_df)
        prediction_plot = visualizer.create_prediction_plot(
            filtered_df.groupby('Date').agg({'Confirmed': 'sum'}).reset_index(),
            predictions['prophet_forecast']
        )
    
    growth_rate = visualizer.create_growth_rate_chart(selected_state)
    recovery_rate = visualizer.create_recovery_rate_chart(selected_state)
    
    return timeline, prediction_plot, growth_rate, recovery_rate

@app.callback(
    Output('state-comparison-graph', 'figure'),
    [Input('state-comparison-dropdown', 'value')]
)
def update_state_comparison(selected_states):
    if not selected_states:
        raise dash.exceptions.PreventUpdate
    return visualizer.create_state_comparison(selected_states)

if __name__ == '__main__':
    app.run(debug=True) 