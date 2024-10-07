import dash
from dash import dcc, html
from dash import dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import json
import sqlite3

class Dashboard:
    def __init__(self, jobs):
        self.db_path = './data/jenkins_data.db'
        self.jobs = jobs
        for job in self.jobs:
            job[job['title']] = job['db_table']

    def updateDashboard(self):
        app = dash.Dash(__name__, suppress_callback_exceptions=True)

        job_tabs = [dcc.Tab(label=job['title'], value=job['title']) for job in self.jobs]

        app.layout = html.Div(children=[
            html.Div(children=[
                dcc.Tabs(id='tabs', value='home', children=[
                    dcc.Tab(label='Home', value='home',  style={'font-family': 'Arial'}),
                    *job_tabs
                ], vertical=True, style={'height': '100vh', 'borderRight': '1px solid #d6d6d6'}),
            ], style={'display': 'inline-block', 'width': '20%', 'verticalAlign': 'top', 'font-family': 'Arial' }),
            html.Div(id='tabs-content', style={'display': 'inline-block', 'width': '80%'})
        ])

        @app.callback(
            Output('tabs-content', 'children'),
            Input('tabs', 'value')
        )
        def render_content(tab):
            if tab == 'home':
                return html.Div([
                    html.H1('Welcome to the Dashboard', style={'font-family': 'Arial', 'textAlign': 'left'})
                ])
            else:
                for job in self.jobs:
                    if job['title'] == tab:
                        current_job = job
                        tab = job['db_table']
                        break
                #print(f'Loading {tab} data')
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cmd = 'SELECT timestamp, build_number, job_status, parameters, comment FROM ' + tab
                cursor.execute(cmd)
                rows = cursor.fetchall()
                conn.close()

                # Initialize empty lists for each parameter mentioned in display_param
                run_dates = []
                build_numbers = []
                param_lists = {param: [] for param in current_job['display_param']}
                build_statuses = []
                comments = []

                # Populate the lists with data from the database
                for row in rows:
                    run_date, build_number, job_status, parameters, comment = row
                    parameters = json.loads(parameters)

                    run_date = run_date.split('T')[0]
                    run_dates.append(run_date)
                    build_numbers.append(build_number)
                    for param in current_job['display_param']:
                        param_value = parameters.get(param, 'N/A')
                        param_lists[param].append(param_value)
                    build_statuses.append(job_status)
                    comments.append(comment)

                # Create a DataFrame dynamically using the lists
                data = {
                    'Date': run_dates,
                    'Build Number': build_numbers,
                    'Status': build_statuses,
                    'Comment': comments
                }
                data.update(param_lists)
                df = pd.DataFrame(data)

                # Sort the DataFrame by 'Build Number' in descending order
                df = df.sort_values(by='Build Number', ascending=False)

                # Define columns for the DataTable
                columns = [{'name': 'Date', 'id': 'Date'},
                           {'name': 'Build Number', 'id': 'Build Number'}] + \
                          [{'name': param.replace('_', ' ').title(), 'id': param} for param in current_job['display_param']] + \
                          [{'name': 'Status', 'id': 'Status'},
                           {'name': 'Comment', 'id': 'Comment', 'editable': True}]


                return html.Div([
                    html.H1(children=job['title'],  style={'font-family': 'Arial', 'textAlign': 'left'}),
                    dash_table.DataTable(
                        id='job-status-table',
                        columns=columns,
                        data=df.to_dict('records'),
                        sort_action='native',
                        filter_action='native',
                        editable=True,
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'border': '1px solid black'
                        },
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold',
                            'border': '1px solid black'
                        },
                        style_data={
                            'border': '1px solid black'
                        },
                        style_data_conditional=[
                            {
                                'if': {
                                    'filter_query': '{Status} = "SUCCESS"',
                                    'column_id': 'Status'
                                },
                                'backgroundColor': 'lightgreen',
                                'color': 'white'
                            },
                            {
                                'if': {
                                    'filter_query': '{Status} = "FAILURE"',
                                    'column_id': 'Status'
                                },
                                'backgroundColor': 'lightcoral',
                                'color': 'white'
                            }
                        ]
                    ),
                    html.Button('Save Comments', id='save-button', n_clicks=0),
                    html.Div(id='output-state')
                ])

        @app.callback(
            Output('output-state', 'children'),
            Input('save-button', 'n_clicks'),
            State('job-status-table', 'data'),
            State('tabs', 'value')
        )
        def save_comments(n_clicks, data, tab):
            for job in self.jobs:
                if job['title'] == tab:
                    tab = job['db_table']
                    break
            if n_clicks > 0:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                for row in data:
                    build_number = row['Build Number']
                    comment = row['Comment']
                    cursor.execute(f'''
                        UPDATE {tab} SET comment = ? WHERE build_number = ?
                    ''', (comment, build_number))
                    conn.commit()
                conn.close()
                return 'Comments Saved'
            return ''

        app.run_server(debug=True)