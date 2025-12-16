# Harvest Timesheet Automation Skill

<skill_overview>
Automates weekly Harvest timesheet submissions by analyzing git commits and generating time entries with meaningful descriptions. Handles authentication, project configuration, and idempotent timesheet updates.
</skill_overview>

<skill_invocation>
This skill is invoked when users need to:
- Submit weekly timesheets to Harvest
- Update timesheet entries with git commit summaries
- Configure Harvest API credentials
- Set up project-specific timesheet settings
</skill_invocation>

## Prerequisites

<prerequisites>
**Required:**
- Python 3.7+ with virtual environment activated
- Harvest account with API access
- Git repository (optional - will use default notes if not available)

**API Credentials:**
- Harvest Personal Access Token
- Harvest Account ID
- Get these from: https://id.getharvest.com/developers

**Project Configuration:**
- `.project.yaml` file with Harvest project/task IDs
- Or run project setup workflow to create it
</prerequisites>

## Skill Workflows

<workflow name="submit_timesheet" primary="true">
<purpose>
Main workflow for submitting weekly timesheets. Analyzes git commits for Monday-Friday, generates meaningful time entry descriptions, and submits to Harvest with idempotent updates.
</purpose>

<when_to_use>
- Every Thursday (or end of week) to submit timesheets
- After making commits you want to include in timesheet
- To update existing entries with new commit information
</when_to_use>

<steps>
1. **Detect Repository**: Check if current directory is a git repository
2. **Load Configuration**: Read `.project.yaml` for project/task IDs
3. **Authenticate**: Verify Harvest API credentials from `~/.harvest/credentials` or environment
4. **Analyze Commits**: Extract commits for current week (Monday-Friday)
5. **Prompt Days Off**: Ask which days were vacation/holidays
6. **Generate Entries**: Create time entries with commit summaries
7. **Preview**: Show what will be submitted
8. **Submit**: Update/create entries in Harvest (idempotent)
9. **Report Results**: Display created/updated entry counts
</steps>

<execution>
This workflow is executed through the `/timesheets` slash command, which:
- Activates the skill's virtual environment automatically
- Uses Bash to execute Python scripts with proper module imports
- Orchestrates the workflow through LLM-guided conversation
- Uses AskUserQuestion for interactive prompts
- Handles prerequisite checking (verifies .project.yaml exists)
- Provides setup instructions if configuration is missing

The slash command uses Bash tool to run Python with proper paths and venv activation.
</execution>

<key_behaviors>
**Idempotent Updates:**
- Running multiple times replaces notes (doesn't append/duplicate)
- Safe to re-run after new commits

**Commit Analysis:**
- Groups commits by day (Monday-Friday)
- Categorizes as Features/Fixes/Refactoring/etc.
- Generates concise summaries suitable for timesheets
- Truncates long descriptions

**Smart Time-Off Handling:**
- **Always prompts** for vacation/holiday days (regardless of git activity)
- If time-off project configured: Creates time entries in time-off project with your reason
- If time-off not configured: Skips those days (no entries created)
- Maintains full 40-hour weeks when time-off project is configured
- Example: Mon-Thu work entries + Fri vacation entry = 40 hours total

**Future Days:**
- If submitting on Thursday for full week, Friday gets default notes
- Can customize with `future_day_notes` in `.project.yaml`
</key_behaviors>
</workflow>

<workflow name="project_setup">
<purpose>
Interactive setup to create `.project.yaml` configuration file with Harvest project and task IDs.
</purpose>

<when_to_use>
- First time using skill in a project
- Switching to different Harvest project
- Updating project/task IDs
</when_to_use>

<execution>
```bash
python3 ~/.claude/skills/harvest_timesheet/run.py setup
```

Prompts for:
- Harvest Project ID
- Harvest Task ID
- Hours per day (default: 8.0)
- Default notes (used when no commits found)
</execution>

<note>
**Finding Project/Task IDs:**
Run helper script to list IDs from recent time entries:
```bash
python3 ~/.claude/skills/harvest_timesheet/list_all_entries.py
```
</note>
</workflow>

<workflow name="setup_auth">
<purpose>
Configure Harvest API authentication credentials.
</purpose>

<when_to_use>
- First time setup
- Rotating access tokens
- Setting up on new machine
</when_to_use>

<execution>
Credentials stored in `~/.harvest/credentials`:
```
HARVEST_ACCESS_TOKEN=your_token_here
HARVEST_ACCOUNT_ID=your_account_id_here
```

Or set as environment variables:
```bash
export HARVEST_ACCESS_TOKEN='your_token'
export HARVEST_ACCOUNT_ID='your_account_id'
```
</execution>
</workflow>

<workflow name="setup_timeoff">
<purpose>
Configure time-off/vacation project for intelligent time tracking. When configured, days off create proper time entries instead of being skipped.
</purpose>

<when_to_use>
- After initial project setup
- Want complete time tracking (no gaps in timesheet)
- Need to track vacation/sick days properly
- Want reasons logged for days off
</when_to_use>

<execution>
**Discover your time-off project:**
```bash
python3 ~/.claude/skills/harvest_timesheet/list_projects.py
```
Lists all projects, highlighting time-off/vacation/PTO projects with their IDs and tasks.

**Interactive setup:**
```bash
python3 ~/.claude/skills/harvest_timesheet/setup_timeoff.py
```

Prompts for:
- Time-off project selection (from detected projects)
- Task ID selection
- Default reason for auto-run mode

Creates `time_off` section in `.project.yaml`.
</execution>

<behavior>
**With time-off configured:**
- When you mark a day off, you're prompted for reason (e.g., "Vacation in Hawaii")
- Time entry created in time-off project with that reason
- Full 40-hour week maintained (e.g., 32 work hours + 8 vacation hours)

**Without time-off configured:**
- Days off simply skip time entry creation (gaps in timesheet)
- Legacy behavior (backward compatible)
</behavior>
</workflow>

## Configuration Files

<configuration>
**`.project.yaml`** (per-project, in project root):
```yaml
harvest:
  project_id: "12345678"           # Regular work project
  task_id: "87654321"              # Regular work task
  default_notes: "Development work"
  hours_per_day: 8.0
  future_day_notes: "Planned work" # Optional

  # Optional: Time-off configuration for smart vacation/sick day tracking
  time_off:
    project_id: "99999999"         # Vacation/PTO project
    task_id: "88888888"            # Vacation/PTO task
    default_reason: "Time off"     # Used by run_auto.py
```

**`~/.harvest/credentials`** (global):
```
HARVEST_ACCESS_TOKEN=your_token_here
HARVEST_ACCOUNT_ID=your_account_id
```

**Slash command**: `/timesheets` - LLM-orchestrated workflow with proper venv handling
**Manual run script**: `run.py` - Interactive menu-driven (for standalone use)
</configuration>

## Helper Scripts

<helpers>
**List all projects (with time-off detection):**
```bash
python3 ~/.claude/skills/harvest_timesheet/list_projects.py
```
Discovers all Harvest projects with IDs and tasks. Highlights time-off/vacation/PTO projects.

**Setup time-off tracking:**
```bash
python3 ~/.claude/skills/harvest_timesheet/setup_timeoff.py
```
Interactive wizard to configure time-off project in `.project.yaml`.

**Check current week entries:**
```bash
python3 ~/.claude/skills/harvest_timesheet/check_week.py
```
Shows all entries for current week with hours and notes.

**List all recent entries:**
```bash
python3 ~/.claude/skills/harvest_timesheet/list_all_entries.py
```
Shows projects and tasks from last 30 days - useful for finding IDs.

**Delete specific entry:**
```bash
python3 ~/.claude/skills/harvest_timesheet/delete_entry.py <entry_id>
```
Removes a time entry by ID (use check_week.py to find IDs).
</helpers>

## Common Issues

<troubleshooting>
**Issue: "Task ID must be numeric"**
- Cause: Used task name instead of numeric ID
- Fix: Run `list_all_entries.py` to find correct numeric task ID
- Update `.project.yaml` with numeric ID

**Issue: "Duplicate entries created"**
- Cause: Running old version that appended notes
- Fix: Skill is now idempotent - delete duplicates, re-run safely
- Use `delete_entry.py` to remove duplicates

**Issue: "Not in git repository"**
- Cause: Running outside git repo
- Effect: All entries use default_notes instead of commit summaries
- Fix: Run from project root, or accept default notes behavior

**Issue: "Authentication failed"**
- Cause: Missing/invalid credentials
- Fix: Check `~/.harvest/credentials` or environment variables
- Verify token at https://id.getharvest.com/developers

**Issue: "EOF when reading a line"**
- Cause: Interactive prompts don't work in non-TTY environments
- Fix: Use `run_auto.py` instead of `run.py`
</troubleshooting>

## Integration Tips

<integration>
**First-Time Setup:**
1. Configure credentials: `setup_harvest_auth()` or set environment variables
2. Configure project: `workflow_project_setup()` or create `.project.yaml`
3. **(Optional)** Configure time-off: `python3 ~/.claude/skills/harvest_timesheet/setup_timeoff.py`
4. Test: Run `/timesheets` slash command

**Weekly Routine:**
1. Make commits throughout the week with clear messages
2. Thursday afternoon: run `/timesheets` slash command
3. Review entries with `check_week.py`
4. Submit for approval in Harvest web interface

**Git Commit Best Practices:**
- Use clear, descriptive commit messages
- Group related changes in single commits
- Skill will summarize these for timesheets

**Time-Off Best Practices:**
- Configure time-off project for complete tracking (no gaps)
- Use descriptive reasons: "Vacation - Hawaii", "Sick day", "Holiday - Thanksgiving"
- Auto-run uses default_reason from config

**Multiple Projects:**
- Each project needs its own `.project.yaml`
- Switch directories before running skill
- Credentials are global (~/.harvest/credentials)
- Can have different time-off projects per project config
</integration>

## Security Notes

<security>
- Never commit `.harvest/credentials` or `.project.yaml` with sensitive data
- Add to `.gitignore` if needed
- Use environment variables in CI/CD environments
- Rotate access tokens periodically
- Credentials stored in user home directory only
</security>

## Architecture

<architecture>
**Core Modules:**
- `main.py` - Workflow orchestration
- `harvest_api.py` - Harvest API v2 client
- `git_analyzer.py` - Git commit extraction and summarization
- `timesheet_generator.py` - Entry generation and submission
- `config.py` - Configuration management

**Entry Points:**
- `run_auto.py` - Auto-execution (no prompts)
- `run.py` - Interactive menu
- Both auto-activate virtual environment

**Key Features:**
- Idempotent updates (replace, not append)
- Existing entry detection and update
- Week boundary handling (Monday-Friday)
- Future day support (e.g., Friday when submitting Thursday)
</architecture>

## Skill Completion

<completion>
The skill completes successfully when:
1. All time entries submitted to Harvest (created or updated)
2. Results displayed showing entry counts
3. Total hours match expected (hours_per_day × working days)
4. No API errors encountered

**Success Output:**
```
✓ Timesheet submitted successfully!
  Created: 0 entries
  Updated: 5 entries
  Total hours: 40.0
  Date range: Nov 17-21, 2025
```

**Idempotency Verified:**
- Running again shows same entry counts
- Notes don't duplicate
- Safe to re-run anytime
</completion>

## Related Documentation

<references>
- Harvest API v2: https://help.getharvest.com/api-v2/
- Skill README: `~/.claude/skills/harvest_timesheet/README.md`
- Requirements: `~/.claude/skills/harvest_timesheet/requirements.txt`
</references>
