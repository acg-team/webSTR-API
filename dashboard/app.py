# Run this app with 'python app.py'
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.colors import n_colors
from dash.exceptions import PreventUpdate

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

# STR variation in CRC
crc_sn = pd.read_csv("./data/filtered_sn_str.csv")
crc_pt = pd.read_csv("./data/filtered_pt_str.csv", low_memory=False)

# Gene expression and subtype information in CRC
exp_1 = pd.read_csv("./data/norm_exp_tumor.csv")
exp_2 = pd.read_csv("./data/norm_exp_normal.csv")
sn_info = pd.read_csv("./data/normaltumor_info.csv", index_col = "patient").T
pt_info = pd.read_csv("./data/primarytumor_info.csv", index_col = "patient").T

# somatic variants in CRC
crc_snv = pd.read_csv("./data/crc_snv_sorted.csv")

# WebSTR API 
webstr_link = "http://webstr-api.ucsd.edu/repeats"

def retrieve_str(gene_name, sample):
    # retrieve STRs from database
    resp = requests.get(webstr_link, params = {'gene_names' : gene_name})
    df_str = pd.DataFrame.from_records(resp.json())
    df_str["tmp_id"] = df_str["chr"].str.cat(df_str["start"].astype("str"), sep = "_")
    
    if sample == "normal samples":
        exp = exp_2.query("gene_name == @gene_name").T.drop(index = "gene_name")
        exp.index = [name.rstrip("_N") for name in exp.index]
        crc = crc_sn
        info = sn_info

    if sample == "tumor samples":
        exp = exp_1.query("gene_name == @gene_name").T.drop(index = "gene_name")
        exp.index = [name.rstrip("_T") for name in exp.index]
        crc = crc_pt
        info = pt_info
    
    exp.columns = ["gene_exp"]
    gene_str_data = pd.merge(crc, df_str, on = "tmp_id", how = "inner", suffixes=('', '_y')) \
                .merge(exp, how = "left", left_on = "patient", right_on = exp.index) \
                .merge(info, how = "left", left_on = "patient", right_on = info.index) \
                .dropna(subset = ["gene_exp", "mean_diff"])
    gene_str_data["mean_length"] = (gene_str_data["allele_a"] + gene_str_data["allele_b"])/2
    
    return gene_str_data

def generate_options(selected_str):
    
    desc_str = selected_str[["tmp_id", "mean_length"]].groupby("tmp_id")  \
                           .agg({"tmp_id": "count", "mean_length" : "std"})  \
                           .query("mean_length != 0") # remove variance zero 
    desc_str.columns = ["count", "var"]
    desc_str = desc_str.sort_values(by = ["count", "var"], ascending = False) \
                       .loc[desc_str["count"]/selected_str["patient"].nunique() > 0.3] # detected in at least 30% samples
    
    return desc_str.index #[{'label': i, 'value': i} for i in desc_str.index]    

def generate_graph(str_data, istr):
    
    all_str_set = pd.DataFrame.from_dict(str_data)
    str_set = all_str_set.loc[all_str_set["tmp_id"] == istr]
    ref = str_set["ref"].values[0]
    
    fig = go.Figure()
    for num_box in np.sort(str_set["mean_length"].unique()):
        y = str_set.loc[str_set["mean_length"] == num_box, "gene_exp"]
        if num_box == ref:
            box_color = '#DAA520'
        elif num_box < ref:
            box_color = '#457b9d' 
        elif num_box > ref:
            box_color = '#e63946' 
        fig.add_trace(go.Box(y = y, 
                            name = str(num_box),
                            boxpoints='all',
                            jitter=0.5,
                            pointpos=0,
                            marker = dict(color = box_color)))
    fig.update_layout(
       # title = gene_name + " expression level in tumor samples and STR mean length",
        xaxis_title = "Mean Length of STRs (Ref. Allele = " + str(ref) + ")",
        yaxis_title = "Normalized Gene expression ",
        font = dict(family="Arial", size=14),
        template = "plotly_white")
    
    return fig

def str_graph(sg_pt):
    
    hm_data = sg_pt.loc[sg_pt["tmp_id"].isin(generate_options(sg_pt))]
    unit_name = dict(hm_data[["tmp_id", "period"]].drop_duplicates("tmp_id").values)
    hm_data = hm_data[["tmp_id", "patient", "mean_length"]].pivot(index = "tmp_id", columns = "patient")
    hm_data.columns = hm_data.columns.droplevel()
    
    colors = n_colors('rgb(69, 123, 157)', 'rgb(230, 57, 70)', hm_data.shape[0], colortype='rgb')
    fig = go.Figure()
    i=0
    for ind in hm_data.mean(axis = 1).sort_values().index:
        fig.add_trace(go.Violin(x = hm_data.loc[ind,:], 
                                name = ind + "\t" + "(unit=" + str(unit_name[ind]) + ")", 
                                line_color = colors[i]))
        i = i+1
    
    # Reduce opacity to see all histograms
    fig.update_traces(opacity=0.85, 
                      orientation='h', 
                      side='positive', 
                      width = 2, 
                      points = False)
    # Overlay both histograms
    fig.update_layout(barmode='overlay', 
                      showlegend=False, 
                      title = "Overall STR Length Variations in Primary Tumor Samples",
                      yaxis = dict(tickmode = "linear"),
                      xaxis_title = "Mean Length of STRs",
                      yaxis_showgrid = True,
                      font = dict(family="Arial", size=14),
                      template = "plotly_white")
    
    return fig
    
def subtype_graph(str_data, istr, subtype):
    
    data = pd.DataFrame.from_dict(str_data)
    data = data.loc[data["tmp_id"] == istr].sort_values(by = ["mean_length"])
    
    if subtype == "MSI":
        box_color = ["#e63946", "#457b9d"]
    else:
        box_color = ["#e63946", "#457b9d", "#DAA520", "#8FBC8F"]
    fig = go.Figure()
    for cms, color in zip(np.sort(data[subtype].unique()), box_color):
        fig.add_trace(go.Box(y = data.loc[data[subtype] == cms, "gene_exp"], 
                        x = data.loc[data[subtype] == cms, "mean_length"], 
                        boxpoints = 'all',
                        pointpos = 0,
                        marker_size = 4,
                        marker_color = color,
                        name = cms))
    fig.update_layout(
        yaxis_title='Normalized gene expression',
        xaxis_title = "Mean Length of STRs",
        template = "plotly_white",
        font = dict(family="Arial", size=14),
        #title = "expression level in tumor samples and STR mean length",
        boxmode='group' # group together boxes of the different traces for each value of x
    )
    return fig

def paired_graph(sn_str_data, pt_str_data, istr):
    
    sn_str_data = pd.DataFrame.from_dict(sn_str_data)
    pt_str_data = pd.DataFrame.from_dict(pt_str_data)
    fg_sn = sn_str_data.loc[sn_str_data["tmp_id"] == istr]
    fg_pt = pt_str_data.loc[pt_str_data["tmp_id"] == istr]
    # match patients
    patients = np.intersect1d(fg_sn["patient"].unique(), fg_pt["patient"].unique())
    fg_sn = fg_sn.loc[fg_sn["patient"].isin(patients)]
    fg_pt = fg_pt.loc[fg_pt["patient"].isin(patients)]
    fg = pd.merge(fg_sn, fg_pt, on = "patient")
    fg["diff_length"] = fg["mean_length_y"] - fg["mean_length_x"]
    fg["diff_exp"] = fg["gene_exp_y"] - fg["gene_exp_x"]
    
    fig = go.Figure()
    fig.add_trace(go.Box(y = fg["diff_exp"], 
                 x = fg["diff_length"], 
                 boxpoints='all',
                 pointpos=0,
                 marker_size=6,
                 marker = dict(color = '#e63946')))
    fig.update_layout(
        yaxis_title='Gene Expression Difference',
        xaxis_title = "Length Difference of STRs",
        title = "Primary Tumor vs Solid Normal",
        template = "plotly_white",
        font = dict(family="Arial", size=14),
        boxmode='group' # group together boxes of the different traces for each value of x
    )
    return fig

def mu_str_graph(mu_data, gene_name):
    
    fig = go.Figure()
    fig.add_trace(go.Violin(y = mu_data.loc[mu_data['type'] == "Mutant", "mean_length"],
                        name = gene_name + "+ (N=" + str(mu_data["type"].value_counts()["Mutant"]) + ")", 
                        line_color = '#e63946', box_visible=True))

    fig.add_trace(go.Violin(y = mu_data.loc[mu_data['type'] == "WT", "mean_length"],
                        name = gene_name + "- (N=" + str(mu_data["type"].value_counts()["WT"]) + ")", 
                        line_color = "#457b9d", box_visible=True))
    fig.update_traces(meanline_visible=True, jitter=0.02)
    fig.update_layout(yaxis_title = "Mean length of STRs",
                      font = dict(family="Arial", size=14),
                      template = "plotly_white")
    
    return fig

def mu_gene_graph(mu_data, gene_name):
    
    fig = go.Figure()
    fig.add_trace(go.Violin(x = mu_data.loc[mu_data['type'] == 'Mutant', 'mean_length'],
                            y = mu_data.loc[mu_data['type'] == 'Mutant', 'gene_exp'],
                            legendgroup='Yes', scalegroup='Yes', name= gene_name + '+',
                            side = 'negative',
                            line_color = '#e63946')
                )
    fig.add_trace(go.Violin(x = mu_data.loc[mu_data['type'] == 'WT', 'mean_length'],
                            y = mu_data.loc[mu_data['type'] == 'WT', 'gene_exp'],
                            legendgroup='No', scalegroup='No', name= gene_name + '-',
                            side='positive',
                            line_color = '#457b9d')
                )
    fig.update_traces(meanline_visible=True, jitter=0.02)
    fig.update_layout(violingap=0, 
                    violinmode='overlay',
                    violingroupgap=0,
                    xaxis_title = "Mean Length of STRs",
                    yaxis_title = "Normalized Gene Expresion",
                    font = dict(family="Arial", size=14),
                    template = "plotly_white")
    
    return fig
    
tab1_content = html.Div(
    [
        html.Div(
            [
                dbc.Label("STRs in Normal Samples"),
                dcc.Dropdown(id = "str-sn")
            ]
        ),
        html.Br(),
        dbc.RadioItems(
            id = "sn-type",
            options = [
             {"label": "Only Normal", "value": "only normal"},
             {"label": "Paired Tumor", "value": "paired tumor"}],
            inline = True,
            value = "only normal"
        ),
        dcc.Graph(id = "graph-sn"),       
    ],
    style = {"padding-top": "5px",
             "padding-left": "10px",
             "padding-right": "5px"}
)

tab2_content =  html.Div(
    [
        html.Div(
            [
                dbc.Label("STRs in Tumor Samples"),
                dcc.Dropdown(id = "str-pt")
            ]
        ),
        html.Br(),
        dbc.RadioItems(
            id = "pt-type",
            options = [
             {"label": "All", "value": "All"},
             {"label": "CMS", "value": "CMS"},
             {"label": "MSI", "value": "MSI"}],
            inline = True,
            value = "All"
        ),
        dcc.Graph(id = "graph-pt"),       
    ],
    style = {"padding-top": "5px",
             "padding-left": "5px",
             "padding-right": "10px"}
)
        
app.layout = dbc.Container(
    [   
        dcc.Store(id = "sn-str-data"),
        dcc.Store(id = "pt-str-data"),
        # webpage title
        html.H1("STR variation in TCGA CRC",
                style = {'textAlign':'center',  
                        'color':'darkblue',
                        'fontSize'  : '30px',
                        'fontWeight': 'bold'}
                ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Label("Input Gene: "),
                    width = "auto"
                ),
                dbc.Col(
                    dbc.Input(
                    id = "gene-name",
                    type = "text",
                    value = "SYNE1",
                    ), md = 3,
                ),
                dbc.Col(
                dbc.Button("Submit",
                color="primary",
                id="button",
                outline=True,
                ), width = "auto"
                ), 
            ],justify = "center"),
        html.Br(),
        # dbc.Row(
        #     [
        #         dbc.Col(tab1_content),
        #         dbc.Col(tab2_content)
        #     ], align = "center",
        # )
        # html.Div(
        #     [
        #     dbc.Tabs(
        #         [
        #             dbc.Tab(tab1_content, label = "Normal samples", tab_id = "tab_1"),
        #             dbc.Tab(tab2_content, label = "Tumor samples", tab_id = "tab_2"),
        #         ],
        #         id = "tabs",
        #         active_tab = "tab_1",
        #     ),
        #     html.Div(id = "content"),
        #    ]
        # )
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(html.H5("STR Variation")),
                    dbc.CardBody([
                        dcc.Graph(id = "graph-str")
                    ])
                ])
            )
        ], align = "center"),
        html.Br(),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(html.H5("STR - Gene Expression")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(tab1_content, md = 4),
                            dbc.Col(tab2_content, md = 8)
                            ])
                        ])]
                    ))
        ], align = "center"),
        html.Br(),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(html.H5("STR - Somatic Mutation")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(dcc.Graph(id = "mu-str"), md = 6),
                            dbc.Col(dcc.Graph(id = "mu-gene"), md = 6)
                        ])
                    ])
                ])
            )
        ]),
        html.Br()
    ],
    # style = {
    #     "margin-left": "3%",
    #     "margin-right": "3%"},
)

@app.callback(
    Output("sn-str-data", "data"),
    Output("pt-str-data", "data"),
    Output("graph-str", "figure"),
    Input('button', 'n_clicks'),
    State("gene-name", "value")
)
def update_str(n_clicks, selected_gene):
    sg_sn = retrieve_str(selected_gene, "normal samples")
    sg_pt = retrieve_str(selected_gene, "tumor samples")
    selected = ["tmp_id", "patient", "period", "mean_length", "ref", "gene_exp", "CMS", "MSI"]
    sg_sn = sg_sn[selected]
    sg_pt = sg_pt[selected]
    return sg_sn.to_dict('records'), sg_pt.to_dict("records"), str_graph(sg_pt)

@app.callback(
    Output("str-sn", "options"),
    Input("sn-str-data", "data")
    
)
def update_sn_str_selection(sn_str_data):
    str_data = pd.DataFrame.from_dict(sn_str_data)
    return generate_options(str_data)

@app.callback(
    Output("str-pt", "options"),
    Input("pt-str-data", "data")
)
def update_pt_str_selection(pt_str_data):
    str_data = pd.DataFrame.from_dict(pt_str_data)
    return generate_options(str_data)


@app.callback(
    Output("graph-sn", "figure"),
    Input("sn-str-data", "data"),
    Input("pt-str-data", "data"),
    Input("str-sn", "value"),
    Input("sn-type", "value")
)

def update_sn_graph(sn_str_data, pt_str_data, sn_str, sn_type):
    if sn_str is None:
        return {}
    elif sn_type == "only normal":
        return generate_graph(sn_str_data, sn_str) 
    elif sn_type == "paired tumor":
        return paired_graph(sn_str_data, pt_str_data, sn_str)

@app.callback(
    Output("graph-pt", "figure"),
    Input("pt-str-data", "data"),
    Input("str-pt", "value"),
    Input("pt-type", "value")
)
def update_pt_graph(pt_str_data, pt_str, pt_type):
    if pt_str is None:
        return {}
    elif pt_type == "All":
        return generate_graph(pt_str_data, pt_str)
    else:
        return subtype_graph(pt_str_data, pt_str, pt_type)
    
@app.callback(
    Output("mu-str", "figure"),
    Output("mu-gene", "figure"),
    Input("pt-str-data", "data"),
    Input("str-pt", "value"),
    State("gene-name", "value")
)
def update_mu_graph(pt_str_data, pt_str, gene_name):
    if pt_str is None:
        return {}, {}
    else:
        gene_snv = pd.DataFrame(crc_snv.loc[crc_snv["Hugo_Symbol"] == gene_name,
                                            "patient"].value_counts())
        gene_snv.columns = ["Mu_Count"]
        sg_pt = pd.DataFrame.from_dict(pt_str_data)
        str_data = sg_pt.loc[sg_pt["tmp_id"] == pt_str]
        mu_data = str_data[["patient", "gene_exp", "mean_length"]].merge(gene_snv, 
                    left_on = "patient", right_on = gene_snv.index, how = "left")
        mu_data["type"] = np.where(mu_data["Mu_Count"].isna(), "WT", "Mutant")
        
        return mu_str_graph(mu_data, gene_name), mu_gene_graph(mu_data, gene_name)
    
if __name__ == '__main__':
    app.run_server(debug = True)
