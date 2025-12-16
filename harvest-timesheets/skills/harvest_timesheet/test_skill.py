#!/usr/bin/env python3
"""
Test script for Harvest timesheet automation skill.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from harvest_timesheet.main import (
    workflow_project_setup,
    workflow_setup_auth,
    workflow_submit_timesheet
)

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  HARVEST TIMESHEET AUTOMATION - TEST")
    print("=" * 60)
    print("\nWhat would you like to test?\n")
    print("1. Test project setup workflow")
    print("2. Test authentication setup workflow")
    print("3. Test timesheet submission workflow (requires setup)")
    print("4. Run main menu")
    print("5. Exit")

    choice = input("\nChoice (1-5): ").strip()

    if choice == "1":
        workflow_project_setup()
    elif choice == "2":
        workflow_setup_auth()
    elif choice == "3":
        workflow_submit_timesheet()
    elif choice == "4":
        from harvest_timesheet.main import main
        main()
    elif choice == "5":
        print("\nGoodbye!")
    else:
        print("\n✗ Invalid choice")
