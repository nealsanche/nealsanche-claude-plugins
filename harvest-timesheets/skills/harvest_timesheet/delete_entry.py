#!/usr/bin/env python3
"""Delete a time entry by ID."""

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

from harvest_timesheet.config import get_harvest_credentials
from harvest_timesheet.harvest_api import HarvestClient

if len(sys.argv) < 2:
    print("Usage: python3 delete_entry.py <entry_id>")
    sys.exit(1)

entry_id = sys.argv[1]

# Get credentials
access_token, account_id = get_harvest_credentials()
client = HarvestClient(access_token, account_id)

# Delete the entry
response = client.session.delete(f"{client.BASE_URL}/time_entries/{entry_id}")

if response.status_code == 200:
    print(f"✓ Successfully deleted entry {entry_id}")
else:
    print(f"✗ Error deleting entry: {response.status_code}")
    print(response.text)
