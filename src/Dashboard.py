import dash
from dash import dcc, html
from dash import dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import json
import sqlite3

class Dashboard:
    def __init__(self, db_tables):
        self.db_path = './data/jenkins_data.db'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.db_table = db_tables[1]

    def updateDashboard(self):
        # Extract relevant data for the dashboard
        run_dates = []
        build_numbers = []
        from_builds = []
        to_builds = []
        databases = []
        excluded_plugins_list = []
        build_statuses = []
        comments = []

        # Fetch job data from the database
        cmd = 'SELECT timestamp, build_number, job_status, parameters, comment FROM ' + self.db_table
        self.cursor.execute(cmd)
        rows = self.cursor.fetchall()

        for row in rows:
            run_date, build_number, job_status, parameters, comment = row
            parameters = json.loads(parameters)
            from_build = parameters.get('from_build', 'N/A')
            if 'to_build' in parameters:
                #to_build = parameters['to_build']
                to_build = parameters.get('to_build')
            database = parameters.get('database', 'N/A')
            excluded_plugins = parameters.get('exception_list', 'N/A')

            run_date = run_date.split('T')[0]
            run_dates.append(run_date)
            build_numbers.append(build_number)
            from_builds.append(from_build)
            if 'to_build' in parameters:
                to_builds.append(to_build)
            databases.append(database)
            excluded_plugins_list.append(excluded_plugins)
            build_statuses.append(job_status)
            comments.append(comment)

        #if len(to_builds) > 0:
        if to_builds:
            # Create a DataFrame
            df = pd.DataFrame({
                'Date': run_dates,
                'Build Number': build_numbers,
                'From Build': from_builds,
                'To Build': to_builds,
                'Database': databases,
                'Excluded Plugins': excluded_plugins_list,
                'Status': build_statuses,
                'Comment': comments
            })

            columns = [
                {'name': 'Date', 'id': 'Date'},
                {'name': 'Build Number', 'id': 'Build Number'},
                {'name': 'From Build', 'id': 'From Build'},
                {'name': 'To Build', 'id': 'To Build'},
                {'name': 'Database', 'id': 'Database'},
                {'name': 'Excluded Plugins', 'id': 'Excluded Plugins'},
                {'name': 'Status', 'id': 'Status'},
                {'name': 'Comment', 'id': 'Comment', 'editable': True}
            ]
        else:
            df = pd.DataFrame({
                'Date': run_dates,
                'Build Number': build_numbers,
                'From Build': from_builds,
                'Database': databases,
                'Excluded Plugins': excluded_plugins_list,
                'Status': build_statuses,
                'Comment': comments
            })

            columns = [
                {'name': 'Date', 'id': 'Date'},
                {'name': 'Build Number', 'id': 'Build Number'},
                {'name': 'From Build', 'id': 'From Build'},
                {'name': 'Database', 'id': 'Database'},
                {'name': 'Excluded Plugins', 'id': 'Excluded Plugins'},
                {'name': 'Status', 'id': 'Status'},
                {'name': 'Comment', 'id': 'Comment', 'editable': True}
            ]

        # Initialize the Dash app with suppress_callback_exceptions=True
        app = dash.Dash(__name__, suppress_callback_exceptions=True)

        # Define the layout of the dashboard
        app.layout = html.Div(children=[
            html.Div(children=[
                dcc.Tabs(id='tabs', value='home', children=[
                    dcc.Tab(label='Home', value='home'),
                    dcc.Tab(label='XLR_Fresh_Install', value='xlr_fresh_install')
                ], vertical=True, style={'height': '100vh', 'borderRight': '1px solid #d6d6d6'}),
            ], style={'display': 'inline-block', 'width': '20%', 'verticalAlign': 'top'}),
            html.Div(id='tabs-content', style={'display': 'inline-block', 'width': '80%'})
        ])

        @app.callback(
            Output('tabs-content', 'children'),
            Input('tabs', 'value')
        )
        def render_content(tab):
            if tab == 'xlr_fresh_install':
                return html.Div([
                    html.H1(children=self.db_table),
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
            else:
                return html.Div([
                    html.H1('Welcome to the Dashboard')
                ])

        @app.callback(
            Output('output-state', 'children'),
            Input('save-button', 'n_clicks'),
            State('job-status-table', 'data')
        )
        def save_comments(n_clicks, data):
            if n_clicks > 0:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                for row in data:
                    build_number = row['Build Number']
                    comment = row['Comment']
                    cursor.execute(f'''
                        UPDATE {self.db_table} SET comment = ? WHERE build_number = ?
                    ''', (comment, build_number))
                    conn.commit()
                conn.close()
                return 'Comments Saved'
            return ''

        # Run the Dash app
        app.run_server(debug=True)