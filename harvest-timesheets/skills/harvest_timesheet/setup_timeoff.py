#!/usr/bin/env python3
"""Interactive setup for time-off project configuration."""

import sys
import os
from pathlib import Path
import yaml

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

def main():
    print("\n" + "=" * 70)
    print("  TIME-OFF PROJECT SETUP")
    print("=" * 70)

    print("\nThis wizard will help you configure time-off/vacation tracking.")
    print("\nWhen you mark a day off, a time entry will be created in your")
    print("time-off project with the reason you provide (e.g., 'Vacation').")

    try:
        # Load existing project config
        config_path = Path('.project.yaml')
        if not config_path.exists():
            print("\n✗ Error: .project.yaml not found")
            print("  Run project setup first: python3 run.py setup")
            return

        config = load_project_config()

        # Get credentials and client
        access_token, account_id = get_harvest_credentials()
        client = HarvestClient(access_token, account_id)

        # List time-off projects
        print("\n" + "-" * 70)
        print("Searching for time-off projects...")
        print("-" * 70)

        projects = client.get_projects()
        time_off_keywords = ['time off', 'time-off', 'timeoff', 'pto', 'vacation', 'holiday', 'leave', 'talent-time off', 'talent time off']
        time_off_projects = []

        for project in projects:
            if project['is_active']:
                name_lower = project['name'].lower()
                if any(keyword in name_lower for keyword in time_off_keywords):
                    time_off_projects.append(project)

        if time_off_projects:
            print("\n📅 Found these time-off related projects:\n")
            for i, project in enumerate(time_off_projects, 1):
                print(f"  {i}. {project['name']} (ID: {project['id']})")

            print(f"\n  {len(time_off_projects) + 1}. Enter project ID manually")
            print(f"  {len(time_off_projects) + 2}. Skip time-off setup (disable feature)")

            choice = input(f"\nSelect option (1-{len(time_off_projects) + 2}): ").strip()

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(time_off_projects):
                    selected_project = time_off_projects[choice_num - 1]
                    project_id = str(selected_project['id'])
                    project_name = selected_project['name']
                elif choice_num == len(time_off_projects) + 1:
                    project_id = input("\nEnter time-off project ID: ").strip()
                    project_name = "Custom"
                else:
                    print("\n✓ Time-off setup skipped")
                    return
            except (ValueError, IndexError):
                print("\n✗ Invalid choice")
                return
        else:
            print("\n⚠ No time-off projects found automatically")
            print("\nYou can:")
            print("  1. Enter project ID manually")
            print("  2. Skip setup")

            choice = input("\nChoice (1-2): ").strip()
            if choice == "1":
                project_id = input("Enter time-off project ID: ").strip()
                project_name = "Custom"
            else:
                print("\n✓ Time-off setup skipped")
                return

        # Get tasks for selected project
        print(f"\nFetching tasks for project: {project_name}...")
        task_assignments = client.get_project_tasks(project_id)
        active_tasks = [a for a in task_assignments if a['is_active']]

        if not active_tasks:
            print("\n✗ No active tasks found for this project")
            return

        print("\nAvailable tasks:\n")
        for i, assignment in enumerate(active_tasks, 1):
            task = assignment['task']
            print(f"  {i}. {task['name']} (ID: {task['id']})")

        if len(active_tasks) == 1:
            task_id = str(active_tasks[0]['task']['id'])
            print(f"\n✓ Using only available task: {active_tasks[0]['task']['name']}")
        else:
            task_choice = input(f"\nSelect task (1-{len(active_tasks)}): ").strip()
            try:
                task_num = int(task_choice)
                if 1 <= task_num <= len(active_tasks):
                    task_id = str(active_tasks[task_num - 1]['task']['id'])
                else:
                    print("\n✗ Invalid task selection")
                    return
            except ValueError:
                print("\n✗ Invalid input")
                return

        # Get default reason
        print("\nDefault reason for auto-run mode:")
        print("  (Used when run_auto.py automatically creates time-off entries)")
        default_reason = input("Default reason [Time off]: ").strip() or "Time off"

        # Update config
        config['harvest']['time_off'] = {
            'project_id': project_id,
            'task_id': task_id,
            'default_reason': default_reason
        }

        # Save config
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print("\n" + "=" * 70)
        print("✓ Time-off configuration saved!")
        print("=" * 70)
        print(f"\n  Project ID: {project_id}")
        print(f"  Task ID: {task_id}")
        print(f"  Default reason: {default_reason}")
        print("\nFrom now on, when you mark a day off:")
        print("  - You'll be prompted for a reason")
        print("  - A time entry will be created in your time-off project")
        print("  - Your timesheet will show full hours (no gaps)")
        print("\nTo disable: Remove 'time_off' section from .project.yaml\n")

    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
