import dash
from dash import dcc, html
from dash import dash_table
import pandas as pd
import json

# Load job data from JSON file
with open('historical_data.json', 'r') as f:
    job_data = json.load(f)

# Extract relevant data for the dashboard
run_dates = []
build_numbers = []
from_builds = []
databases = []
excluded_plugins_list = []
build_statuses = []

for job in job_data:
    run_date = job.get('timestamp', 'N/A')
    build_number = job.get('build_number', 'N/A')
    from_build = job.get('parameters', {}).get('from_build', 'N/A')
    database = job.get('parameters', {}).get('database', 'N/A')
    excluded_plugins = job.get('parameters', {}).get('exception_list', 'N/A')
    job_status = job.get('job_status', 'N/A')

    run_date = run_date.split('T')[0]
    run_dates.append(run_date)
    build_numbers.append(build_number)
    from_builds.append(from_build)
    databases.append(database)
    excluded_plugins_list.append(excluded_plugins)
    build_statuses.append(job_status)

# Create a DataFrame
df = pd.DataFrame({
    'Date': run_dates,
    'Build Number': build_numbers,
    'From Build': from_builds,
    'Database': databases,
    'Excluded Plugins': excluded_plugins_list,
    'Status': build_statuses,
})

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the dashboard
app.layout = html.Div(children=[
    html.H1(children='XLR Fresh Install Job Status'),
    dash_table.DataTable(
        id='job-status-table',
        columns=[
            {'name': 'Date', 'id': 'Date'},
            {'name': 'Build Number', 'id': 'Build Number'},
            {'name': 'From Build', 'id': 'From Build'},
            {'name': 'Database', 'id': 'Database'},
            {'name': 'Excluded Plugins', 'id': 'Excluded Plugins'},
            {'name': 'Status', 'id': 'Status'}
        ],
        data=df.to_dict('records'),
        sort_action='native',
        filter_action='native',
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
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)