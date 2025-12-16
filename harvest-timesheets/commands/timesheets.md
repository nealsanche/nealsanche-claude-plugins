---
description: 'Submit weekly Harvest timesheets through LLM-guided conversation'
---

# timesheets

LLM-orchestrated Harvest timesheet submission with intelligent conversation and UI prompts.

## Your Role

You are orchestrating the timesheet submission workflow. Use Bash to execute Python scripts from the harvest_operations module, then guide the user through submission using natural conversation and **AskUserQuestion** for choices.

## Workflow

### Step 1: Check Prerequisites and Load Configuration

**First, check if .project.yaml exists in the current directory:**

Use the Bash tool to check:
```bash
if [ -f ".project.yaml" ]; then echo "CONFIG_EXISTS=true"; else echo "CONFIG_EXISTS=false"; fi
```

**If CONFIG_EXISTS=false:**
- Stop the workflow
- Tell the user: "❌ Configuration missing. You need to set up your Harvest project first."
- Provide setup instructions:
  ```
  **Setup Steps:**
  1. **Find your project IDs:** Run this to see your Harvest projects:
     `cd ~/.claude/skills/harvest_timesheet && source venv/bin/activate && python3 list_projects.py`

  2. **Run project setup:** Follow the interactive prompts:
     `cd ~/.claude/skills/harvest_timesheet && source venv/bin/activate && python3 -c "from harvest_timesheet.main import workflow_project_setup; workflow_project_setup()"`

  3. **(Optional) Setup time-off tracking:**
     `cd ~/.claude/skills/harvest_timesheet && source venv/bin/activate && python3 setup_timeoff.py`

  4. Then run `/timesheets` again
  ```
- STOP - don't continue

**If CONFIG_EXISTS=true:**

Load configuration and analyze the week using the Bash tool:

```bash
cd ~/.claude/skills && source harvest_timesheet/venv/bin/activate && python3 << 'PYTHON_SCRIPT'
import sys
from pathlib import Path
import json
import os

# Change to the original working directory where .project.yaml should be
original_cwd = os.environ.get('OLDPWD', os.getcwd())
if original_cwd and original_cwd != os.getcwd():
    os.chdir(original_cwd)

sys.path.insert(0, str(Path.home() / '.claude/skills'))

from harvest_timesheet.harvest_operations import load_configuration, analyze_week

try:
    config, client = load_configuration()
    analysis = analyze_week()

    output = {
        'success': True,
        'week_start': analysis.week_dates[0].strftime('%b %d'),
        'week_end': analysis.week_dates[-1].strftime('%b %d, %Y'),
        'has_git': analysis.has_git,
        'total_commits': analysis.stats['total_commits'],
        'days_with_commits': analysis.stats['days_with_commits'],
        'days_without_commits': analysis.stats['days_without_commits'],
        'project_id': config.project_id,
        'hours_per_day': config.hours_per_day,
        'time_off_enabled': bool(config.time_off_project_id),
        'time_off_project_id': config.time_off_project_id if config.time_off_project_id else None,
        'week_dates': [{'date': d.strftime('%Y-%m-%d'), 'day_name': d.strftime('%A'), 'display': d.strftime('%A (%b %d)')} for d in analysis.week_dates]
    }

    print(json.dumps(output, indent=2))

except Exception as e:
    import traceback
    output = {
        'success': False,
        'error': str(e),
        'traceback': traceback.format_exc()
    }
    print(json.dumps(output, indent=2))
PYTHON_SCRIPT
```

**Parse the JSON output** and store the values for later use in the workflow.

**If success=false:** Show the error message and stop the workflow.

### Step 2: Show Week Summary

Using the JSON output from Step 1, present the week summary in a friendly way:

```
## 📅 Week of {week_start} - {week_end}

[If has_git is true:]
✅ Found **{total_commits} commits** across **{days_with_commits} days**
[If days_without_commits > 0:]
📝 {days_without_commits} days will use default notes

[If has_git is false:]
📝 Not in git repository - using default notes for all days

**Project**: {project_id}
**Hours/day**: {hours_per_day}

[If time_off_enabled is true:]
✅ **Time-off tracking enabled**
Days off will create entries in project {time_off_project_id}

[If time_off_enabled is false:]
⚠️  **Time-off tracking disabled** - days off will be skipped
```

### Step 3: Ask About Days Off

Use **AskUserQuestion** tool to ask about days off:

**First question:**
```
Question: "Were there any days off this week (vacation, sick, holiday)?"
Header: "Days Off"
Options:
  - "No days off" / "I worked all 5 days"
  - "Yes, I had days off" / "I'll specify which days"
```

**If yes, follow up with:**

Use the AskUserQuestion tool with multiSelect=true.
- Question: "Which days were you off?"
- Header: "Select Days"
- multiSelect: true
- Options: Use the week_dates array from Step 1 JSON output to build options dynamically:
  - For each day in week_dates, create an option with:
    - label: The 'display' value (e.g., "Monday (Nov 18)")
    - description: "Mark as day off"

Example (use actual dates from JSON):
- "Monday (Nov 18)" / "Mark as day off"
- "Tuesday (Nov 19)" / "Mark as day off"
- "Wednesday (Nov 20)" / "Mark as day off"
- "Thursday (Nov 21)" / "Mark as day off"
- "Friday (Nov 22)" / "Mark as day off"

**Store the selected days** - you'll need to map them back to date objects for Step 5.

### Step 4: Ask for Reasons (if time-off enabled)

For each day marked off (only if `config.time_off_project_id` exists):

**Use AskUserQuestion with common reasons:**
```
Question: "What was the reason for [Day]?"
Header: "Reason"
Options:
  - "Vacation" / "Personal time off"
  - "Sick day" / "Medical appointment or illness"
  - "Holiday" / "Company or federal holiday"
  - "Personal day" / "Personal matters"
```

User can also choose "Other" to type custom reason.

### Step 5: Generate and Preview Entries

Build a days_off dictionary from the user's responses in Steps 3-4.

**Format:**
- Keys: Date strings in 'YYYY-MM-DD' format (from week_dates)
- Values: Reason strings (from Step 4)
- Example: `{"2025-11-21": "Thanksgiving Holiday", "2025-11-22": "Vacation"}`

**Create a JSON file with the workflow data:**

Use the Bash tool to create a temporary JSON file with all the data needed:
```bash
cd ~/.claude/skills && source harvest_timesheet/venv/bin/activate && cat > /tmp/timesheet_workflow.json << 'JSON'
{
  "days_off": {
    "2025-11-21": "Thanksgiving Holiday",
    "2025-11-22": "Vacation"
  }
}
JSON
```

**Then run the generation script:**
```bash
cd [USER_PROJECT_DIR] && ~/.claude/skills/harvest_timesheet/venv/bin/python3 << 'PYTHON_SCRIPT'
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.home() / '.claude/skills'))

from harvest_timesheet.harvest_operations import load_configuration, analyze_week, generate_entries, format_entries_preview

# Load workflow data
with open('/tmp/timesheet_workflow.json') as f:
    workflow_data = json.load(f)

# Load config and analyze
config, client = load_configuration()
analysis = analyze_week()

# Convert days_off strings to date objects
from datetime import datetime
days_off = {}
for date_str, reason in workflow_data['days_off'].items():
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    days_off[date_obj] = reason

# Generate entries
entries = generate_entries(analysis, config, days_off)

# Format and print preview
preview = format_entries_preview(entries)
print("\n## 📋 Preview\n")
print(preview)

# Save entries for Step 6
entries_json = [{'date': str(e.date), 'hours': e.hours, 'notes': e.notes, 'project_id': e.project_id, 'task_id': e.task_id} for e in entries]
with open('/tmp/timesheet_entries.json', 'w') as f:
    json.dump({'entries': entries_json, 'count': len(entries)}, f, indent=2)
PYTHON_SCRIPT
```

**Show the preview output** to the user.

### Step 6: Confirm and Submit

Use **AskUserQuestion** for final confirmation:

```
Question: "Ready to submit these {len(entries)} entries to Harvest?"
Header: "Confirm"
Options:
  - "Yes, submit now" / "Submit all entries"
  - "No, cancel" / "Don't submit, let me review"
```

**If yes:**

```bash
cd [USER_PROJECT_DIR] && ~/.claude/skills/harvest_timesheet/venv/bin/python3 << 'PYTHON_SCRIPT'
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.home() / '.claude/skills'))

from harvest_timesheet.harvest_operations import load_configuration, submit_entries

# Load entries from Step 5
with open('/tmp/timesheet_entries.json') as f:
    data = json.load(f)

# Reconstruct entry objects
from collections import namedtuple
Entry = namedtuple('Entry', ['date', 'hours', 'notes', 'project_id', 'task_id'])
from datetime import datetime

entries = []
for e in data['entries']:
    entries.append(Entry(
        date=datetime.strptime(e['date'], '%Y-%m-%d').date(),
        hours=e['hours'],
        notes=e['notes'],
        project_id=e['project_id'],
        task_id=e['task_id']
    ))

# Load client
config, client = load_configuration()

# Submit
result = submit_entries(entries, client)

# Print results as JSON
output = {
    'success': result.success,
    'created': result.created,
    'updated': result.updated,
    'total_hours': result.total_hours,
    'date_range': result.date_range,
    'failed': result.failed if hasattr(result, 'failed') else 0,
    'errors': result.errors if hasattr(result, 'errors') else []
}

print(json.dumps(output, indent=2))
PYTHON_SCRIPT
```

**Parse the JSON output and show results:**
```
[If success is true:]
## ✅ Success!

- **Created**: {created} entries
- **Updated**: {updated} entries
- **Total hours**: {total_hours}
- **Date range**: {date_range}

[If success is false:]
## ⚠️ Completed with errors

- **Created**: {created}
- **Updated**: {updated}
- **Failed**: {failed}

**Errors:**
{list each error}
```

**Cleanup:**
```bash
rm -f /tmp/timesheet_workflow.json /tmp/timesheet_entries.json
```

## Important Notes

- **Always use AskUserQuestion** for user choices (don't use terminal prompts)
- **Show previews** before submitting
- **Be conversational** - explain what you're doing
- **Handle errors gracefully** - offer helpful next steps
- **Validate day selections** - make sure they match week_dates
- **Parse user responses** - handle "Mon", "Monday", date objects, etc.
- **Create days_off dict** mapping date strings to reason strings
- **Use Bash tool** for all Python execution - never try to execute Python directly

## Example Flow

```
User: /timesheets

You: *Check for .project.yaml*

You: *Load config and analyze week using Bash*

You: 📅 Week of Nov 18 - Nov 22
     ✅ Found 42 commits across 4 days
     ✅ Time-off tracking enabled

You: *Use AskUserQuestion*
     "Were there any days off this week?"

User: *Selects "Yes, I had days off"*

You: *Use AskUserQuestion with multiSelect*
     "Which days were you off?"

User: *Selects Thursday, Friday*

You: *Use AskUserQuestion for each day*
     "What was the reason for Thursday?"

User: *Selects "Holiday"* -> "Thanksgiving"

You: "What was the reason for Friday?"

User: *Selects "Vacation"* -> "Day after Thanksgiving"

You: *Generate entries using Bash and show preview*
     📋 Preview
     1. Monday: 8h - Features: Add auth system...
     2. Tuesday: 8h - Features: Implement OAuth...
     3. Wednesday: 8h - Fixes: Fix login bug...
     4. Thursday: 8h - Thanksgiving
     5. Friday: 8h - Day after Thanksgiving

     Total: 40 hours

You: *Use AskUserQuestion*
     "Ready to submit these 5 entries?"

User: *Selects "Yes, submit now"*

You: *Submit using Bash and show results*
     ✅ Success!
     - Updated: 5 entries
     - Total hours: 40.0
     - Date range: Nov 18-22, 2025

You: *Cleanup temp files*
```

## Begin Workflow

**Start executing the workflow now** - check for configuration and begin the conversation.
