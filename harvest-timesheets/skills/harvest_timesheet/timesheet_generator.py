"""
Timesheet generation and submission logic.

Combines git commit analysis with Harvest API to create
and submit time entries.
"""

from datetime import date
from typing import Dict, List, Any, Optional
from .git_analyzer import (
    get_current_week_dates,
    get_commits_by_day,
    summarize_commits_for_day,
    format_commits_for_display,
    get_commit_statistics
)
from .harvest_api import HarvestClient, HarvestAPIError


class TimesheetEntry:
    """Represents a single timesheet entry."""

    def __init__(
        self,
        project_id: str,
        task_id: str,
        spent_date: date,
        hours: float,
        notes: str
    ):
        self.project_id = project_id
        self.task_id = task_id
        self.spent_date = spent_date
        self.hours = hours
        self.notes = notes

    def __repr__(self):
        return (
            f"TimesheetEntry(date={self.spent_date}, "
            f"hours={self.hours}, notes={self.notes[:50]}...)"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API submission."""
        return {
            "project_id": self.project_id,
            "task_id": self.task_id,
            "spent_date": self.spent_date,
            "hours": self.hours,
            "notes": self.notes
        }


def prompt_for_days_off(week_dates: List[date], time_off_configured: bool = False) -> Dict[date, str]:
    """
    Interactive prompt asking user about days off.

    Args:
        week_dates: List of dates in the week
        time_off_configured: Whether time-off project is configured

    Returns:
        Dict mapping dates to reasons for days off (empty dict if no days off)
    """
    print("\n=== Days Off ===")
    if time_off_configured:
        print("Were there any days you were on vacation or holiday this week?")
        print("(Time entries will be created in your time-off project)")
    else:
        print("Were there any days you were on vacation or holiday this week?")
        print("(No time entries will be created for these days)")

    # First ask if ANY days off
    response = input("\nAny days off this week? (y/n): ").strip().lower()

    if response not in ['y', 'yes']:
        print("\n✓ No days off this week")
        return {}

    # Show available days
    print("\nDays in this week:")
    day_map = {}  # Map day names to dates
    for i, day_date in enumerate(week_dates, 1):
        day_name = day_date.strftime("%A")
        date_str = day_date.strftime("%Y-%m-%d")
        day_map[day_name.lower()] = day_date
        print(f"  {day_name} ({date_str})")

    # Ask which days
    print("\nExamples: 'Monday', 'Monday Wednesday', 'Friday', 'Mon Wed Fri'")
    days_input = input("Which days were off? ").strip().lower()

    days_off = {}

    # Parse the input
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                 'mon', 'tue', 'wed', 'thu', 'fri']

    # Create shortcuts map
    shortcuts = {
        'mon': 'monday', 'tue': 'tuesday', 'wed': 'wednesday',
        'thu': 'thursday', 'fri': 'friday'
    }

    for token in days_input.split():
        token = token.strip(',').lower()
        # Expand shortcut
        if token in shortcuts:
            token = shortcuts[token]

        if token in day_map:
            day_date = day_map[token]

            if time_off_configured:
                day_display = day_date.strftime("%A")
                reason = input(f"Reason for {day_display} (e.g., Vacation, Sick, Holiday): ").strip()
                if not reason:
                    reason = "Time off"
                days_off[day_date] = reason
            else:
                days_off[day_date] = "Day off"

    if days_off:
        print(f"\n✓ Marked {len(days_off)} day(s) off")
        if time_off_configured:
            print("  Time entries will be created in your time-off project")
    else:
        print("\n⚠ No valid days recognized - working full week")

    return days_off


def generate_weekly_entries(
    week_dates: List[date],
    project_id: str,
    task_id: str,
    hours_per_day: float,
    default_notes: str,
    days_off: Dict[date, str],
    repo_path: str = ".",
    future_day_notes: Optional[str] = None,
    time_off_project_id: Optional[str] = None,
    time_off_task_id: Optional[str] = None
) -> List[TimesheetEntry]:
    """
    Generate timesheet entries for the week based on git commits.

    For future days (days that haven't happened yet), uses special handling:
    - If it's Thursday or earlier and Friday hasn't happened, Friday gets
      special future day notes or copies Thursday's notes

    For days off (when time_off_project_id is configured):
    - Creates time entries in the time-off project with the reason as notes
    - If time_off_project_id is not configured, days off are skipped entirely

    Args:
        week_dates: List of dates in the week
        project_id: Harvest project ID for regular work
        task_id: Harvest task ID for regular work
        hours_per_day: Hours to log per day
        default_notes: Notes to use when no commits found
        days_off: Dict mapping dates to reasons for days off
        repo_path: Path to git repository
        future_day_notes: Notes to use for future days (optional)
        time_off_project_id: Harvest project ID for time off entries (optional)
        time_off_task_id: Harvest task ID for time off entries (optional)

    Returns:
        List of TimesheetEntry objects
    """
    from datetime import datetime

    today = datetime.now().date()

    # Get commits grouped by day
    try:
        commits_by_day = get_commits_by_day(week_dates, repo_path)
        stats = get_commit_statistics(commits_by_day)

        print(f"\n=== Git Commit Analysis ===")
        print(f"Total commits: {stats['total_commits']}")
        print(f"Days with commits: {stats['days_with_commits']}")

        if stats['days_without_commits'] > 0:
            print(f"Days without commits: {stats['days_without_commits']}")
            print(f"  (will use default notes)")

    except Exception as e:
        print(f"⚠ Warning: Could not analyze git commits: {e}")
        print(f"  Using default notes for all entries")
        commits_by_day = {d: [] for d in week_dates}

    # Identify future days
    future_days = [d for d in week_dates if d > today]
    if future_days:
        print(f"\n📅 Future days detected: {len(future_days)} day(s)")
        for fd in future_days:
            print(f"   - {fd.strftime('%A %Y-%m-%d')}")

        if future_day_notes:
            print(f"   Using custom future notes: \"{future_day_notes}\"")
        else:
            print(f"   Using default notes: \"{default_notes}\"")

    # Generate entries
    entries = []

    for i, day_date in enumerate(week_dates):
        # Handle days off
        if day_date in days_off:
            if time_off_project_id and time_off_task_id:
                # Create time-off entry with reason
                entry = TimesheetEntry(
                    project_id=time_off_project_id,
                    task_id=time_off_task_id,
                    spent_date=day_date,
                    hours=hours_per_day,
                    notes=days_off[day_date]
                )
                entries.append(entry)
            # else: skip this day (no time entry created)
            continue

        # Get commits for this day
        commits = commits_by_day.get(day_date, [])

        # Determine notes based on whether this is a future day
        if day_date > today:
            # Future day - use future_day_notes if set, otherwise default_notes
            notes = future_day_notes if future_day_notes else default_notes
        elif commits:
            # Past/present day with commits
            notes = summarize_commits_for_day(commits)
        else:
            # Past/present day without commits
            notes = default_notes

        # Create entry
        entry = TimesheetEntry(
            project_id=project_id,
            task_id=task_id,
            spent_date=day_date,
            hours=hours_per_day,
            notes=notes
        )

        entries.append(entry)

    return entries


def preview_entries(entries: List[TimesheetEntry]) -> None:
    """
    Display timesheet entries for user review.

    Args:
        entries: List of entries to preview
    """
    print("\n=== Timesheet Preview ===\n")

    if not entries:
        print("No entries to submit.")
        return

    total_hours = sum(e.hours for e in entries)

    for i, entry in enumerate(entries, 1):
        day_name = entry.spent_date.strftime("%A")
        date_str = entry.spent_date.strftime("%Y-%m-%d")

        print(f"{i}. {day_name} {date_str} - {entry.hours} hours")
        print(f"   {entry.notes}")
        print()

    print(f"Total hours: {total_hours}")


def check_for_existing_entries(
    entries: List[TimesheetEntry],
    client: HarvestClient
) -> Dict[date, List[Dict[str, Any]]]:
    """
    Check if any entries already exist in Harvest for the given dates/project.

    Args:
        entries: List of entries to check
        client: Harvest API client

    Returns:
        Dictionary mapping dates to existing entries
    """
    existing_by_date = {}

    for entry in entries:
        try:
            existing = client.check_duplicate_entries(
                entry.project_id,
                entry.spent_date
            )

            if existing:
                existing_by_date[entry.spent_date] = existing
        except HarvestAPIError as e:
            print(f"⚠ Warning: Could not check existing entries for {entry.spent_date}: {e}")

    return existing_by_date


def submit_entries(
    entries: List[TimesheetEntry],
    client: HarvestClient,
    update_existing: bool = True
) -> Dict[str, Any]:
    """
    Submit timesheet entries to Harvest.

    If entries already exist for a date/project, they will be updated
    with the new notes (replacing existing notes for idempotent behavior).

    Args:
        entries: List of entries to submit
        client: Harvest API client
        update_existing: Whether to update existing entries (default: True)

    Returns:
        Dictionary with submission results
    """
    if not entries:
        return {
            "success": True,
            "created": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }

    # Check for existing entries
    existing_by_date = check_for_existing_entries(entries, client)

    if existing_by_date:
        print(f"\n📝 Found existing entries for {len(existing_by_date)} date(s)")
        print("   These will be updated (notes replaced)")

    # Submit entries
    print("\n=== Submitting to Harvest ===\n")

    results = {
        "success": True,
        "created": 0,
        "updated": 0,
        "failed": 0,
        "errors": [],
        "entries": []
    }

    for entry in entries:
        try:
            # Check if entry exists for this date
            if entry.spent_date in existing_by_date:
                existing_entries = existing_by_date[entry.spent_date]

                # Find the entry for this project (there should be only one)
                matching_entry = None
                for existing in existing_entries:
                    if str(existing.get('project', {}).get('id')) == entry.project_id:
                        matching_entry = existing
                        break

                if matching_entry and update_existing:
                    # Update existing entry - replace notes to make it idempotent
                    entry_id = matching_entry['id']

                    # Simply replace with new notes (idempotent behavior)
                    result = client.update_time_entry(
                        entry_id=entry_id,
                        hours=entry.hours,
                        notes=entry.notes
                    )

                    results["updated"] += 1
                    results["entries"].append(result)

                    day_name = entry.spent_date.strftime("%A")
                    print(f"✓ {day_name} {entry.spent_date}: Updated ({entry.hours} hours)")
                    continue

            # Create new entry
            result = client.create_time_entry(
                project_id=entry.project_id,
                task_id=entry.task_id,
                spent_date=entry.spent_date,
                hours=entry.hours,
                notes=entry.notes
            )

            results["created"] += 1
            results["entries"].append(result)

            day_name = entry.spent_date.strftime("%A")
            print(f"✓ {day_name} {entry.spent_date}: Created ({entry.hours} hours)")

        except HarvestAPIError as e:
            results["failed"] += 1
            results["success"] = False
            error_msg = f"{entry.spent_date}: {str(e)}"
            results["errors"].append(error_msg)

            print(f"✗ {entry.spent_date}: Failed - {e}")

    return results


def confirm_submission() -> bool:
    """
    Ask user to confirm submission.

    Returns:
        True if user confirms, False otherwise
    """
    print("\n" + "=" * 50)
    response = input("Submit these entries to Harvest? (yes/no): ").strip().lower()

    return response in ['yes', 'y']


def get_date_range_summary(entries: List[TimesheetEntry]) -> str:
    """
    Get human-readable date range for entries.

    Args:
        entries: List of timesheet entries

    Returns:
        String like "Nov 17-21, 2025"
    """
    if not entries:
        return "No entries"

    dates = sorted([e.spent_date for e in entries])
    start = dates[0]
    end = dates[-1]

    if start.month == end.month:
        return f"{start.strftime('%b %d')}-{end.strftime('%d, %Y')}"
    else:
        return f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
