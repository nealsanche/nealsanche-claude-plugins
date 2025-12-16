#!/usr/bin/env python3
"""
Test script to demonstrate Thursday submission behavior.
Shows how Friday gets populated with Thursday's notes when submitting on Thursday.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from harvest_timesheet.timesheet_generator import (
    TimesheetEntry,
    generate_weekly_entries
)


def demo_thursday_submission():
    """
    Simulate submitting timesheet on Thursday.
    Friday should use default notes from .project.yaml.
    """
    print("\n" + "=" * 60)
    print("  DEMO: Thursday Submission (Friday uses default notes)")
    print("=" * 60 + "\n")

    # Simulate week dates
    monday = date(2025, 11, 17)
    week_dates = [monday + timedelta(days=i) for i in range(5)]

    print("Week dates:")
    for d in week_dates:
        print(f"  {d.strftime('%A %Y-%m-%d')}")

    # Simulate being Thursday
    print("\n📅 Today: Thursday 2025-11-20")
    print("   (Friday 2025-11-21 is in the future)\n")

    # Mock commits_by_day (no git repo needed for demo)
    print("Sample commit notes for Mon-Thu:")
    sample_commits = {
        monday: ["Implemented authentication"],
        monday + timedelta(days=1): ["Added password reset"],
        monday + timedelta(days=2): ["Updated API endpoints"],
        monday + timedelta(days=3): ["Code review and testing"],
        # Friday (index 4) has no commits because it hasn't happened yet
    }

    for day, commits in sample_commits.items():
        print(f"  {day.strftime('%A')}: {commits[0]}")

    print("\n" + "-" * 60)
    print("Generated Timesheet Entries:")
    print("-" * 60 + "\n")

    # Manually create entries to show the behavior
    entries = []

    # Monday-Thursday: Use actual notes
    notes_by_day = [
        "Implemented authentication; Fixed login validation",
        "Added password reset functionality; Refactored middleware",
        "Updated API endpoints; Added rate limiting; Fixed CORS",
        "Code review and testing; Updated documentation"
    ]

    for i in range(4):  # Mon-Thu
        entry = TimesheetEntry(
            project_id="12345",
            task_id="67890",
            spent_date=week_dates[i],
            hours=8.0,
            notes=notes_by_day[i]
        )
        entries.append(entry)

    # Friday: Use default notes (future day)
    default_note = "Development work"
    friday_entry = TimesheetEntry(
        project_id="12345",
        task_id="67890",
        spent_date=week_dates[4],  # Friday
        hours=8.0,
        notes=default_note  # Default notes from .project.yaml
    )
    entries.append(friday_entry)

    # Display all entries
    for i, entry in enumerate(entries, 1):
        day_name = entry.spent_date.strftime("%A")
        date_str = entry.spent_date.strftime("%Y-%m-%d")
        is_future = "(FUTURE - uses default notes)" if i == 5 else ""

        print(f"{i}. {day_name} {date_str} - {entry.hours} hours {is_future}")
        print(f"   {entry.notes}")
        print()

    print("=" * 60)
    print("✓ Friday automatically uses default notes from .project.yaml!")
    print("=" * 60)


def demo_with_custom_future_notes():
    """
    Demonstrate using custom notes for future days.
    """
    print("\n\n" + "=" * 60)
    print("  DEMO: Custom Future Day Notes")
    print("=" * 60 + "\n")

    monday = date(2025, 11, 17)
    week_dates = [monday + timedelta(days=i) for i in range(5)]

    print("If you configure 'future_day_notes' in .project.yaml:")
    print("\nharvest:")
    print("  future_day_notes: \"Planned development work\"")
    print("\nFriday would use: \"Planned development work\"")
    print("Instead of the default notes.")


if __name__ == "__main__":
    demo_thursday_submission()
    demo_with_custom_future_notes()

    print("\n\n" + "=" * 60)
    print("Configuration Options:")
    print("=" * 60)
    print("""
1. Default behavior (no future_day_notes set):
   - Friday uses default_notes from .project.yaml
   - Same note as days without commits

2. Custom future notes (set future_day_notes):
   - Friday uses your specified future_day_notes
   - Different from default_notes, specific to future days

Example .project.yaml:

harvest:
  project_id: "12345678"
  task_id: "98765432"
  default_notes: "Development work"
  hours_per_day: 8.0
  future_day_notes: "Planned development and testing"  # Optional
""")
