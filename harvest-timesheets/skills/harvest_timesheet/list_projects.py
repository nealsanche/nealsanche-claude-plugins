#!/usr/bin/env python3
"""List all Harvest projects with their IDs and task assignments."""

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

def main():
    try:
        # Get credentials
        access_token, account_id = get_harvest_credentials()
        client = HarvestClient(access_token, account_id)

        print("\n" + "=" * 70)
        print("  HARVEST PROJECTS")
        print("=" * 70)

        # Initialize project_tasks dict (will be populated if we use fallback)
        project_tasks = {}

        # Try to get all projects first
        try:
            projects = client.get_projects()
        except Exception as e:
            # Fallback: Get projects from recent time entries
            print("\n⚠ Cannot access full projects list (API permissions)")
            print("  Discovering projects from your time entries instead...\n")

            from datetime import datetime, timedelta

            # Get time entries from last 90 days
            start_date = (datetime.now() - timedelta(days=90)).date()
            end_date = datetime.now().date()

            entries = client.get_time_entries(from_date=start_date, to_date=end_date)

            # Extract unique projects and their tasks from entries
            projects_dict = {}
            project_tasks = {}  # Map project_id -> {task_id: task_info}

            for entry in entries:
                project = entry.get('project')
                task = entry.get('task')

                if project:
                    project_id = project['id']

                    # Store project info
                    if project_id not in projects_dict:
                        projects_dict[project_id] = {
                            'id': project_id,
                            'name': project['name'],
                            'code': project.get('code', ''),
                            'is_active': True,  # Assume active if we have entries
                            'client': entry.get('client', {})
                        }

                    # Store task info for this project
                    if task:
                        task_id = task['id']
                        if project_id not in project_tasks:
                            project_tasks[project_id] = {}
                        if task_id not in project_tasks[project_id]:
                            project_tasks[project_id][task_id] = {
                                'id': task_id,
                                'name': task['name']
                            }

            projects = list(projects_dict.values())

        if not projects:
            print("\n⚠ No projects found")
            return

        # Separate time-off related projects from regular projects
        time_off_keywords = ['time off', 'time-off', 'timeoff', 'pto', 'vacation', 'holiday', 'leave', 'talent-time off', 'talent time off']
        time_off_projects = []
        regular_projects = []

        for project in projects:
            name_lower = project['name'].lower()
            if any(keyword in name_lower for keyword in time_off_keywords):
                time_off_projects.append(project)
            else:
                regular_projects.append(project)

        # Display time-off projects first
        if time_off_projects:
            print("\n📅 TIME-OFF / VACATION PROJECTS:")
            print("-" * 70)
            for project in time_off_projects:
                print(f"\n  Project: {project['name']}")
                print(f"  ID: {project['id']}")
                print(f"  Client: {project.get('client', {}).get('name', 'N/A')}")
                print(f"  Active: {project['is_active']}")

                # Get tasks for this project
                project_id = project['id']
                try:
                    task_assignments = client.get_project_tasks(str(project_id))
                    if task_assignments:
                        print(f"  Tasks:")
                        for assignment in task_assignments:
                            if assignment['is_active']:
                                task = assignment['task']
                                print(f"    - {task['name']} (ID: {task['id']})")
                    else:
                        print(f"  Tasks: (none found)")
                except Exception as e:
                    # Fallback: Use tasks from time entries if available
                    if project_id in project_tasks and project_tasks[project_id]:
                        print(f"  Tasks (from your time entries):")
                        for task_id, task_info in project_tasks[project_id].items():
                            print(f"    - {task_info['name']} (ID: {task_info['id']})")
                    else:
                        print(f"  Tasks: (not found in recent entries)")

        # Display regular projects
        if regular_projects:
            print("\n\n💼 REGULAR PROJECTS:")
            print("-" * 70)
            for project in regular_projects:
                print(f"\n  Project: {project['name']}")
                print(f"  ID: {project['id']}")
                print(f"  Client: {project.get('client', {}).get('name', 'N/A')}")
                print(f"  Active: {project['is_active']}")

                # Get tasks for this project
                project_id = project['id']
                try:
                    task_assignments = client.get_project_tasks(str(project_id))
                    if task_assignments:
                        print(f"  Tasks:")
                        for assignment in task_assignments:
                            if assignment['is_active']:
                                task = assignment['task']
                                print(f"    - {task['name']} (ID: {task['id']})")
                    else:
                        print(f"  Tasks: (none found)")
                except Exception as e:
                    # Fallback: Use tasks from time entries if available
                    if project_id in project_tasks and project_tasks[project_id]:
                        print(f"  Tasks (from your time entries):")
                        for task_id, task_info in project_tasks[project_id].items():
                            print(f"    - {task_info['name']} (ID: {task_info['id']})")
                    else:
                        print(f"  Tasks: (not found in recent entries)")

        print("\n" + "=" * 70)
        print("\n💡 TIP: Use these IDs in your .project.yaml configuration")
        print("   Run setup_timeoff.py to configure time-off project interactively\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
