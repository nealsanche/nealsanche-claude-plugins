#!/usr/bin/env python3
"""
Demo script for Harvest timesheet automation skill.
Tests the core functionality without requiring actual Harvest credentials.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from harvest_timesheet.git_analyzer import (
    get_current_week_dates,
    get_week_dates_for_date,
    detect_repository
)
from harvest_timesheet.timesheet_generator import TimesheetEntry


def demo_week_dates():
    """Demo: Show current week dates."""
    print("\n" + "=" * 60)
    print("  DEMO: Current Week Dates")
    print("=" * 60 + "\n")

    week_dates = get_current_week_dates()

    print("Current week (Monday-Friday):")
    for i, d in enumerate(week_dates, 1):
        day_name = d.strftime("%A")
        date_str = d.strftime("%Y-%m-%d")
        print(f"  {i}. {day_name:9s} {date_str}")

    print(f"\nWeek spans: {week_dates[0]} to {week_dates[-1]}")


def demo_git_detection():
    """Demo: Detect git repository."""
    print("\n" + "=" * 60)
    print("  DEMO: Git Repository Detection")
    print("=" * 60 + "\n")

    repo_path = detect_repository()

    if repo_path:
        print(f"✓ Git repository detected!")
        print(f"  Path: {repo_path}")
    else:
        print("✗ Not in a git repository")
        print("  (This is OK - skill will work with default notes)")


def demo_git_commits():
    """Demo: Analyze git commits for current week."""
    print("\n" + "=" * 60)
    print("  DEMO: Git Commit Analysis")
    print("=" * 60 + "\n")

    repo_path = detect_repository()

    if not repo_path:
        print("⚠ Not in a git repository - skipping commit analysis")
        return

    try:
        from harvest_timesheet.git_analyzer import (
            get_commits_by_day,
            format_commits_for_display,
            get_commit_statistics,
            summarize_commits_for_day
        )

        week_dates = get_current_week_dates()
        commits_by_day = get_commits_by_day(week_dates)
        stats = get_commit_statistics(commits_by_day)

        print(f"Commit Statistics:")
        print(f"  Total commits: {stats['total_commits']}")
        print(f"  Days with commits: {stats['days_with_commits']}")
        print(f"  Days without commits: {stats['days_without_commits']}")

        if stats['total_commits'] > 0:
            print("\nCommits by day:")
            print(format_commits_for_display(commits_by_day))

            print("\n" + "-" * 60)
            print("Timesheet-ready summaries:")
            print("-" * 60)

            for day_date in week_dates:
                commits = commits_by_day.get(day_date, [])
                if commits:
                    summary = summarize_commits_for_day(commits)
                    day_name = day_date.strftime("%A")
                    print(f"\n{day_name} ({day_date}):")
                    print(f"  {summary}")
        else:
            print("\n⚠ No commits found for current week")

    except Exception as e:
        print(f"✗ Error analyzing commits: {e}")


def demo_timesheet_entries():
    """Demo: Generate sample timesheet entries."""
    print("\n" + "=" * 60)
    print("  DEMO: Timesheet Entry Generation")
    print("=" * 60 + "\n")

    week_dates = get_current_week_dates()

    # Create sample entries
    entries = []

    sample_notes = [
        "Implemented user authentication flow; Fixed login validation bugs",
        "Added password reset functionality; Refactored auth middleware",
        "Updated API endpoints; Added rate limiting; Fixed CORS issues",
        "Code review and testing; Updated documentation",
        "Bug fixes and performance improvements"
    ]

    for i, day_date in enumerate(week_dates):
        entry = TimesheetEntry(
            project_id="12345678",
            task_id="98765432",
            spent_date=day_date,
            hours=8.0,
            notes=sample_notes[i]
        )
        entries.append(entry)

    print("Sample timesheet entries (5-day week):\n")

    total_hours = 0
    for i, entry in enumerate(entries, 1):
        day_name = entry.spent_date.strftime("%A")
        date_str = entry.spent_date.strftime("%Y-%m-%d")

        print(f"{i}. {day_name} {date_str} - {entry.hours} hours")
        print(f"   {entry.notes}")
        print()

        total_hours += entry.hours

    print(f"Total hours: {total_hours}")


def demo_configuration():
    """Demo: Show sample configuration files."""
    print("\n" + "=" * 60)
    print("  DEMO: Configuration Files")
    print("=" * 60 + "\n")

    print("Sample .project.yaml:")
    print("-" * 40)
    print("""harvest:
  project_id: "12345678"
  task_id: "98765432"
  default_notes: "Development work on authentication module"
  hours_per_day: 8.0""")

    print("\n\nSample .env file:")
    print("-" * 40)
    print("""HARVEST_ACCESS_TOKEN=your_token_here
HARVEST_ACCOUNT_ID=your_account_id_here""")

    print("\n\n💡 Tip: Get your Harvest credentials at:")
    print("   https://id.getharvest.com/developers")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  HARVEST TIMESHEET AUTOMATION - DEMO")
    print("=" * 60)

    demos = [
        ("Week Dates", demo_week_dates),
        ("Git Detection", demo_git_detection),
        ("Git Commits", demo_git_commits),
        ("Timesheet Entries", demo_timesheet_entries),
        ("Configuration", demo_configuration),
    ]

    print("\nAvailable demos:\n")
    for i, (name, _) in enumerate(demos, 1):
        print(f"{i}. {name}")
    print(f"{len(demos) + 1}. Run all demos")
    print(f"{len(demos) + 2}. Exit")

    choice = input("\nChoice: ").strip()

    try:
        choice_num = int(choice)

        if 1 <= choice_num <= len(demos):
            demos[choice_num - 1][1]()
        elif choice_num == len(demos) + 1:
            for name, func in demos:
                func()
                input("\nPress Enter to continue...")
        elif choice_num == len(demos) + 2:
            print("\nGoodbye!")
        else:
            print("\n✗ Invalid choice")

    except ValueError:
        print("\n✗ Invalid input")


if __name__ == "__main__":
    main()
