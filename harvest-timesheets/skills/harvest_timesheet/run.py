#!/usr/bin/env python3
"""
Main entry point for Harvest Timesheet Automation skill.

This script can be called directly by Claude Code without needing
to activate a virtual environment.
"""

import sys
import os
from pathlib import Path

# Auto-activate virtual environment if not already active
def activate_venv():
    """Activate the virtual environment if it exists and we're not already in one."""
    # Check if we're already in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return  # Already in a venv

    # Find the venv directory
    script_dir = Path(__file__).parent
    venv_dir = script_dir / 'venv'

    if venv_dir.exists():
        # Determine the python executable path
        if sys.platform == 'win32':
            python_exe = venv_dir / 'Scripts' / 'python.exe'
        else:
            python_exe = venv_dir / 'bin' / 'python3'

        # Re-execute this script with the venv python
        if python_exe.exists():
            os.execv(str(python_exe), [str(python_exe)] + sys.argv)

# Activate venv before importing anything else
activate_venv()

# Ensure the package can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import workflows
from harvest_timesheet.main import (
    workflow_project_setup,
    workflow_setup_auth,
    workflow_submit_timesheet,
    main as interactive_main
)

def main():
    """Entry point with command-line argument support."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command in ['setup', 'project-setup', 'config']:
            workflow_project_setup()
        elif command in ['auth', 'authenticate', 'login']:
            workflow_setup_auth()
        elif command in ['submit', 'timesheet', 'run']:
            workflow_submit_timesheet()
        elif command in ['help', '-h', '--help']:
            print_help()
        else:
            print(f"Unknown command: {command}")
            print_help()
    else:
        # Interactive menu
        interactive_main()

def print_help():
    """Print usage help."""
    print("""
Harvest Timesheet Automation

Usage:
  python3 run.py [command]

Commands:
  setup      - Configure project (.project.yaml)
  auth       - Setup Harvest authentication
  submit     - Submit timesheet for current week
  help       - Show this help message

If no command is provided, an interactive menu will be shown.

Examples:
  python3 run.py setup
  python3 run.py submit
  python3 run.py
""")

if __name__ == "__main__":
    main()
