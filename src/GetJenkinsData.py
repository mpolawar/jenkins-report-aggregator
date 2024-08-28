import sqlite3
import requests
import json
import os
import sys
from datetime import datetime

class GetJenkinsData:
    def __init__(self):
        self.job_details_data = None
        self.username = None
        self.api_token = None
        self.jenkins_url = None
        self.job_name = None
        self.title = None
        self.api_url = None
        self.table_name = None
        self.jobs = []
        self.db_path = './data/jenkins_data.db'
        self.job_details_json = "./src/job_details.json"
        self.db_connection = sqlite3.connect(self.db_path)
        self.db_cursor = self.db_connection.cursor()

    def table_exists(self, table_name):
        self.db_cursor.execute('''
        SELECT name FROM sqlite_master WHERE type='table' AND name=?
        ''', (table_name,))
        return self.db_cursor.fetchone() is not None

    def create_table(self, table_name):
        self.db_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                build_number INTEGER,
                job_status TEXT,
                parameters TEXT,
                comment TEXT
            )
        ''')
        self.db_connection.commit()

    def readJobDetails(self):
        # Read job details from job_details.json
        if os.path.exists(self.job_details_json):
            with open(self.job_details_json, 'r') as f:
                self.job_details_data = json.load(f)
                print(f'job_details.json data is :\n  {self.job_details_data}\n')
        else:
            print("No job details found exiting the program.")
            sys.exit(1)

        # Read creds from job_details.json
        self.username = self.job_details_data.get('creds', {}).get('username', 'N/A')
        #print(self.username)
        self.api_token = self.job_details_data.get('creds', {}).get('api_token', 'N/A')
        #print(self.api_token)

        # Read all jobs details from job_details.json
        self.jobs = self.job_details_data.get('jobs', [])

    def updateDatabase(self):
        for job in self.jobs:
            print(f'\nUpdating database for {job["db_table"]}')

            # Update table with all OR latest entries
            if self.table_exists(job["db_table"]):
                print(f'Table {job["db_table"]} already exists')

                # API endpoint to get the latest job details
                self.api_url = f'{job["jenkins_url"]}/job/{job["job_name"]}/lastBuild/api/json?tree=number,result,timestamp,actions[parameters[*]]'
                response = requests.get(self.api_url, auth=(self.username, self.api_token))
                if response.status_code == 200:
                    latest_build = response.json()
                    print("LATEST BUILD FROM JENKINS IS: " + str(latest_build['number']))
                    # Check if the build_number already exists in the database
                    self.db_cursor.execute(f'''
                        SELECT 1 FROM {job["db_table"]} WHERE build_number = ?
                    ''', (latest_build['number'],))
                    if self.db_cursor.fetchone() is None:
                        # Insert the latest build data into the database
                        parameters = {}
                        for action in latest_build.get('actions', []):
                            if 'parameters' in action:
                                for param in action['parameters']:
                                    parameters[param['name']] = param['value']
                        build_data = {
                            'timestamp': datetime.fromtimestamp(latest_build['timestamp'] / 1000).isoformat(),
                            'build_number': latest_build['number'],
                            'job_status': latest_build.get('result', 'N/A'),
                            'parameters': json.dumps(parameters)
                        }
                        self.db_cursor.execute(f'''
                            INSERT INTO {job["db_table"]} (timestamp, build_number, job_status, parameters)
                            VALUES (?, ?, ?, ?)
                        ''', (build_data['timestamp'], build_data['build_number'], build_data['job_status'], build_data['parameters']))
                        self.db_connection.commit()
                        print(f'Build number {latest_build["number"]} added to the database table {job["db_table"]}')
                    else:
                        print(f'Build number {latest_build["number"]} already exists in the database')

            # Code to update all build details
            else:
                print(f'Table {job["db_table"]} does not exist')
                self.create_table(job["db_table"])

                # API endpoint to get job details
                self.api_url = f'{job["jenkins_url"]}/job/{job["job_name"]}/api/json?tree=allBuilds[number,result,timestamp,actions[parameters[*]]]'
                response = requests.get(self.api_url, auth=(self.username, self.api_token))
                if response.status_code == 200:
                    job_data = response.json()
                    print("JOB DATA IS: ")
                    all_builds = job_data.get('allBuilds', [])
                    print("ALL BUILDS ARE: ")
                    print(all_builds)
                    # Insert new build data into the database
                    for build in all_builds:
                        parameters = {}
                        for action in build.get('actions', []):
                            if 'parameters' in action:
                                for param in action['parameters']:
                                    parameters[param['name']] = param['value']
                        build_data = {
                            'timestamp': datetime.fromtimestamp(build['timestamp'] / 1000).isoformat(),
                            'build_number': build['number'],
                            'job_status': build.get('result', 'N/A'),
                            'parameters': json.dumps(parameters)
                        }
                        self.db_cursor.execute(f'''
                            INSERT INTO {job["db_table"]} (timestamp, build_number, job_status, parameters)
                            VALUES (?, ?, ?, ?)
                        ''', (build_data['timestamp'], build_data['build_number'], build_data['job_status'], build_data['parameters']))
                        self.db_connection.commit()
                else:
                    print(f'Failed to fetch job data: {response.status_code}')

    def display_historical_results(self):
        self.db_cursor.execute(f'SELECT * FROM {self.table_name}')
        rows = self.db_cursor.fetchall()
        for row in rows:
            print(f"Timestamp: {row[1]}")
            print(f"Build Number: {row[2]}")
            print(f"Job Status: {row[3]}")
            print(f"Parameters: {row[4]}")
            print("-" * 40)