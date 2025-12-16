"""
Git commit analysis for timesheet generation.

Extracts and summarizes git commits for the current week,
grouping them by day and creating human-readable summaries.
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from pathlib import Path
import re

try:
    from git import Repo, Commit
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


class GitAnalysisError(Exception):
    """Raised when git analysis fails."""
    pass


def check_git_available():
    """Check if GitPython is available."""
    if not GIT_AVAILABLE:
        raise GitAnalysisError(
            "GitPython not installed. Install with: pip install gitpython"
        )


def get_current_week_dates() -> List[date]:
    """
    Get Monday through Friday dates for the current week.

    Returns:
        List of date objects representing Mon-Fri of current week
    """
    today = datetime.now().date()

    # Find Monday of current week (weekday() returns 0 for Monday)
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)

    # Generate Monday through Friday
    week_dates = [monday + timedelta(days=i) for i in range(5)]

    return week_dates


def get_week_dates_for_date(target_date: date) -> List[date]:
    """
    Get Monday through Friday dates for the week containing target_date.

    Args:
        target_date: Date to find the week for

    Returns:
        List of date objects representing Mon-Fri of that week
    """
    days_since_monday = target_date.weekday()
    monday = target_date - timedelta(days=days_since_monday)

    week_dates = [monday + timedelta(days=i) for i in range(5)]

    return week_dates


def get_git_repo(path: str = ".") -> Repo:
    """
    Get git repository object for the given path.

    Args:
        path: Path to git repository (default: current directory)

    Returns:
        Git Repo object

    Raises:
        GitAnalysisError: If not a git repository
    """
    check_git_available()

    try:
        repo = Repo(path, search_parent_directories=True)
        return repo
    except Exception as e:
        raise GitAnalysisError(
            f"Not a git repository or git not available: {e}"
        )


def get_commits_by_day(week_dates: List[date], repo_path: str = ".") -> Dict[date, List[Commit]]:
    """
    Extract git commits grouped by day for the given week.

    Args:
        week_dates: List of dates to extract commits for
        repo_path: Path to git repository

    Returns:
        Dictionary mapping date to list of commits for that day
    """
    check_git_available()
    repo = get_git_repo(repo_path)

    commits_by_day = {d: [] for d in week_dates}

    # Get all commits from the start of the week to now
    start_date = week_dates[0]
    end_date = week_dates[-1] + timedelta(days=1)  # Include full Friday

    # Convert to datetime for comparison
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.min.time())

    try:
        # Get commits in date range
        commits = list(repo.iter_commits(
            all=True,
            since=start_datetime,
            until=end_datetime
        ))

        # Group by date
        for commit in commits:
            commit_date = datetime.fromtimestamp(commit.committed_date).date()

            if commit_date in commits_by_day:
                commits_by_day[commit_date].append(commit)

    except Exception as e:
        print(f"⚠ Warning: Error reading git commits: {e}")

    return commits_by_day


def clean_commit_message(message: str) -> str:
    """
    Clean and normalize a commit message.

    Args:
        message: Raw commit message

    Returns:
        Cleaned commit message (first line only, trimmed)
    """
    # Take first line only
    first_line = message.split("\n")[0].strip()

    # Remove common prefixes
    prefixes = [
        r"^WIP:?\s*",
        r"^Merge\s+.*",
        r"^\[skip\s+ci\]\s*",
        r"^\[ci\s+skip\]\s*",
    ]

    for prefix in prefixes:
        first_line = re.sub(prefix, "", first_line, flags=re.IGNORECASE)

    return first_line.strip()


def summarize_commits_for_day(commits: List[Commit], max_length: int = 200) -> str:
    """
    Create a concise summary of commits for a single day.

    Args:
        commits: List of commits for the day
        max_length: Maximum length of summary

    Returns:
        Human-readable summary string suitable for timesheet
    """
    if not commits:
        return ""

    # Clean and deduplicate messages
    messages = []
    seen = set()

    for commit in commits:
        cleaned = clean_commit_message(commit.message)

        if cleaned and cleaned not in seen:
            # Skip merge commits and version bumps
            if not any(skip in cleaned.lower() for skip in ["merge", "bump version", "update version"]):
                messages.append(cleaned)
                seen.add(cleaned)

    if not messages:
        return "Code updates and maintenance"

    # If few commits, join them
    if len(messages) <= 3:
        summary = "; ".join(messages)
        if len(summary) <= max_length:
            return summary

    # For many commits, create a more concise summary
    # Group by common patterns
    features = [m for m in messages if any(word in m.lower() for word in ["add", "implement", "create", "new"])]
    fixes = [m for m in messages if any(word in m.lower() for word in ["fix", "bug", "issue", "resolve"])]
    refactors = [m for m in messages if any(word in m.lower() for word in ["refactor", "clean", "improve", "optimize"])]
    docs = [m for m in messages if any(word in m.lower() for word in ["doc", "readme", "comment"])]
    tests = [m for m in messages if any(word in m.lower() for word in ["test", "spec"])]

    summary_parts = []

    if features:
        if len(features) == 1:
            summary_parts.append(features[0])
        else:
            summary_parts.append(f"Features: {', '.join(features[:2])}")

    if fixes:
        if len(fixes) == 1:
            summary_parts.append(fixes[0])
        else:
            summary_parts.append(f"Fixes: {', '.join(fixes[:2])}")

    if refactors:
        summary_parts.append(f"Refactoring and improvements")

    if tests:
        summary_parts.append("Test updates")

    if docs:
        summary_parts.append("Documentation")

    # If we didn't categorize anything, just take first few messages
    if not summary_parts:
        summary_parts = messages[:3]

    summary = "; ".join(summary_parts)

    # Truncate if still too long
    if len(summary) > max_length:
        summary = summary[:max_length - 3] + "..."

    return summary


def format_commits_for_display(commits_by_day: Dict[date, List[Commit]]) -> str:
    """
    Format commits by day for display to user.

    Args:
        commits_by_day: Dictionary mapping dates to commits

    Returns:
        Formatted string showing commits by day
    """
    output = []

    for day_date in sorted(commits_by_day.keys()):
        commits = commits_by_day[day_date]
        day_name = day_date.strftime("%A")
        date_str = day_date.strftime("%Y-%m-%d")

        output.append(f"\n{day_name} ({date_str}):")

        if commits:
            for commit in commits[:5]:  # Show max 5 commits
                message = clean_commit_message(commit.message)
                if message:
                    output.append(f"  - {message}")

            if len(commits) > 5:
                output.append(f"  ... and {len(commits) - 5} more commits")
        else:
            output.append("  (no commits)")

    return "\n".join(output)


def get_commit_statistics(commits_by_day: Dict[date, List[Commit]]) -> Dict[str, int]:
    """
    Get statistics about commits for the week.

    Args:
        commits_by_day: Dictionary mapping dates to commits

    Returns:
        Dictionary with statistics (total_commits, days_with_commits, etc.)
    """
    total_commits = sum(len(commits) for commits in commits_by_day.values())
    days_with_commits = sum(1 for commits in commits_by_day.values() if commits)

    return {
        "total_commits": total_commits,
        "days_with_commits": days_with_commits,
        "days_without_commits": len(commits_by_day) - days_with_commits,
    }


def detect_repository() -> Optional[Path]:
    """
    Detect if current directory or parent is a git repository.

    Returns:
        Path to repository root, or None if not found
    """
    check_git_available()

    try:
        repo = Repo(".", search_parent_directories=True)
        return Path(repo.working_dir)
    except Exception:
        return None
