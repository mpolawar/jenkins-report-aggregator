#!/usr/bin/python
import sys
sys.path.insert(0, ".")
from src.GetJenkinsData import GetJenkinsData

# Get Jenkins data to DB
jenkins_data = GetJenkinsData()
jenkins_data.readJobDetails()
jenkins_data.updateDatabase()
