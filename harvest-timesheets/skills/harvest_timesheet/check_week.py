#!/usr/bin/env python3
"""Check time entries for the current week."""

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
from harvest_timesheet.git_analyzer import get_current_week_dates

# Get credentials
access_token, account_id = get_harvest_credentials()
client = HarvestClient(access_token, account_id)

# Get project ID from config
config = load_project_config()
project_id = config['harvest']['project_id']

# Get current week dates
week_dates = get_current_week_dates()
from_date = week_dates[0].strftime('%Y-%m-%d')
to_date = week_dates[-1].strftime('%Y-%m-%d')

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
        print(f"\nTime entries for week {from_date} to {to_date}:\n")

        # Group by date
        by_date = {}
        for entry in entries:
            spent_date = entry['spent_date']
            if spent_date not in by_date:
                by_date[spent_date] = []
            by_date[spent_date].append(entry)

        for date_str in sorted(by_date.keys()):
            date_entries = by_date[date_str]
            print(f"\n{date_str} - {len(date_entries)} entry/entries:")
            for entry in date_entries:
                print(f"  Entry ID: {entry['id']}")
                print(f"  Hours: {entry['hours']}")
                print(f"  Task: {entry['task']['name']}")
                print(f"  Notes: {entry['notes'][:100]}..." if len(entry['notes']) > 100 else f"  Notes: {entry['notes']}")
                print()

        print(f"\nTotal entries: {len(entries)}")
        total_hours = sum(e['hours'] for e in entries)
        print(f"Total hours: {total_hours}")
    else:
        print(f"\nNo time entries found for project {project_id} this week")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
