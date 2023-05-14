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
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dash import dash_table

#from flask import Flask
#server = Flask(__name__)


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


external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    {
        'href': 'https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap',
        'rel': 'stylesheet',
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server= app.server

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
    filtered_data = data.iloc[:current_row_index+1]  # Add +1 here

    # Update the current row index
    current_row_index += 1
    if current_row_index > len(data):
        current_row_index = len(data)

    return filtered_data


def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    return sentiment

@app.callback(
    Output("sentiment-analysis", "children"),
    Input("candidate-dropdown", "value"),
    Input("interval-component", "n_intervals"),
)

def update_sentiment_analysis(selected_candidates, n_intervals):
    # Get the data from your dataset
    # For example, assuming you have a dataset with a "Comments" column:
    comments_data = pd.read_excel("comments_data.xlsx")

    # Filter data based on selected candidates
    if selected_candidates and len(selected_candidates) > 0:
        comments_data = comments_data[comments_data["Candidate"].isin(selected_candidates)]

    # Analyze the sentiment of the comments
    comments_data["Sentiment"] = comments_data["Comments"].apply(analyze_sentiment)

    # Convert sentiment from dictionary to float
    comments_data["Sentiment"] = comments_data["Sentiment"].apply(lambda x: x["compound"])

    # Calculate average sentiment score for each candidate
    avg_sentiment = comments_data.groupby("Candidate")["Sentiment"].mean().reset_index()

    # Create a table to display the average sentiment scores
    sentiment_table = dash_table.DataTable(
        id='sentiment-table',
        columns=[{"name": i, "id": i} for i in avg_sentiment.columns],
        data=avg_sentiment.to_dict('records'),
        style_table={
            'overflowX': 'auto',
            'whiteSpace': 'normal'
        },
        style_cell={
            'minWidth': '0px', 'maxWidth': '500px',
            'whiteSpace': 'normal',
            'textOverflow': 'ellipsis',
            'textAlign': 'left'
        }
    )

    # Create a table to display the comments
    comments_table = dash_table.DataTable(
        id='comments-table',
        columns=[{"name": "Comment", "id": "Comments"}],
        data=comments_data[["Comments"]].to_dict('records'),
        style_table={
            'overflowX': 'auto',
            'whiteSpace': 'normal'
        },
        style_cell={
            'minWidth': '0px', 'maxWidth': '500px',
            'whiteSpace': 'normal',
            'textOverflow': 'ellipsis',
            'textAlign': 'left'
        }
    )

    # Combine both tables in one div
    combined_table = html.Div([
        html.H3("Sentiment Analysis Results"),
        html.Div([
            html.Div([
                html.H4("Average Sentiment Scores by Candidate"),
                sentiment_table
            ], className="six columns"),

            html.Div([
                html.H4("Comments"),
                comments_table
            ], className="six columns"),
        ], className="row"),
    ])

    return combined_table





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
        html.H1("Senegal - Elections Presidentielles 2019", className="my-4 text-center", style={"font-family": "Roboto", "font-weight": "bold"}),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Select Departments", style={"font-family": "Roboto"}),
                        dcc.Dropdown(
                            id="region-dropdown",
                            options=[
                                {"label": dept, "value": dept}
                                for dept in data["Department"].unique()
                            ],
                            multi=True,
                            placeholder="All Departments",
                            value=[],
                            persistence=True,
                            #persistence_type="session"
                        ),
                    ],
                    lg=6,
                ),
                dbc.Col(
                    [
                        html.H5("Select Candidates", style={"font-family": "Roboto"}),
                        dcc.Dropdown(
                            id="candidate-dropdown",
                            options=[
                                {"label": candidate, "value": candidate}
                                for candidate in data["Candidate"].unique()
                            ],
                            multi=True,
                            placeholder="All Candidates",
                            value=[],
                            persistence=True,
                            persistence_type="session"
                        ),
                    ],
                    lg=6,
                ),
            ],
            className="my-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.RadioItems(
                        id="map-mode-toggle",
                        options=[
                           # {"label": "Percentage Lead", "value": "lead"},
                           # {"label": "Flipped Departments", "value": "flip"},
                        ],
                        value="lead",
                        inline=True,
                        className="text-center",
                    ),
                    lg=12,
                ),
            ],
            className="my-4",
        ),

        dbc.Row(
            [
                dbc.Col(
                    html.Div(id="candidate-info", className="d-flex justify-content-center"),
                    lg=12,
                ),
            ],
            className="my-4",
        ),
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
                    html.Div(id="results-table"),
                    lg=12,
                ),
            ],
            className="my-4",
        ),
        
        dbc.Row(
            [
                dbc.Col(
                    html.Div(id="sentiment-analysis"),
                    lg=12,
                ),
            ],
            className="my-4",
        ),

        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="sunburst-chart"),
                    lg=6,
                ),
                dbc.Col(
                    dcc.Graph(id="election-results-map"),
                    lg=6,
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

        dbc.Row(
        [
            dbc.Col(
                html.Div(id="clicked-department-info"),
                lg=12,
            ),
        ],
        className="my-4",
       ),

        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="pie-chart"),
                    lg=6,
                ),
                dbc.Col(
                    dcc.Graph(id="line-chart"),
                    lg=6,
                ),
            ],
            className="my-4",
        ),

        dcc.Interval(
        id="interval-component",
        interval=10 * 1000,  # in milliseconds
        n_intervals=5,
        #max_intervals=12,  # Add this line
        ),

        dcc.Store(id="filtered-data-store"), 
    ],
    fluid=True,
)

@app.callback(
    [
        Output("candidate-info", "children"),
        Output("election-results-graph", "figure"),
        Output("sunburst-chart", "figure"),
        Output("election-results-map", "figure"),
        Output("scatterplot-graph", "figure"),
        Output("pie-chart", "figure"),  # Add this line
        Output("line-chart", "figure"),  # Add this line

    ],
    [
        Input("region-dropdown", "value"),
        Input("candidate-dropdown", "value"),
        Input("map-mode-toggle", "value"),
        Input("interval-component", "n_intervals"),
    ],
)

def update_dashboard(selected_departments, selected_candidates, map_mode, n_intervals):
    api_data = get_live_data()
    data = process_data(api_data)

    filtered_data = data.copy()
    if selected_departments and len(selected_departments) > 0:
        filtered_data = filtered_data[filtered_data["Department"].isin(selected_departments)]
    if selected_candidates and len(selected_candidates) > 0:
        filtered_data = filtered_data[filtered_data["Candidate"].isin(selected_candidates)]

    # The rest of the function remains the same

    candidate_info = [
        dbc.Card(
            [
                dbc.CardImg(src=app.get_asset_url(candidate_images[candidate]), top=True, style={"width": "100%"}),
                dbc.CardBody(
                    [
                        html.H4(candidate, className="card-title"),
                        html.P(
                            f"Percentage: {filtered_data.loc[filtered_data['Candidate'] == candidate, 'Percentage'].mean():.2f}%",
                            className="card-text",
                        ),
                    ]
                ),
            ],
            style={"width": "15rem", "display": "inline-block", "margin-right": "10px"},
        )
        for candidate in (data["Candidate"].unique() if not selected_candidates else selected_candidates)

    ]



    bar_fig = px.bar(
        filtered_data,
        x="Department",
        y="Percentage",
        color="Candidate",
        title="Election Results by Department",
        barmode="group",
        text="Percentage",
        color_discrete_map=candidate_colors,
    )
    bar_fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    bar_fig.update_layout(uniformtext_minsize=8, uniformtext_mode="hide")

    sunburst_fig = px.sunburst(
        filtered_data,
        path=["Candidate", "Department"],
        values="Percentage",
        title="Election Results by Candidate and Department",
        color="Candidate",
        color_discrete_map=candidate_colors,
    )
    
    # Replace the map_fig definition in the update_dashboard function with the following code:
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
        hover_data=["Department", "Candidate", "Percentage"],
    )


    map_fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            zoom=5,
            center={"lat": 14.6928, "lon": -17.4467},
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        title="Election Results by Department on Map"
    )

    scatter_fig = px.scatter(
        filtered_data,
        x="Votes",
        y="Percentage",
        color="Candidate",
        size="Percentage",
        hover_data=["Department", "Candidate"],
        labels={"Votes": "Total Votes"},
        title="Election Results Scatterplot",
        color_discrete_map=candidate_colors,
    )


    pie_fig = px.pie(
    filtered_data,
    values="Percentage",
    names="Candidate",
    title="Election Results by Candidate",
    color_discrete_map=candidate_colors,
    )

    line_fig = px.line(
    filtered_data,
    x="Department",
    y="Percentage",
    color="Candidate",
    title="Election Results Trend",
    line_shape="spline",
    color_discrete_map=candidate_colors,
    )


    return candidate_info, bar_fig, sunburst_fig, map_fig, scatter_fig, pie_fig, line_fig


@app.callback(
    Output("results-table", "children"),
    [Input("interval-component", "n_intervals")],
)


def update_results_table(n_intervals):
    api_data = get_live_data()
    data = process_data(api_data)
    total_votes_data = data.copy()
    total_votes_data["Votes"] = (total_votes_data["Percentage"] * total_votes_data["Votes"]) / 100
    table_data = total_votes_data.pivot_table(
        index="Department",
        columns="Candidate",
        values="Votes",
        aggfunc="sum",
    ).reset_index()

    # Round the values in the table_data DataFrame
    table_data.iloc[:, 1:] = table_data.iloc[:, 1:].round()

    table = dbc.Table.from_dataframe(
        table_data,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="table-striped",
        style={"backgroundColor": "white", "color": "black"},
    )

    return table

@app.callback(
    Output("clicked-department-info", "children"),
    Input("election-results-map", "clickData"),
)
def display_clicked_department_info(clickData):
    if clickData is None:
        return "Click on a department to see detailed results"

    department = clickData["points"][0]["location"]
    results = data[data["Department"] == department]

    # Display the results for the clicked department
    return dbc.Table.from_dataframe(
        results,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="table-striped",
        style={"backgroundColor": "white", "color": "black"},
    )



if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 8080))
