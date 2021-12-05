import re
import utils
import webbrowser

try:
    import dash
except ModuleNotFoundError:
    utils.install_dependencies()
    import dash
from dash.dependencies import Input, Output
from dash import dcc, html, dash_table


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)

webbrowser.open("http://127.0.0.1:8050/")
pscan_data = utils.read_table("PharmacoScan_96F.r8_UPMC_2.na36.dc_annot.csv")

search_data = utils.SearchData()


app.layout = html.Div(
    children=[
        html.H4("Pharmacoscan Query Tool", id="header"),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Dropdown(
                            id="gene_drop_down",
                            options=[
                                {"label": gene, "value": gene}
                                for gene in pscan_data["gene"].unique()
                            ],
                            placeholder="Select a gene to query.",
                            multi=False,
                        ),
                    ],
                ),
                dcc.Textarea(
                    id="text_rsid_search",
                    placeholder="Please enter an rsID to search for.",
                    style={"width": "100%"},
                ),
                html.Div(
                    id="text_rsid_search_error",
                    style={"whiteSpace": "pre-line", "color": "red"},
                ),
                dcc.Textarea(
                    id="text_pos_search",
                    placeholder="Please enter a position to search for.",
                    style={"width": "100%"},
                ),
                html.Div(
                    id="text_pos_search_error",
                    style={"whiteSpace": "pre-line", "color": "red"},
                ),
                html.Div(
                    [
                        html.Button("Submit", id="submit_button", n_clicks=0),
                        html.Div(
                            id="overall_error",
                            style={"whiteSpace": "pre-line", "color": "red"},
                        ),
                    ]
                ),
                html.Div(
                    dash_table.DataTable(id="data_table"),
                    style={"display": "inline-block", "width": "40%"},
                ),
            ],
            style={"display": "inline-block", "width": "20%"},
        ),
    ]
)


@app.callback(
    Output("text_rsid_search_error", "children"),
    Input("text_rsid_search", "value"),
)
def validate_rsid_input(rsid):
    search_data.rsid = None
    if rsid is None or rsid == "":
        return ""
    rsid = rsid.strip().lower()
    if re.match(r"^rs\d+$", rsid) is None:
        return "ERROR: rsID is in incorrect format. Format accepted is rs123456"
    possible_rsids = pscan_data["rsid"].unique()
    if rsid not in possible_rsids:
        return "ERROR: rsID provided does not exist within the file."
    search_data.rsid = rsid
    return ""


@app.callback(
    Output("text_pos_search_error", "children"),
    Input("text_pos_search", "value"),
)
def validate_position_input(position):
    search_data.position = None
    if position is None or position == "":
        return ""
    try:
        position = int(position)
    except ValueError:
        return "ERROR: Incorrect format provided for position. Must be in format 123456789."

    possible_positions = pscan_data["pos"].unique()
    if position not in possible_positions:
        return "ERROR: The position provided does not have a corresponding probe."
    search_data.position = position
    return ""


@app.callback(Output("gene_drop_down", "value"), Input("gene_drop_down", "value"))
def get_genes(gene):
    search_data.gene = gene
    return dash.no_update


@app.callback(
    Output("overall_error", "children"),
    Output("submit_button", "n_clicks"),
    Output("data_table", "columns"),
    Output("data_table", "data"),
    Input("submit_button", "n_clicks"),
)
def compile_results(n_clicks):
    if n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    n_clicks = 0
    if not search_data.gene and not search_data.rsid and not search_data.position:
        return (
            "Must supply one of gene, position, or rsid",
            n_clicks,
            dash.no_update,
            dash.no_update,
        )
    # Making a copy of the data here so I don't permanently overwrite
    search_data.data = pscan_data.copy()
    if search_data.gene:
        search_data.filter_by_gene()
        search_data.get_probe_count()
        search_data.send_cpic_request()
        if search_data.gene_cpic_data is not None:
            search_data.merge_data()
    if search_data.rsid:
        search_data.filter_by_rsid()
    if search_data.position:
        search_data.filter_by_position_input()
    # Creates variables needed to create the data table
    columns = [{"name": i, "id": i} for i in search_data.data.columns]
    data = search_data.data.to_dict("records")
    return "", n_clicks, columns, data


if __name__ == "__main__":
    app.run_server(port=8050)
