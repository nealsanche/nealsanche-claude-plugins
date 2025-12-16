"""
Main entry point for Harvest timesheet automation workflows.

Provides three main workflows:
1. Project setup - Configure .project.yaml
2. Authentication setup - Configure Harvest API credentials
3. Timesheet submission - Analyze commits and submit entries
"""

from typing import Optional
from .config import (
    create_project_config,
    load_project_config,
    setup_harvest_auth,
    get_harvest_credentials,
    ConfigurationError
)
from .git_analyzer import (
    get_current_week_dates,
    detect_repository,
    GitAnalysisError
)
from .harvest_api import HarvestClient, HarvestAPIError, test_authentication
from .timesheet_generator import (
    generate_weekly_entries,
    preview_entries,
    submit_entries,
    confirm_submission,
    get_date_range_summary
)


def workflow_project_setup() -> None:
    """
    Interactive workflow for setting up project configuration.

    Creates .project.yaml with Harvest project details.
    """
    try:
        print("\n" + "=" * 60)
        print("  HARVEST PROJECT SETUP")
        print("=" * 60 + "\n")

        config = create_project_config()

        print("\n✓ Project setup complete!")
        print(f"  Project ID: {config['harvest']['project_id']}")
        print(f"  Task ID: {config['harvest']['task_id']}")
        print(f"  Hours per day: {config['harvest']['hours_per_day']}")

    except ConfigurationError as e:
        print(f"\n✗ Setup failed: {e}")
        return
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled by user")
        return
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return


def workflow_setup_auth() -> None:
    """
    Interactive workflow for setting up Harvest API authentication.

    Prompts for access token and account ID, tests authentication,
    and stores credentials.
    """
    try:
        print("\n" + "=" * 60)
        print("  HARVEST AUTHENTICATION SETUP")
        print("=" * 60 + "\n")

        access_token, account_id = setup_harvest_auth()

        # Test the credentials
        print("\nTesting authentication...")
        if test_authentication(access_token, account_id):
            print("\n✓ Authentication setup complete!")
        else:
            print("\n✗ Authentication test failed. Please check your credentials.")

    except ConfigurationError as e:
        print(f"\n✗ Setup failed: {e}")
        return
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled by user")
        return
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return


def workflow_submit_timesheet(repo_path: str = ".") -> None:
    """
    Interactive workflow for analyzing commits and submitting timesheet.

    This is the main workflow that:
    1. Loads project configuration
    2. Retrieves Harvest credentials
    3. Analyzes git commits for the week
    4. Prompts for days off
    5. Generates time entries
    6. Shows preview
    7. Submits to Harvest

    Args:
        repo_path: Path to git repository (default: current directory)
    """
    try:
        print("\n" + "=" * 60)
        print("  HARVEST TIMESHEET SUBMISSION")
        print("=" * 60 + "\n")

        # Check if in git repository
        repo_root = detect_repository()
        if not repo_root:
            print("⚠ Warning: Not in a git repository")
            print("  Timesheet entries will use default notes only\n")
            use_git = False
        else:
            print(f"📂 Repository: {repo_root}\n")
            use_git = True

        # Load project configuration
        print("Loading project configuration...")
        try:
            config = load_project_config()
            print("✓ Configuration loaded\n")
        except ConfigurationError as e:
            print(f"\n✗ Configuration error: {e}")
            print("\nRun the project setup workflow first:")
            print("  workflow_project_setup()")
            return

        # Get Harvest credentials
        print("Loading Harvest credentials...")
        try:
            access_token, account_id = get_harvest_credentials()
            print("✓ Credentials loaded\n")
        except ConfigurationError as e:
            print(f"\n✗ Credentials error: {e}")
            print("\nRun the authentication setup workflow first:")
            print("  workflow_setup_auth()")
            return

        # Create Harvest client
        client = HarvestClient(access_token, account_id)

        # Verify authentication
        print("Verifying Harvest authentication...")
        try:
            user = client.get_current_user()
            print(f"✓ Authenticated as: {user['first_name']} {user['last_name']}\n")
        except HarvestAPIError as e:
            print(f"\n✗ Authentication failed: {e}")
            print("\nPlease check your credentials or re-run authentication setup.")
            return

        # Get current week dates
        week_dates = get_current_week_dates()
        print("=" * 60)
        print(f"Week: {week_dates[0].strftime('%B %d')} - {week_dates[-1].strftime('%B %d, %Y')}")
        print("=" * 60)

        # Ask about days off
        from .timesheet_generator import prompt_for_days_off
        time_off_config = harvest_config.get('time_off')
        time_off_configured = time_off_config is not None and 'project_id' in time_off_config
        days_off = prompt_for_days_off(week_dates, time_off_configured=time_off_configured)

        # Generate entries
        print("\n" + "=" * 60)
        print("Generating timesheet entries...")
        print("=" * 60)

        harvest_config = config['harvest']

        # Get future day notes if configured
        future_day_notes = harvest_config.get('future_day_notes')

        # Extract time-off project/task IDs if configured
        time_off_project_id = time_off_config.get('project_id') if time_off_config else None
        time_off_task_id = time_off_config.get('task_id') if time_off_config else None

        if use_git:
            try:
                entries = generate_weekly_entries(
                    week_dates=week_dates,
                    project_id=harvest_config['project_id'],
                    task_id=harvest_config['task_id'],
                    hours_per_day=harvest_config['hours_per_day'],
                    default_notes=harvest_config['default_notes'],
                    days_off=days_off,
                    repo_path=repo_path,
                    future_day_notes=future_day_notes,
                    time_off_project_id=time_off_project_id,
                    time_off_task_id=time_off_task_id
                )
            except GitAnalysisError as e:
                print(f"⚠ Warning: Git analysis failed: {e}")
                print("  Creating entries with default notes only")
                use_git = False

        if not use_git:
            # Create entries with default notes
            from .timesheet_generator import TimesheetEntry
            entries = []
            for day_date in week_dates:
                if day_date in days_off:
                    # Create time-off entry if configured
                    if time_off_project_id and time_off_task_id:
                        entry = TimesheetEntry(
                            project_id=time_off_project_id,
                            task_id=time_off_task_id,
                            spent_date=day_date,
                            hours=harvest_config['hours_per_day'],
                            notes=days_off[day_date]
                        )
                        entries.append(entry)
                else:
                    # Regular work entry
                    entry = TimesheetEntry(
                        project_id=harvest_config['project_id'],
                        task_id=harvest_config['task_id'],
                        spent_date=day_date,
                        hours=harvest_config['hours_per_day'],
                        notes=harvest_config['default_notes']
                    )
                    entries.append(entry)

        # Preview entries
        preview_entries(entries)

        if not entries:
            print("\n✓ No entries to submit (all days marked off)")
            return

        # Confirm submission
        if not confirm_submission():
            print("\n✗ Submission cancelled by user")
            return

        # Submit to Harvest
        results = submit_entries(entries, client)

        # Display results
        print("\n" + "=" * 60)
        print("  SUBMISSION RESULTS")
        print("=" * 60)

        if results['success']:
            print("\n✓ Timesheet submitted successfully!")
            print(f"  Created: {results['created']} entries")
            print(f"  Updated: {results['updated']} entries")

            total_hours = sum(e.hours for e in entries)
            date_range = get_date_range_summary(entries)
            print(f"  Total hours: {total_hours}")
            print(f"  Date range: {date_range}")

        else:
            print("\n⚠ Submission completed with errors:")
            print(f"  Created: {results['created']} entries")
            print(f"  Updated: {results['updated']} entries")
            print(f"  Failed: {results['failed']} entries")

            if results['errors']:
                print("\nErrors:")
                for error in results['errors']:
                    print(f"  - {error}")

        print("\n" + "=" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n\n✗ Submission cancelled by user")
        return
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return


def main():
    """
    Main entry point with interactive menu.
    """
    print("\n" + "=" * 60)
    print("  HARVEST TIMESHEET AUTOMATION")
    print("=" * 60)
    print("\nWhat would you like to do?\n")
    print("1. Submit timesheet for current week")
    print("2. Setup project configuration (.project.yaml)")
    print("3. Setup Harvest authentication")
    print("4. Exit")

    choice = input("\nChoice (1-4): ").strip()

    if choice == "1":
        workflow_submit_timesheet()
    elif choice == "2":
        workflow_project_setup()
    elif choice == "3":
        workflow_setup_auth()
    elif choice == "4":
        print("\nGoodbye!")
    else:
        print("\n✗ Invalid choice")


if __name__ == "__main__":
    main()
