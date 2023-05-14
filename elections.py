import os
import json
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objs as go
import time
import threading

mapbox_access_token = "your_mapbox_access_token_here"
excel_path = "elections_senegal_with_timestamps.csv"
example_data = pd.read_csv(excel_path)

with open("senegal.geojson", "r") as file:
    senegal_geojson = json.load(file)

data = example_data.copy()

def update_data():
    global data
    while True:
        data = pd.read_csv(excel_path)
        data['Timestamp'] = pd.Timestamp.now()
        time.sleep(5)

data_updater = threading.Thread(target=update_data)
data_updater.start()

def process_data(data):
    candidates = ["Macky_SALL", "Idrissa_SECK", "Ousmane_Sonko", "Madické_NIANG", "El_hadji_SALL"]
    df = pd.DataFrame(data)
    
    # Drop the existing 'Percentage' column
    if 'Percentage' in df.columns:
        df = df.drop(columns=['Percentage'])
    
    # Calculate the total votes for each department
    df['TotalVotes'] = df[candidates].sum(axis=1)
    
    # Calculate the percentage of votes for each candidate
    for candidate in candidates:
        df[f"{candidate}_Percentage"] = df[candidate] / df['TotalVotes'] * 100
    
    # Melt the DataFrame to make it tidy
    df = pd.melt(df, id_vars=["Department", "Votes"], value_vars=[f"{candidate}_Percentage" for candidate in candidates], var_name="Candidate", value_name="Percentage")
    
    # Remove the "_Percentage" suffix from the candidate names
    df['Candidate'] = df['Candidate'].str.replace("_Percentage", "")
    
    print("DataFrame columns:", df.columns)
    print("Candidates list:", candidates)
    
    return df


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

candidate_colors = {
    "Macky_SALL": "brown",
    "Idrissa_SECK": "orange",
    "Ousmane_Sonko": "darkgreen",
    "El_hadji_SALL": "darkblue",
    "Madické_NIANG": "red",
}

candidate_images = {
    "Macky_SALL": "macky_sall.jpeg",
    "Idrissa_SECK": "idirissa_seck.jpeg",
    "Ousmane_Sonko": "ousmane_sonko.jpeg",
    "Madické_NIANG": "madicke_niang.jpeg",
    "El_hadji_SALL": "issa_sall.jpeg"
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
                                for dept in sorted(data["Department"].unique())
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
                    style={"width":"250px", "height": "40px"},
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
],
fluid=True,
)

def generate_candidate_info(data, api_data, candidate_colors):
    candidate_info = {}
    candidates = data["Candidate"].unique()

    for candidate in candidates:
        total_votes = data[data["Candidate"] == candidate]["Votes"].sum()
        percentage = total_votes / data["Votes"].sum() * 100
        candidate_info[candidate] = {
            "total_votes": int(total_votes),
            "percentage": round(percentage, 2),
            "color": candidate_colors[candidate],
        }

    return candidate_info


# The rest of the code remains the same

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
    ],
)
def update_dashboard(selected_departments, selected_candidates):
    filtered_data = data.copy()

    if selected_departments is not None and len(selected_departments) > 0:
        filtered_data = filtered_data[filtered_data["Department"].isin(selected_departments)]

    if selected_candidates is not None and len(selected_candidates) > 0:
        filtered_data = filtered_data[filtered_data["Candidate"].isin(selected_candidates)]

    candidate_info = generate_candidate_info(filtered_data, candidate_colors)

    # The rest of the code inside the update_dashboard function remains the same

    bar_fig = go.Figure()

    for candidate in candidate_colors.keys():
        candidate_data = filtered_data[filtered_data["Candidate"] == candidate]
        bar_fig.add_trace(go.Bar(x=candidate_data["Department"], y=candidate_data["Percentage"],
                                 name=candidate, marker_color=candidate_colors[candidate]))

    bar_fig.update_layout(go.Layout(barmode="group", title="Election Results by Department",
                                    xaxis=dict(title="Department"), yaxis=dict(title="Percentage")))

    sunburst_fig = px.sunburst(
        filtered_data,
        path=['Department', 'Candidate'],
        values='Votes',
        color='Candidate',
        color_discrete_map=candidate_colors,
        title="Election Results by Candidate and Department",
    )

    map_fig = px.choropleth_mapbox(
        filtered_data,
        geojson=senegal_geojson,
        locations="Department",
        featureidkey="properties.NAME_1",
        color="Percentage",
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=5,
        center={"lat":14.692944, "lon": -17.446181},
        opacity=0.7,
        hover_name="Department",
        hover_data=["Candidate", "Percentage"],
        title="Election Results by Department",
    )
    map_fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

    scatter_fig = px.scatter(
        filtered_data,
        x="Votes",
        y="Percentage",
        color="Candidate",
        color_discrete_map=candidate_colors,
        title="Election Results Scatterplot",
        labels={"Votes": "Number of Votes", "Percentage": "Percentage"},
        hover_name="Department",
        hover_data=["Candidate", "Percentage"],
    )

    return (
        candidate_info,
        bar_fig,
        sunburst_fig,
        map_fig,
        scatter_fig,
    )

if __name__ == "__main__":
    app.run_server(debug=True)


