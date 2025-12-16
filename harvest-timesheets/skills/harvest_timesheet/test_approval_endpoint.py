#!/usr/bin/env python3
"""Test different approval endpoints."""

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

# Get credentials
access_token, account_id = get_harvest_credentials()
client = HarvestClient(access_token, account_id)

# Test various endpoints
endpoints_to_test = [
    "/time_sheets",
    "/timesheets",
    "/approvals",
    "/time_entry_approvals"
]

print("Testing Harvest API endpoints for timesheet submission:\n")

for endpoint in endpoints_to_test:
    url = f"{client.BASE_URL}{endpoint}"
    print(f"Testing GET {endpoint}...")
    response = client.session.get(url)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Response: {response.json()}")
    print()
