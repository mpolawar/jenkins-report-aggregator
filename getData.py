import requests
import json
import os
from datetime import datetime

# Jenkins server details
jenkins_url = 'https://jenkins-ng.xebialabs.com/jenkinsng/'
job_name = 'QualityEngineering/job/XLR_Fresh_Install/job/master'
username = 'mpolawar'
api_token = 'Omsai@1234' 

# API endpoint to get job details
api_url = f'{jenkins_url}/job/{job_name}/api/json?tree=allBuilds[number,result,timestamp,actions[parameters[*]]]'

# Make the API request
response = requests.get(api_url, auth=(username, api_token))

# Check if the request was successful
if response.status_code == 200:
    job_data = response.json()
    all_builds = job_data.get('allBuilds', [])

    # Load existing historical data
    if os.path.exists('historical_data.json'):
        with open('historical_data.json', 'r') as f:
            historical_data = json.load(f)
    else:
        historical_data = []

    # Append new build data
    for build in all_builds:
        parameters = {}
        for action in build.get('actions', []):
            if 'parameters' in action:
                for param in action['parameters']:
                    parameters[param['name']] = param['value']

        build_data = {
            'timestamp': datetime.fromtimestamp(build['timestamp'] / 1000).isoformat(),
            'build_number': build['number'],
            'job_status': build.get('result', 'N/A'),  # Use 'result' instead of 'status'
            'parameters': parameters
        }
        historical_data.append(build_data)

    # Save updated historical data
    with open('historical_data.json', 'w') as f:
        json.dump(historical_data, f, indent=4)
else:
    print(f'Failed to fetch job data: {response.status_code}')

# Function to display historical results
def display_historical_results():
    if os.path.exists('historical_data.json'):
        with open('historical_data.json', 'r') as f:
            historical_data = json.load(f)
            for entry in historical_data:
                print(f"Timestamp: {entry['timestamp']}")
                print(f"Build Number: {entry['build_number']}")
                print(f"Job Status: {entry['job_status']}")
                print(f"Parameters: {entry['parameters']}")
                print("-" * 40)
    else:
        print("No historical data found.")

# Display historical results
display_historical_results()
