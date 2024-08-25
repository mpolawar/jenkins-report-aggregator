#!/usr/bin/python
import sys
sys.path.insert(0, ".")
from src.GetJenkinsData import GetJenkinsData
from src.Dashboard import Dashboard

# Get Jenkins data to DB
jenkins_data = GetJenkinsData()
jenkins_data.readJobDetails()
jenkins_data.updateDatabase()
#jenkins_data.display_historical_results()

# Update the dashboard with the latest data
dashboard = Dashboard(jenkins_data.tables)
dashboard.updateDashboard()
