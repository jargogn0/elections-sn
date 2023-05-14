import os
import json
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objs as go
import datetime

# Replace this with your Mapbox access token
mapbox_access_token = "your_mapbox_access_token_here"

# Replace example_data with your actual data
example_data = pd.read_excel("new_elections_data.xlsx")

# Add Senegal GeoJSON data
senegal_geojson = json.load(open("senegal.geojson", "r"))

def process_data(data):
    df = data.copy()
    candidates = ["Macky SALL", "Idrissa SECK", "Ousmane Sonko", "Madické NIANG", "El hadji SALL"]
    
    for candidate in candidates:
        df[candidate] = pd.to_numeric(df[candidate], errors='coerce')
    
    df = df[df["Votes"] > 0]
    df = df.dropna(subset=candidates)
    
    for candidate in candidates:
        df[f"{candidate}"] = df[candidate] / df["Votes"] * 100

    df = pd.melt(df, id_vars=["Department", "Votes"], value_vars=[f"{candidate}" for candidate in candidates], var_name="Candidate", value_name="Percentage")
    
    return df


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

@app.server.before_request
def before_request():
    global api_data
    api_data = get_live_data()


current_row_index = 0


import pytz

def get_live_data():
    global current_row_index

    # Replace with the actual API or data source
    data = pd.read_excel("new_elections_data.xlsx")

    # Convert the Timestamp column to timezone-aware timestamps
    data['Timestamp'] = pd.to_datetime('2022-04-10 ' + data['Timestamp'], utc=True, format="%Y-%m-%d %H:%M:%S")

    # Filter data based on the current row index and the timestamp column
    filtered_data = data.iloc[:current_row_index]

    # Update the current row index
    current_row_index += 1
    if current_row_index > len(data):
        current_row_index = len(data)

    return filtered_data




api_data = get_live_data()
data = process_data(api_data)

candidate_colors = {
    "Macky SALL": "brown",
    "Idrissa SECK": "orange",
    "Ousmane Sonko": "darkgreen",
    "El hadji SALL": "darkblue",
    "Madické NIANG": "red",
}

candidate_images = {
    "Macky SALL": "macky_sall.jpeg",
    "Idrissa SECK": "idirissa_seck.jpeg",
    "Ousmane Sonko": "ousmane_sonko.jpeg",
    "Madické NIANG": "madicke_niang.jpeg",
    "El hadji SALL": "issa_sall.jpeg"
}

app.layout = dbc.Container(
    [
        html.H1("Senegal Election Results Dashboard", className="my-4"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Select Departments"),
                        dcc.Dropdown(
                            id="region-dropdown",
                            options=[
                                {"label": dept, "value": dept}
                                for dept in data["Department"].unique()
                            ],
                            multi=True,
                            placeholder="Select a department",
                            className="py-1",
                            style={"width": "250px", "height": "40px"},
                        ),
                    ],
                    lg=4,
                ),
         dbc.Col(
            [
                html.H5("Select Candidates"),
                dcc.Dropdown(
                    id="candidate-dropdown",
                    options=[
                        {"label": candidate, "value": candidate}
                        for candidate in candidate_colors.keys()
                    ],
                    multi=True,
                    placeholder="Select a candidate",
                    className="py-1",
                    style={"width": "250px", "height": "40px"},
                ),
            ],
            lg=4,
        ),
    ],
    className="my-4",
),
html.Div(id="candidate-info"),
dbc.Row(
    [
        dbc.Col(
            dcc.Graph(id="election-results-graph"),
            lg=12,
        ),
    ],
    className="my-4",
),
dbc.Row(
    [
        dbc.Col(
            dcc.Graph(id="sunburst-chart"),
            lg=12,
        ),
    ],
    className="my-4",
),
dbc.Row(
    [
        dbc.Col(
            dcc.Graph(id="election-results-map"),
            lg=12,
        ),
    ],
    className="my-4",
),
dbc.Row(
    [
        dbc.Col(
            dcc.Graph(id="scatterplot-graph"),
            lg=12,
        ),
    ],
    className="my-4",
),
    dcc.Interval(
            id="interval-component",
            interval=2 * 1000,  # in milliseconds, here it's set to update every 5 seconds
            n_intervals=0,
        ),
    ],
    fluid=True,
)

def generate_candidate_info(data, api_data, candidate_colors):
    candidate_info = []
    for candidate in candidate_colors.keys():
        candidate_name = candidate
        candidate_votes = api_data[candidate_name].sum()
        candidate_info.append(
            html.Div(
                [
                    html.Img(
                        src=app.get_asset_url(candidate_images[candidate_name]),
                        style={"height": "80px", "width": "80px"},
                    ),
                    html.P(candidate_name),
                    html.P(f"Votes: {candidate_votes}"),
                ],
                style={
                    "display": "inline-block",
                    "border": f"3px solid {candidate_colors[candidate]}",
                    "padding": "10px",
                    "margin": "5px",
                },
            )
        )

    return candidate_info


@app.callback(
    [
        Output("candidate-info", "children"),
        Output("election-results-graph", "figure"),
        Output("sunburst-chart", "figure"),
        Output("election-results-map", "figure"),
        Output("scatterplot-graph", "figure"),
    ],
    [
        Input("region-dropdown", "value"),
        Input("candidate-dropdown", "value"),
        Input("interval-component", "n_intervals"),
    ],
)

def update_dashboard(selected_departments, selected_candidates, n_intervals):
    # Get the live data
    api_data = get_live_data()
    data = process_data(api_data)
    filtered_data = data.copy()

    if selected_departments is not None and len(selected_departments) > 0:
        filtered_data = filtered_data[filtered_data["Department"].isin(selected_departments)]

    if selected_candidates is not None and len(selected_candidates) > 0:
        filtered_data = filtered_data[filtered_data["Candidate"].isin(selected_candidates)]

    candidate_info = generate_candidate_info(filtered_data, api_data, candidate_colors)

    # Create a bar chart with a secondary axis and line plots for each candidate
    bar_fig = go.Figure()

    for candidate in candidate_colors.keys():
        candidate_data = filtered_data[filtered_data["Candidate"] == candidate]
        bar_fig.add_trace(go.Bar(x=candidate_data["Department"], y=candidate_data["Percentage"],
                                 name=candidate, marker_color=candidate_colors[candidate]))

    bar_fig.update_layout(go.Layout(barmode="group", title="Election Results by Department",
                                    xaxis=dict(title="Department"), yaxis=dict(title="Percentage")))


    # Update hierarchical bar chart
    sunburst_fig = px.sunburst(
        filtered_data,
        path=['Department', 'Candidate'],
        values='Percentage',
        color='Candidate',
        color_discrete_map=candidate_colors,
        title="Election Results by Candidate and Department",
    )


    # Update map
    map_fig = px.choropleth_mapbox(
        filtered_data,
        geojson=senegal_geojson,
        locations="Department",
        featureidkey="properties.NAME_1",
        color="Percentage",
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=5,
        center={"lat": 14.6928, "lon": -17.4467},
        opacity=0.5,
        labels={"Percentage": "Percentage"},
        title="Election Results by Department on Map",
    )
    map_fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # Update boxplot
    boxplot_fig = px.box(
        filtered_data,
        x="Candidate",
        y="Percentage",
        color="Candidate",
        title="Percentage by Candidate",
        color_discrete_map=candidate_colors
    )


    return candidate_info, bar_fig, sunburst_fig, map_fig, boxplot_fig

if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
