"""
Harvest Timesheet Automation

A Claude Code skill for automating weekly timesheet submissions to Harvest
by analyzing git commits and generating time entries.
"""

__version__ = "1.0.0"

from .main import (
    workflow_project_setup,
    workflow_submit_timesheet,
    workflow_setup_auth,
)

__all__ = [
    "workflow_project_setup",
    "workflow_submit_timesheet",
    "workflow_setup_auth",
]
