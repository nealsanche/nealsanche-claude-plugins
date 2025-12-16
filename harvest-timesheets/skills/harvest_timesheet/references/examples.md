# Usage Examples

## Example 1: First Time Setup

**Scenario:** New user, never used the skill before

### Step 1: Get Harvest credentials
1. Visit https://id.getharvest.com/developers
2. Create Personal Access Token
3. Note your Account ID

### Step 2: Configure authentication
```bash
mkdir -p ~/.harvest
cat > ~/.harvest/credentials << 'EOF'
HARVEST_ACCESS_TOKEN=your_access_token_here
HARVEST_ACCOUNT_ID=your_account_id_here
EOF
chmod 600 ~/.harvest/credentials
```

### Step 3: Test authentication
```bash
python3 ~/.claude/skills/harvest_timesheet/list_all_entries.py
```

**Output:**
```
All recent time entries (last 30 days):

Project ID: 45418127
Project Name: securitas-18mo-team
Tasks:
  - Task ID: 25016966, Name: NB - AI Spike
```

### Step 4: Create project config
```bash
cd ~/projects/my-project
cat > .project.yaml << 'EOF'
harvest:
  project_id: "45418127"
  task_id: "25016966"
  default_notes: "Development work"
  hours_per_day: 8.0
EOF
```

### Step 5: Submit timesheet
```bash
python3 ~/.claude/skills/harvest_timesheet/run_auto.py
```

**Success!** Timesheet submitted.

---

## Example 2: Weekly Routine (Thursday Submission)

**Scenario:** Submitting timesheet every Thursday afternoon

### Commands
```bash
cd ~/projects/my-project
python3 ~/.claude/skills/harvest_timesheet/run_auto.py
```

### Output
```
============================================================
  HARVEST TIMESHEET SUBMISSION
============================================================

📂 Repository: /Users/john/projects/my-project

Loading project configuration...
✓ Configuration loaded

Loading Harvest credentials...
✓ Credentials loaded

Verifying Harvest authentication...
✓ Authenticated as: John Doe

============================================================
Week: November 17 - November 21, 2025
============================================================

=== Days Off ===
Mark any days you were on vacation or holiday:

Monday 2025-11-17 - Day off? (y/n): n
Tuesday 2025-11-18 - Day off? (y/n): n
Wednesday 2025-11-19 - Day off? (y/n): n
Thursday 2025-11-20 - Day off? (y/n): n
Friday 2025-11-21 - Day off? (y/n): n

✓ No days off this week

============================================================
Generating timesheet entries...
============================================================

=== Git Commit Analysis ===
Total commits: 45
Days with commits: 4
Days without commits: 1
  (will use default notes)

📅 Future days detected: 1 day(s)
   - Friday 2025-11-21
   Using default notes: "Development work"

=== Timesheet Preview ===

1. Monday 2025-11-17 - 8.0 hours
   Features: Add user authentication, Implement API endpoints;
   Fixes: Fix login validation, Resolve session timeout

2. Tuesday 2025-11-18 - 8.0 hours
   Features: Add password reset feature;
   Refactoring: Clean up middleware code;
   Tests: Add integration tests

3. Wednesday 2025-11-19 - 8.0 hours
   Features: Implement role-based permissions;
   Fixes: Fix CORS headers, Resolve database connection pooling

4. Thursday 2025-11-20 - 8.0 hours
   Features: Add audit logging;
   Fixes: Fix memory leak in websocket handler

5. Friday 2025-11-21 - 8.0 hours
   Development work

Total hours: 40.0

==================================================
Submit these entries to Harvest? (yes/no): yes

📝 Found existing entries for 2 date(s)
   These will be updated (notes replaced)

=== Submitting to Harvest ===

✓ Monday 2025-11-17: Updated (8.0 hours)
✓ Tuesday 2025-11-18: Updated (8.0 hours)
✓ Wednesday 2025-11-19: Created (8.0 hours)
✓ Thursday 2025-11-20: Created (8.0 hours)
✓ Friday 2025-11-21: Created (8.0 hours)

============================================================
  SUBMISSION RESULTS
============================================================

✓ Timesheet submitted successfully!
  Created: 3 entries
  Updated: 2 entries
  Total hours: 40.0
  Date range: Nov 17-21, 2025

============================================================
```

---

## Example 3: Vacation Day

**Scenario:** Monday was a holiday

### Interaction
```
Monday 2025-11-17 - Day off? (y/n): y
Tuesday 2025-11-18 - Day off? (y/n): n
Wednesday 2025-11-19 - Day off? (y/n): n
Thursday 2025-11-20 - Day off? (y/n): n
Friday 2025-11-21 - Day off? (y/n): n

✓ Marked 1 day(s) off
```

### Result
Only 4 entries created (Tuesday-Friday), total 32.0 hours.

---

## Example 4: No Commits (Non-code Work)

**Scenario:** Working on documentation, meetings, no code commits

### Output
```
=== Git Commit Analysis ===
Total commits: 0
Days with commits: 0
Days without commits: 5
  (will use default notes)

=== Timesheet Preview ===

1. Monday 2025-11-17 - 8.0 hours
   Development work

2. Tuesday 2025-11-18 - 8.0 hours
   Development work

[... all days use default_notes ...]
```

### Result
All entries created with `default_notes` from config.

---

## Example 5: Re-running (Idempotency)

**Scenario:** Already submitted, made more commits, want to update

### First Run
```
✓ Monday 2025-11-17: Created (8.0 hours)
```

**Notes:** "Add user authentication"

### Made More Commits
```bash
git commit -m "fix: resolve login bug"
git commit -m "feat: add password reset"
```

### Second Run
```
📝 Found existing entries for 1 date(s)
   These will be updated (notes replaced)

✓ Monday 2025-11-17: Updated (8.0 hours)
```

**New Notes:** "Features: Add user authentication, Add password reset; Fixes: Resolve login bug"

**Key Point:** Notes **replaced**, not appended. Safe to re-run.

---

## Example 6: Finding IDs for New Project

**Scenario:** Need to set up skill for a new project

### Step 1: List recent entries
```bash
python3 ~/.claude/skills/harvest_timesheet/list_all_entries.py
```

### Output
```
All recent time entries (last 30 days):

Project ID: 45418127
Project Name: securitas-18mo-team
Tasks:
  - Task ID: 25016966, Name: NB - AI Spike

Project ID: 12345678
Project Name: new-client-project
Tasks:
  - Task ID: 87654321, Name: Development
  - Task ID: 87654322, Name: Code Review
```

### Step 2: Choose IDs
For "new-client-project", using "Development" task:
- Project ID: `12345678`
- Task ID: `87654321`

### Step 3: Create config
```bash
cd ~/projects/new-client-project
cat > .project.yaml << 'EOF'
harvest:
  project_id: "12345678"
  task_id: "87654321"
  default_notes: "Client project development"
  hours_per_day: 8.0
EOF
```

---

## Example 7: Checking Submitted Entries

**Scenario:** Verify what was submitted this week

### Command
```bash
python3 ~/.claude/skills/harvest_timesheet/check_week.py
```

### Output
```
Time entries for week 2025-11-17 to 2025-11-21:

2025-11-17 - 1 entry/entries:
  Entry ID: 2795764339
  Hours: 8.0
  Task: NB - AI Spike
  Notes: Features: Add user authentication, Implement API endpoints...

2025-11-18 - 1 entry/entries:
  Entry ID: 2795764449
  Hours: 8.0
  Task: NB - AI Spike
  Notes: Features: Add password reset feature; Refactoring: Clean up...

[... more days ...]

Total entries: 5
Total hours: 40.0
```

---

## Example 8: Fixing Duplicate Entry

**Scenario:** Accidentally created duplicate entry on Wednesday

### Step 1: Find entry IDs
```bash
python3 ~/.claude/skills/harvest_timesheet/check_week.py
```

### Output
```
2025-11-19 - 2 entry/entries:
  Entry ID: 2795764636
  Hours: 8.0
  Notes: Features: Add permissions...

  Entry ID: 2795764522
  Hours: 8.0
  Notes:
```

### Step 2: Delete empty duplicate
```bash
python3 ~/.claude/skills/harvest_timesheet/delete_entry.py 2795764522
```

### Output
```
✓ Successfully deleted entry 2795764522
```

### Step 3: Verify
```bash
python3 ~/.claude/skills/harvest_timesheet/check_week.py
```

Now shows only 1 entry for Wednesday.

---

## Example 9: Custom Future Day Notes

**Scenario:** Want specific notes for Friday when submitting Thursday

### Config
```yaml
harvest:
  project_id: "45418127"
  task_id: "25016966"
  default_notes: "Development work"
  hours_per_day: 8.0
  future_day_notes: "Sprint planning and code review"
```

### Submission (on Thursday)
```
5. Friday 2025-11-21 - 8.0 hours
   Sprint planning and code review
```

**Result:** Friday uses `future_day_notes` instead of `default_notes`.

---

## Example 10: Interactive vs Auto Mode

### Interactive Mode
```bash
python3 ~/.claude/skills/harvest_timesheet/run.py submit
```

**Prompts:**
- Days off? (wait for input)
- Submit? (wait for confirmation)

### Auto Mode
```bash
python3 ~/.claude/skills/harvest_timesheet/run_auto.py
```

**Behavior:**
- Days off? → automatically "n"
- Submit? → automatically "yes"
- No waiting, runs to completion

**Use Case:**
- Interactive: First time, want to review
- Auto: Weekly routine, trust the process
