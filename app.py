#!/usr/bin/env python3
from datetime import datetime
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from tidal_current_requests.tidal_current_requests import TidalCurrentRequester
import plotly.express as px
import pandas as pd
import numpy as np

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

server = app.server

# Load in API for getting NOAA requests
currents_requester = TidalCurrentRequester()

def gen_navbar():
    return dbc.NavbarSimple(
        children=[
            dbc.NavLink("Home", href="/", active="exact"),
            dbc.NavLink("Page 1", href="/page-1", active="exact"),
            dbc.NavLink("Page 2", href="/page-2", active="exact"),
        ],
        color="primary",
        dark=True,
    )


def gen_container_body():
    return dbc.Container(
        children = [
            dbc.Row(
                dbc.Col(
                    html.H2(children="Puget Sound Tidal Currents", style={'textAlign': 'center'})
                ),
                style={"padding-top": "1vh"}
            ),
            dbc.Row(
                dbc.Col(
                    html.Div(
                        id="live-update-last-update-text",
                        style={'textAlign': 'center'}
                    ),
                ),
                style={"padding-bottom": "1vh"}
            ),
            dbc.Row(
                [
                    dbc.Col(width=3, align="center", id="flow-card"),
                    dbc.Col(width=3, align="center", id="delta-card"),
                ],
                justify="evenly",
                style={"padding-bottom": "2vh"}
            ),
        ],
        class_name="pad-row",
        fluid=True
    )


def gen_interval():
    return dcc.Interval(
        id="interval-component",
        interval=5*60*1000, # update every five minutes
        n_intervals=0
    )


app.layout = html.Div(
    children = [
        #dcc.Location(id="url"),
        #gen_navbar(),
        gen_container_body(),
        dcc.Graph(id="live-update-currents-graph"),
        gen_interval()
    ]
)


@app.callback(
    Output("live-update-last-update-text", "children"),
    Output("live-update-currents-graph", "figure"),
    Output("flow-card", "children"),
    Output("delta-card", 'children'),
    Input("interval-component", "n_intervals")
)
def update_page(n):
    now = datetime.now()
    updated_text =  f"Last updated: {now.strftime('%Y-%m-%d %H:%M')}"
    df = pd.DataFrame(currents_requester.get_current_predictions_for_now())
    fig = px.line(
        df, x="Time", y="Current", color="Relationship", color_discrete_sequence=px.colors.qualitative.Dark24
    )
    current_flow, delta_per_hour = _get_current_flow_and_delta(df, now)
    flow_style, delta_style = _get_card_styles(current_flow, delta_per_hour)
    flow_card = _generate_card(
        "Tidal Current Velocity", "knots", current_flow, flow_style
    )
    delta_card = _generate_card(
        "Velocity Change", "knots per hour", delta_per_hour, delta_style
    )
    return updated_text, fig, flow_card, delta_card


def _get_current_flow_and_delta(df, now):
    df["Time_Delta"] = (df["Time"] - now).abs()
    index = df[df["Time_Delta"] == df["Time_Delta"].min()].index.values[0]
    current_flow = df.loc[index,"Current"]
    
    sub_df = df.loc[index-1:index+1,:]
    res = {}
    for col in ["Current", "Time"]:
        res[f"{col}_Delta"] = sub_df.loc[
                sub_df["Time"] == sub_df["Time"].max(), col
            ].values[0] - sub_df.loc[
                sub_df["Time"] == sub_df["Time"].min(), col
            ].values[0]
    change_per_hour = float(
        res["Current_Delta"] / (res["Time_Delta"] / np.timedelta64(1, "h"))
    )
    return current_flow, change_per_hour


def _generate_card(title, units, value, style):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(title, className="card-title"),
                html.P(units),
                dbc.Card(
                    dbc.CardBody(
                        html.H3(f"{value:.2f}")
                    ),
                    color=style
                ),
            ]
        ),
        color = "secondary"
    )


def _get_card_styles(current_flow, delta_per_hour):
    current_style = "success" if current_flow < -2.5 else "danger"
    if delta_per_hour < 0:
        delta_style = "success"
    elif current_flow < -2.5:
        delta_style = "warn"
    else:
        delta_style = "danger"
    return current_style, delta_style


if __name__ == "__main__":
    app.run_server(debug=True)
