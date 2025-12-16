"""
Non-interactive Harvest timesheet operations for LLM orchestration.

This module provides pure functions that return data without prompting,
allowing an LLM to orchestrate the workflow with AskUserQuestion.
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .config import load_project_config, get_harvest_credentials, ConfigurationError
from .harvest_api import HarvestClient, HarvestAPIError
from .git_analyzer import (
    detect_repository,
    get_current_week_dates,
    get_commits_by_day,
    summarize_commits_for_day,
    get_commit_statistics
)
from .timesheet_generator import TimesheetEntry


@dataclass
class WeekAnalysis:
    """Analysis of the current week's work."""
    week_dates: List[date]
    repo_path: Optional[str]
    commits_by_day: Dict[date, List]
    stats: Dict[str, int]
    has_git: bool


@dataclass
class TimesheetConfig:
    """Timesheet configuration."""
    project_id: str
    task_id: str
    hours_per_day: float
    default_notes: str
    future_day_notes: Optional[str]
    time_off_project_id: Optional[str]
    time_off_task_id: Optional[str]
    time_off_default_reason: Optional[str]


@dataclass
class SubmissionResult:
    """Result of timesheet submission."""
    success: bool
    created: int
    updated: int
    failed: int
    errors: List[str]
    total_hours: float
    date_range: str


def load_configuration() -> Tuple[TimesheetConfig, HarvestClient]:
    """
    Load configuration and create Harvest client.

    Returns:
        Tuple of (TimesheetConfig, HarvestClient)

    Raises:
        ConfigurationError: If config invalid or credentials missing
    """
    # Load project config
    config = load_project_config()
    harvest = config['harvest']

    # Extract time-off config if present
    time_off = harvest.get('time_off')

    timesheet_config = TimesheetConfig(
        project_id=harvest['project_id'],
        task_id=harvest['task_id'],
        hours_per_day=harvest.get('hours_per_day', 8.0),
        default_notes=harvest['default_notes'],
        future_day_notes=harvest.get('future_day_notes'),
        time_off_project_id=time_off.get('project_id') if time_off else None,
        time_off_task_id=time_off.get('task_id') if time_off else None,
        time_off_default_reason=time_off.get('default_reason', 'Time off') if time_off else None
    )

    # Get credentials and create client
    access_token, account_id = get_harvest_credentials()
    client = HarvestClient(access_token, account_id)

    # Verify authentication
    try:
        user = client.get_current_user()
    except HarvestAPIError as e:
        raise ConfigurationError(f"Harvest authentication failed: {e}")

    return timesheet_config, client


def analyze_week(repo_path: str = ".") -> WeekAnalysis:
    """
    Analyze the current week's commits and dates.

    Args:
        repo_path: Path to git repository

    Returns:
        WeekAnalysis with commit data and statistics
    """
    week_dates = get_current_week_dates()

    # Check if in git repository
    repo_root = detect_repository()
    has_git = repo_root is not None

    if has_git:
        try:
            commits_by_day = get_commits_by_day(week_dates, repo_path)
            stats = get_commit_statistics(commits_by_day)
        except Exception:
            has_git = False
            commits_by_day = {}
            stats = {'total_commits': 0, 'days_with_commits': 0, 'days_without_commits': 5}
    else:
        commits_by_day = {}
        stats = {'total_commits': 0, 'days_with_commits': 0, 'days_without_commits': 5}

    return WeekAnalysis(
        week_dates=week_dates,
        repo_path=repo_root,
        commits_by_day=commits_by_day,
        stats=stats,
        has_git=has_git
    )


def generate_entries(
    analysis: WeekAnalysis,
    config: TimesheetConfig,
    days_off: Dict[date, str]
) -> List[TimesheetEntry]:
    """
    Generate timesheet entries for the week.

    Args:
        analysis: Week analysis with commits
        config: Timesheet configuration
        days_off: Dict mapping dates to reasons for days off

    Returns:
        List of TimesheetEntry objects ready to submit
    """
    today = datetime.now().date()
    entries = []

    for day_date in analysis.week_dates:
        # Handle days off
        if day_date in days_off:
            if config.time_off_project_id and config.time_off_task_id:
                entry = TimesheetEntry(
                    project_id=config.time_off_project_id,
                    task_id=config.time_off_task_id,
                    spent_date=day_date,
                    hours=config.hours_per_day,
                    notes=days_off[day_date]
                )
                entries.append(entry)
            continue

        # Get commits for this day
        commits = analysis.commits_by_day.get(day_date, [])

        # Determine notes
        if day_date > today:
            # Future day
            notes = config.future_day_notes if config.future_day_notes else config.default_notes
        elif commits:
            # Past/present day with commits
            notes = summarize_commits_for_day(commits)
        else:
            # Past/present day without commits
            notes = config.default_notes

        entry = TimesheetEntry(
            project_id=config.project_id,
            task_id=config.task_id,
            spent_date=day_date,
            hours=config.hours_per_day,
            notes=notes
        )
        entries.append(entry)

    return entries


def submit_entries(entries: List[TimesheetEntry], client: HarvestClient) -> SubmissionResult:
    """
    Submit timesheet entries to Harvest.

    Args:
        entries: List of entries to submit
        client: Authenticated Harvest client

    Returns:
        SubmissionResult with submission statistics
    """
    from .timesheet_generator import submit_entries as _submit

    results = _submit(entries, client)

    total_hours = sum(e.hours for e in entries)

    # Get date range
    if entries:
        dates = sorted([e.spent_date for e in entries])
        start = dates[0].strftime('%b %d')
        end = dates[-1].strftime('%b %d, %Y')
        date_range = f"{start}-{end}"
    else:
        date_range = "N/A"

    return SubmissionResult(
        success=results['success'],
        created=results['created'],
        updated=results['updated'],
        failed=results['failed'],
        errors=results.get('errors', []),
        total_hours=total_hours,
        date_range=date_range
    )


def format_entry_preview(entry: TimesheetEntry) -> str:
    """
    Format a single entry for preview.

    Args:
        entry: TimesheetEntry to format

    Returns:
        Formatted string for display
    """
    day_name = entry.spent_date.strftime('%A')
    date_str = entry.spent_date.strftime('%Y-%m-%d')
    notes_preview = entry.notes[:80] + '...' if len(entry.notes) > 80 else entry.notes

    return f"{day_name} {date_str}: {entry.hours}h - {notes_preview}"


def format_entries_preview(entries: List[TimesheetEntry]) -> str:
    """
    Format all entries for preview display.

    Args:
        entries: List of entries to preview

    Returns:
        Formatted multi-line string
    """
    if not entries:
        return "No entries to submit"

    lines = ["Timesheet Preview:", ""]

    for i, entry in enumerate(entries, 1):
        lines.append(f"{i}. {format_entry_preview(entry)}")

    total_hours = sum(e.hours for e in entries)
    lines.append("")
    lines.append(f"Total: {total_hours} hours")

    return "\n".join(lines)
