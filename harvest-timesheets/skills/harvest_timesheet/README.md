# Harvest Timesheet Automation

A Claude Code skill that automates weekly Harvest timesheet submissions by analyzing git commits and generating time entries.

> 📘 **Full Documentation:** See [SKILL.md](./SKILL.md) for complete skill documentation

## Features

- **Git Commit Analysis**: Automatically extracts and summarizes commits from the current week
- **Smart Entry Generation**: Creates time entries with meaningful descriptions based on your work
- **Idempotent Updates**: Safely re-run without duplicating notes (replaces instead of appends)
- **Days Off Handling**: Prompts for vacation/holiday days to exclude from timesheet
- **Multiple Workflows**: Setup, authentication, and submission workflows
- **Secure Credential Storage**: Supports environment variables and .env files
- **Auto Virtual Environment**: Automatically activates venv when run

## Installation

1. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

2. **Get Harvest API credentials:**
   - Visit https://id.getharvest.com/developers
   - Create a Personal Access Token
   - Note your Account ID

## Quick Start

### 1. Setup Authentication

Run the authentication setup workflow:

```python
from harvest_timesheet import workflow_setup_auth

workflow_setup_auth()
```

This will prompt you for your Harvest Access Token and Account ID.

### 2. Configure Your Project

In your project directory, run the project setup:

```python
from harvest_timesheet import workflow_project_setup

workflow_project_setup()
```

This creates a `.project.yaml` file with your Harvest project and task IDs.

### 3. Submit Your Timesheet

Every Thursday (or whenever you need to submit):

```python
from harvest_timesheet import workflow_submit_timesheet

workflow_submit_timesheet()
```

This will:
- Analyze your git commits for the week
- Ask about any days off
- Generate time entries with commit summaries
- **For future days (e.g., Friday when submitting on Thursday)**: Use default notes
- Show a preview
- Submit to Harvest (with your confirmation)

**Thursday Submission Feature**: When you submit on Thursday for the full week, Friday automatically gets your default notes from `.project.yaml` (or custom `future_day_notes` if configured).

## Project Configuration

The `.project.yaml` file contains:

```yaml
harvest:
  project_id: "12345678"           # Your Harvest project ID
  task_id: "98765432"              # Your Harvest task ID
  default_notes: "Development work" # Used when no commits found AND for future days
  hours_per_day: 8.0               # Hours to log per day
  future_day_notes: "Planned work" # (Optional) Custom notes for future days like Friday
```

**Note about `default_notes` and `future_day_notes`:**
- `default_notes`: Used for past/present days with no commits AND future days (if `future_day_notes` not set)
- `future_day_notes`: (Optional) Used specifically for future days when submitting on Thursday for the full week

## Credential Storage

Credentials can be stored in several ways:

### Option 1: Environment Variables (Recommended)

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export HARVEST_ACCESS_TOKEN='your_token_here'
export HARVEST_ACCOUNT_ID='your_account_id_here'
```

### Option 2: .env File

Create a `.env` file in your project root:

```
HARVEST_ACCESS_TOKEN=your_token_here
HARVEST_ACCOUNT_ID=your_account_id_here
```

**Important**: Add `.env` to your `.gitignore`!

### Option 3: ~/.harvest/credentials

Create `~/.harvest/credentials`:

```
HARVEST_ACCESS_TOKEN=your_token_here
HARVEST_ACCOUNT_ID=your_account_id_here
```

## How It Works

### Commit Analysis

The skill analyzes git commits for Monday-Friday of the current week:

1. Extracts commits for each day
2. Cleans and deduplicates commit messages
3. Categorizes commits (features, fixes, refactoring, etc.)
4. Generates concise summaries suitable for timesheets

### Entry Generation

For each working day:
- If commits exist: Creates summary from commit messages
- If no commits: Uses default notes from `.project.yaml`
- Logs configured hours per day (default: 8.0)

### Updating Existing Entries

If entries already exist in Harvest for a date/project:
- The skill updates them instead of creating duplicates
- Notes are replaced with new commit summaries (idempotent - not appended)
- Hours are updated to the configured value
- Safe to re-run multiple times without duplicating content

## Usage Examples

### Example 1: Standard Weekly Submission

```python
from harvest_timesheet import workflow_submit_timesheet

# Run on Thursday to submit timesheet
workflow_submit_timesheet()

# Output:
# === HARVEST TIMESHEET SUBMISSION ===
#
# Repository: /Users/john/projects/myapp
#
# Week: November 17 - November 21, 2025
#
# === Days Off ===
# Monday 2025-11-17 - Day off? (y/n): n
# Tuesday 2025-11-18 - Day off? (y/n): n
# Wednesday 2025-11-19 - Day off? (y/n): n
# Thursday 2025-11-20 - Day off? (y/n): n
# Friday 2025-11-21 - Day off? (y/n): y
#
# === Timesheet Preview ===
#
# 1. Monday 2025-11-17 - 8.0 hours
#    Implemented user authentication; Fixed login validation; Updated API endpoints
#
# 2. Tuesday 2025-11-18 - 8.0 hours
#    Added password reset; Refactored auth middleware; Updated tests
#
# [...]
#
# Submit these entries to Harvest? (yes/no): yes
#
# ✓ Monday 2025-11-17: Created (8.0 hours)
# ✓ Tuesday 2025-11-18: Created (8.0 hours)
# [...]
```

### Example 2: Re-running (Updates Existing)

If you run the workflow again for the same week:

```python
workflow_submit_timesheet()

# Output:
# Found existing entries for 4 date(s)
#    These will be updated (notes replaced)
#
# === Submitting to Harvest ===
#
# ✓ Monday 2025-11-17: Updated (8.0 hours)
# ✓ Tuesday 2025-11-18: Updated (8.0 hours)
# [...]
```

The new commit notes replace existing entries (idempotent behavior).

## Workflows

### workflow_project_setup()

Interactive setup for creating `.project.yaml` configuration file.

**Use when:**
- Setting up a new project
- Changing Harvest project or task IDs

### workflow_setup_auth()

Interactive setup for Harvest API authentication credentials.

**Use when:**
- First time setup
- Updating or rotating access tokens
- Setting up on a new machine

### workflow_submit_timesheet()

Main workflow for analyzing commits and submitting timesheets.

**Use when:**
- Submitting your weekly timesheet (typically Thursdays)
- Re-running to update entries with new commits

## Troubleshooting

### "Not in a git repository"

The skill works best in a git repository. If you're not in one:
- All entries will use default notes from `.project.yaml`
- Consider initializing a git repo: `git init`

### "Authentication failed"

Check your credentials:
1. Verify token at https://id.getharvest.com/developers
2. Ensure Account ID is correct
3. Check environment variables are set: `echo $HARVEST_ACCESS_TOKEN`

### "Project ID not found"

Get the correct IDs:
1. Log into Harvest web interface
2. Navigate to your project
3. Check URL: `https://ACCOUNT.harvestapp.com/projects/PROJECT_ID`
4. Update `.project.yaml` with correct IDs

### "No commits found"

This is normal if:
- You haven't committed this week
- You're working on non-code tasks
- The skill will use default notes instead

### "Duplicate entries"

The skill automatically handles duplicates:
- Existing entries are updated, not duplicated
- Notes are replaced (idempotent - not appended) when re-running
- No manual cleanup needed - safe to run multiple times

## Best Practices

1. **Commit regularly** with meaningful messages
2. **Run on Thursdays** to review and submit before end of week
3. **Keep `.project.yaml` updated** if project structure changes
4. **Review the preview** before submitting
5. **Use default notes** for non-code work days

## Security

- Never commit credentials to git
- Add `.project.yaml` to `.gitignore` if it contains sensitive info
- Use environment variables for production use
- Rotate access tokens periodically

## Python API

You can also use the individual modules programmatically:

```python
from harvest_timesheet.config import load_project_config, get_harvest_credentials
from harvest_timesheet.git_analyzer import get_current_week_dates, get_commits_by_day
from harvest_timesheet.harvest_api import HarvestClient
from harvest_timesheet.timesheet_generator import generate_weekly_entries, submit_entries

# Load configuration
config = load_project_config()
access_token, account_id = get_harvest_credentials()

# Create client
client = HarvestClient(access_token, account_id)

# Get week dates
week_dates = get_current_week_dates()

# Generate entries
entries = generate_weekly_entries(
    week_dates=week_dates,
    project_id=config['harvest']['project_id'],
    task_id=config['harvest']['task_id'],
    hours_per_day=config['harvest']['hours_per_day'],
    default_notes=config['harvest']['default_notes'],
    days_off=[]
)

# Submit
results = submit_entries(entries, client)
```

## Documentation

**Skill Documentation:**
- [SKILL.md](./SKILL.md) - Complete skill guide with workflows and integration
- [references/api-reference.md](./references/api-reference.md) - Harvest API details
- [references/git-analysis.md](./references/git-analysis.md) - Commit analysis documentation
- [references/configuration.md](./references/configuration.md) - Configuration guide
- [references/examples.md](./references/examples.md) - Real-world usage examples

## Skill Structure

```
harvest_timesheet/
├── SKILL.md                    # Main skill documentation
├── README.md                   # This file
├── references/                 # Detailed documentation
│   ├── api-reference.md
│   ├── git-analysis.md
│   ├── configuration.md
│   └── examples.md
├── run.py                      # Interactive execution
├── run_auto.py                 # Non-interactive execution
├── main.py                     # Workflow orchestration
├── harvest_api.py              # Harvest API client
├── git_analyzer.py             # Git commit analysis
├── timesheet_generator.py      # Entry generation and submission
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
└── venv/                       # Virtual environment
```

## Contributing

This skill is part of the Claude Code skills ecosystem. Contributions and improvements are welcome!

## License

MIT
