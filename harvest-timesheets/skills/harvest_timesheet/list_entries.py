#!/usr/bin/env python3
"""List recent time entries to find task IDs."""

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

from harvest_timesheet.config import get_harvest_credentials, load_project_config
from harvest_timesheet.harvest_api import HarvestClient

# Get credentials
access_token, account_id = get_harvest_credentials()
client = HarvestClient(access_token, account_id)

# Get project ID from config
config = load_project_config()
project_id = config['harvest']['project_id']

# Get time entries for the last 30 days
from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
to_date = datetime.now().strftime('%Y-%m-%d')

response = client.session.get(
    f"{client.BASE_URL}/time_entries",
    params={
        'from': from_date,
        'to': to_date,
        'project_id': project_id
    }
)

if response.status_code == 200:
    data = response.json()
    entries = data.get('time_entries', [])

    if entries:
        print(f"\nRecent time entries for project {project_id}:\n")

        # Collect unique tasks
        tasks = {}
        for entry in entries:
            task_id = entry['task']['id']
            task_name = entry['task']['name']
            if task_id not in tasks:
                tasks[task_id] = task_name

        print("Available tasks found in your entries:\n")
        for task_id, task_name in tasks.items():
            print(f"  Task ID: {task_id}")
            print(f"  Task Name: {task_name}")
            print()

        print(f"\nTotal entries found: {len(entries)}")
    else:
        print(f"\nNo time entries found for project {project_id} in the last 30 days")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
