#!/usr/bin/env python3
"""List all recent time entries across all projects."""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Auto-activate venv
def activate_venv():
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return
    script_dir = Path(__file__).parent
    venv_dir = script_dir / 'venv'
    if venv_dir.exists():
        python_exe = venv_dir / 'bin' / 'python3' if sys.platform != 'win32' else venv_dir / 'Scripts' / 'python.exe'
        if python_exe.exists():
            os.execv(str(python_exe), [str(python_exe)] + sys.argv)

activate_venv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from harvest_timesheet.config import get_harvest_credentials
from harvest_timesheet.harvest_api import HarvestClient

# Get credentials
access_token, account_id = get_harvest_credentials()
client = HarvestClient(access_token, account_id)

# Get time entries for the last 30 days
from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
to_date = datetime.now().strftime('%Y-%m-%d')

response = client.session.get(
    f"{client.BASE_URL}/time_entries",
    params={
        'from': from_date,
        'to': to_date
    }
)

if response.status_code == 200:
    data = response.json()
    entries = data.get('time_entries', [])

    if entries:
        print(f"\nAll recent time entries (last 30 days):\n")

        # Group by project
        projects = {}
        for entry in entries:
            project_id = entry['project']['id']
            project_name = entry['project']['name']
            task_id = entry['task']['id']
            task_name = entry['task']['name']

            if project_id not in projects:
                projects[project_id] = {
                    'name': project_name,
                    'tasks': {}
                }

            projects[project_id]['tasks'][task_id] = task_name

        for project_id, project_data in projects.items():
            print(f"Project ID: {project_id}")
            print(f"Project Name: {project_data['name']}")
            print(f"Tasks:")
            for task_id, task_name in project_data['tasks'].items():
                print(f"  - Task ID: {task_id}, Name: {task_name}")
            print()

        print(f"Total entries found: {len(entries)}")
    else:
        print("\nNo time entries found in the last 30 days")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
