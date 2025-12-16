#!/usr/bin/env python3
"""List available tasks for a Harvest project."""

import sys
import os
from pathlib import Path

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

# List task assignments for the project
response = client.session.get(
    f"{client.BASE_URL}/projects/{project_id}/task_assignments"
)

if response.status_code == 200:
    data = response.json()
    print(f"\nAvailable tasks for project {project_id}:\n")
    for assignment in data['task_assignments']:
        task = assignment['task']
        print(f"  ID: {task['id']}")
        print(f"  Name: {task['name']}")
        print(f"  Active: {assignment['is_active']}")
        print()
else:
    print(f"Error: {response.status_code}")
    print(response.text)
