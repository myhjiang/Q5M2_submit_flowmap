import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import numpy as np
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_dangerously_set_inner_html
import pycountry_convert as pc


# read resident
people_df = pd.read_csv('https://raw.githubusercontent.com/myhjiang/Q5M2_dash_play/master/data/active_people.csv')

# read edge and build network
edge_df = pd.read_csv('https://raw.githubusercontent.com/myhjiang/Q5M2_dash_play/master/data/edges.csv', delimiter="\t", header=None)
edge_df.columns = ['user', 'friend']
G = nx.from_pandas_dataframe(edge_df, 'user', 'friend')
print('Graph made')

centroid_df = pd.read_csv('https://raw.githubusercontent.com/myhjiang/Q5M2_dash_play/master/data/edges.csv', encoding='latin1')  # for later use (rotate on selection)


def make_data():
    country_df = people_df.groupby(['country']).count().reset_index()
    country_df.columns = ['country', 'user_count']

    userset = set(people_df.userid.tolist())
    flow_df = people_df.drop_duplicates(subset='userid')  # just in case, not needed actually
    user_country_dict = pd.Series(flow_df.country.values, index=flow_df.userid).to_dict()

    def make_friend_list(user):
        friends = set(G.neighbors(user))
        present_friends = list(friends.intersection(userset))
        return present_friends

    flow_df['friend_id'] = flow_df.userid.apply(make_friend_list)
    flow_df = pd.DataFrame({'userid': np.repeat(flow_df.userid.values, flow_df.friend_id.str.len()),
                            'country': np.repeat(flow_df.country.values, flow_df.friend_id.str.len()),
                            'friend_id': np.concatenate(flow_df.friend_id.values).astype(
                                int)})  # explode the list to multiple rows
    flow_df['country_dest'] = flow_df['friend_id'].map(user_country_dict)

    # aggregate edge count to country
    flow_df.drop(columns=['friend_id'], inplace=True)
    flow_country = flow_df.groupby(['country', 'country_dest']).count().reset_index()
    flow_country.columns = ['country_from', 'country_to', 'edge_count']
    # drop edges pointing to self and zip origin and destination
    flow_country = flow_country[flow_country['country_from'] != flow_country['country_to']]
    flow_country['zipped'] = tuple(zip(flow_country['country_from'], flow_country['country_to']))

    return country_df, flow_country


def make_point_trace(df):
    point_trace = go.Scattergeo(
        locations=df['country'],
        hoverinfo='location',
        mode='markers',
        marker={'color': 'green', 'size': 5,
                'opacity': 0.7},
        unselected={'marker': {'opacity': 0.1}}
    )
    return point_trace


def make_edge_trace(df, from_selection=True):
    # edge stats: n 2k, min 1, max 7k, Q75 11, mean 45, median 3,
    if not from_selection:
        df = df[df['edge_count'] > 10]
        # after filter: n 500, min 11, max 7k, mean 161, median 30, Q75 82

    # todo: make a decent mapper
    def width_mapper(x):
        if x > 1000:
            return 15
        elif x > 500:
            return 8
        elif x > 100:
            return 4
        elif x > 50:
            return 2
        else:
            return 1

    edge_traces = []
    for index, row in df.iterrows():
        edge_trace = go.Scattergeo(
            locations=row['zipped'],
            mode='lines',
            line={'color': 'rgba(191, 178, 63, 0.2)', 'width': width_mapper(row['edge_count'])},
        )
        edge_traces.append(edge_trace)
    return edge_traces


def make_bars(df):
    df = df[df['user_count'] > 500].reset_index()
    bar_trace = go.Bar(
        y=df['country'],
        x=df['user_count'],
        width=1,
        hoverinfo='y+x',
        marker={'color': 'green'},
        orientation='h',
        unselected={'marker': {'opacity': 0.5}},
        selected={'marker': {'opacity': 1}}
    )
    bar_layout = dict(
        title=dict(
            text="Countries with over 500 active users",
            font=dict(color='rgb(255, 255, 255)')
        ),
        height=400,
        showlegend=False,
        margin=dict(l=50, t=50, b=0),
        paper_bgcolor='rgb(0, 0, 0)',
        plot_bgcolor='rgb(0, 0, 0)',

        yaxis=dict(
            color='rgb(255, 255, 255)',
            categoryorder='total descending',
        ),
        xaxis=dict(
            color='rgb(255, 255, 255)',
            title=dict(text='active user number',
                       font=dict(color='rgb(255, 255, 255)')
                       ),
            showgrid=False,
            range=(0, 13000),
            rangeslider=dict(visible=True, thickness=0.1, bordercolor='rgb(255, 255, 255)', borderwidth=1)
        )
    )
    return bar_trace, bar_layout, df


# map layout
# todo: what the heck is wrong with Sweden and Canada???
map_layout = go.Layout(
        title=dict(
            text='Friendship between countries',
            font=dict(color='rgb(255, 255, 255)')
        ),
        showlegend=False,
        margin=dict(l=0, t=50, b=0),
        paper_bgcolor='rgb(0, 0, 0)',
        plot_bgcolor='rgb(0, 0, 0)',
        geo=dict(
            bgcolor='rgb(0, 0, 0)',
            showland=True,
            showcountries=True,
            showocean=True,
            countrywidth=1,
            landcolor='rgb(50, 50, 50)',
            lakecolor='rgb(0, 0, 0)',
            oceancolor='rgb(0, 0, 0)',
            projection=dict(
                type='orthographic',
                rotation=dict(
                    lon=-100,
                    lat=40,
                    roll=0
                )
            )
        )
    )

# init
country_df, flow_df = make_data()
print(flow_df.edge_count.describe())

init_map_trace = make_edge_trace(flow_df, from_selection=False)
init_map_trace.append(make_point_trace(country_df))
init_bar_trace, init_bar_layout, init_bar_df = make_bars(country_df)

# dash part
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.scripts.config.serve_locally = True
server = app.server

app.layout = html.Div([
    # header and stuff
    html.Div([
        dash_dangerously_set_inner_html.DangerouslySetInnerHTML('''
        <center><strong ><font color="white"  font-family="Source Sans Pro" size=6 font-weight='bold'>Gowalla Global User Impression</font></strong></center>''')
    ], style={'backgroundColor': 'black'}),
    # graph columns
    html.Div([
        html.Div([
            dcc.Graph(
                id='flowmap',
                figure=go.Figure(
                    data=init_map_trace,
                    layout=map_layout
                )
            ),
            # place holder
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML(
                '''<div style="height:20px; width:100%; clear:both;"></div> '''),
            # numbers and stuff
            html.Div(id='info', children=[])
        ], className="six columns"),
        html.Div([
            dcc.Graph(
                id='barchart',
                figure=go.Figure(
                    data=init_bar_trace,
                    layout=init_bar_layout
                )
            ),
            # place taker
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML(
                '''<div style="height:50px; width:100%; clear:both;"></div> '''),
            # todo: update flourish and the iframe!
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML('''<iframe src='https://public.flourish.studio/visualisation/844004/embed' frameborder='0' scrolling='no' style='width:100%;height:600px;'></iframe><div style='width:100%!;margin-top:4px!important;text-align:right!important;'><a class='flourish-credit' href='https://public.flourish.studio/visualisation/844004/?utm_source=embed&utm_campaign=visualisation/844004' target='_top' style='text-decoration:none!important'><img alt='Made with Flourish' src='https://public.flourish.studio/resources/made_with_flourish.svg' style='width:105px!important;height:16px!important;border:none!important;margin:0!important;'> </a></div>''')
        ], className="six columns")
    ], className="row", style={'backgroundColor': 'black'}),
    html.Div(id='selected-countries', style={'display': 'none'}),
])


# update selected country data selected by bar or map
@app.callback(
    Output('selected-countries', 'children'),
    [Input('barchart', 'clickData'),
     Input('flowmap', 'clickData')]
)
def update_selected_data(bar_clicked, map_clicked):
    ctx = dash.callback_context
    holder = None
    # don't do anything if nothing is triggered
    if not ctx.triggered:
        print('not triggered')
        return holder
    else:
        triggered_list = ctx.triggered
        for item in triggered_list:
            if item['value'] is not None:
                if item['prop_id'] == 'flowmap.clickData':
                    holder = map_clicked['points'][0]['pointIndex']
                if item['prop_id'] == 'barchart.clickData':
                    y = bar_clicked['points'][0]['y']
                    holder = country_df.index[country_df['country'] == y].tolist()[0]
            else:
                continue
        return holder


# update bar by selected date
@app.callback(
    Output('barchart', 'figure'),
    [Input('selected-countries', 'children')],
    [State('barchart', 'figure')]
)
def update_bar(picked_country, bar_fig):
    if picked_country:
        # if picked, highlight the country and dim others
        country_name = country_df.iloc[picked_country]['country']
        bar_index = init_bar_df.index[init_bar_df['country']==country_name].tolist()
        bar_fig['data'][0]['selectedpoints'] = bar_index
    return bar_fig


# update map by selected date and country
@app.callback(
    Output('flowmap', 'figure'),
    [Input('selected-countries', 'children')],
    [State('flowmap', 'figure')]
)
def update_map(picked_country, map_figure):
    if picked_country:
        # highlight flows from that country only
        country_name = country_df.iloc[picked_country]['country']
        filtered_country_flow = flow_df[flow_df['country_from'] == country_name]
        map_trace = make_edge_trace(filtered_country_flow)
        map_trace.append(make_point_trace(country_df))
        map_figure['data'] = map_trace
        # highlight country and destinations
        country_to = filtered_country_flow['country_to'].tolist()
        index_list = country_df[country_df['country'].isin(country_to)].index.tolist()
        index_list.append(picked_country)
        map_figure['data'][-1]['selectedpoints'] = index_list
        # rotate map to center
        country_code_iso2 = pc.country_alpha3_to_country_alpha2(country_name)
        lat = centroid_df.loc[centroid_df['country']==country_code_iso2, 'latitude'].iloc[0]
        lon = centroid_df.loc[centroid_df['country']==country_code_iso2, 'longitude'].iloc[0]
        map_figure['layout']['geo']['projection']['rotation']['lat'] = lat
        map_figure['layout']['geo']['projection']['rotation']['lon'] = lon
    return map_figure


# update info below map
@app.callback(
    Output('info', 'children'),
    [Input('selected-countries', 'children')]
)
def update_info(picked_country):
    if not picked_country:
        return [dash_dangerously_set_inner_html.DangerouslySetInnerHTML("""<center><strong ><font color="white"  font-family="Source Sans Pro" size=2 font-weight='bold'>
        Currently showing countries with more than 10 connections <br>
        Pick a country on the map or on the bar for to show all connections of that country.
        </font></strong></center>""")]
    else:
        country = country_df.iloc[picked_country]['country']
        filtered_country_flow = flow_df[flow_df['country_from'] == country]
        n_country_to = len(filtered_country_flow)
        country_code_iso2 = pc.country_alpha3_to_country_alpha2(country)
        country_name = pc.country_alpha2_to_country_name(country_code_iso2)
        user_count = country_df.iloc[picked_country]['user_count']
        line_1 = f"""{country_name} has {user_count} active user(s)."""
        html_raw_1 = f'''<center><strong ><font color="white"  font-family="Source Sans Pro" size=2 font-weight="bold">{line_1}</font></strong></center>'''
        line_2 = f"""{country_name} has connections with {n_country_to} other countries"""
        html_raw_2 = f'''<center><strong ><font color="white"  font-family="Source Sans Pro" size=2 font-weight="bold">{line_2}</font></strong></center>'''
        line_3 = """To clear selections, refresh the webpage. """
        html_raw_3 = f'''<center><strong ><font color="gray"  font-family="Source Sans Pro" size=1 font-weight="100">{line_3}</font></strong></center>'''
        # todo: make it pretty if time allows...
        return [dash_dangerously_set_inner_html.DangerouslySetInnerHTML(html_raw_1),
                dash_dangerously_set_inner_html.DangerouslySetInnerHTML(html_raw_2),
                dash_dangerously_set_inner_html.DangerouslySetInnerHTML(html_raw_3)]


if __name__ == '__main__':
    app.run_server(debug=True)
