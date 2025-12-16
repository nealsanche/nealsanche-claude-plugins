# Configuration Guide

## Configuration Files

### Global Credentials: `~/.harvest/credentials`

**Location:** User home directory
**Purpose:** Store Harvest API credentials globally
**Format:** Plain text, environment variable style

**File contents:**
```
HARVEST_ACCESS_TOKEN=your_token_here
HARVEST_ACCOUNT_ID=your_account_id
```

**Permissions:**
```bash
chmod 600 ~/.harvest/credentials
```

**Security:**
- Never commit this file
- Not in any git repository
- User-only read/write

**Alternative:** Environment variables
```bash
export HARVEST_ACCESS_TOKEN='your_token'
export HARVEST_ACCOUNT_ID='123456'
```

### Project Configuration: `.project.yaml`

**Location:** Project root directory (where you run the skill)
**Purpose:** Per-project Harvest settings
**Format:** YAML

**Required fields:**
```yaml
harvest:
  project_id: "12345678"    # Numeric string
  task_id: "87654321"       # Numeric string
  default_notes: "Development work"
  hours_per_day: 8.0
```

**Optional fields:**
```yaml
harvest:
  future_day_notes: "Planned work"  # For future days (e.g., Friday on Thursday)
```

**Finding IDs:**
Use helper script:
```bash
python3 ~/.claude/skills/harvest_timesheet/list_all_entries.py
```

Shows:
```
Project ID: 45418127
Project Name: your-project-name
Tasks:
  - Task ID: 25016966, Name: Development
```

**Creating:**
```bash
python3 ~/.claude/skills/harvest_timesheet/run.py setup
```

**Git handling:**
Add to `.gitignore` if it contains sensitive info:
```
.project.yaml
```

## Configuration Priority

### Credential Loading Order
1. Environment variables (`HARVEST_ACCESS_TOKEN`, `HARVEST_ACCOUNT_ID`)
2. `~/.harvest/credentials` file
3. Project-local `.env` file (if present)

**First found wins.**

### Project Config Loading
1. Current directory `.project.yaml`
2. Error if not found (run setup workflow)

## Virtual Environment

### Auto-activation

**How it works:**
Both `run.py` and `run_auto.py` automatically activate their venv:

```python
def activate_venv():
    # Check if already in venv
    if in_venv():
        return

    # Find venv directory
    venv_dir = script_dir / 'venv'

    # Re-execute with venv python
    python_exe = venv_dir / 'bin' / 'python3'
    os.execv(str(python_exe), [str(python_exe)] + sys.argv)
```

**Result:**
No need to manually activate. Just run:
```bash
python3 ~/.claude/skills/harvest_timesheet/run_auto.py
```

### Manual Activation (if needed)
```bash
source ~/.claude/skills/harvest_timesheet/venv/bin/activate
```

### Dependencies
Located in `requirements.txt`:
```
requests>=2.31.0
PyYAML>=6.0
python-dotenv>=1.0.0
```

**Install:**
```bash
cd ~/.claude/skills/harvest_timesheet
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration Validation

### On Skill Run

**Checks performed:**
1. **Credentials exist?**
   - Look for `~/.harvest/credentials` or env vars
   - Error if missing: "Run authentication setup workflow"

2. **Project config exists?**
   - Look for `.project.yaml` in current directory
   - Error if missing: "Run project setup workflow"

3. **Credentials valid?**
   - Test with `GET /users/me`
   - Show authenticated user name
   - Error if invalid: "Check credentials"

4. **Project/Task IDs valid?**
   - Attempt to create/update entry
   - Error if invalid: "Project ID not found"

### Helper Commands

**Test authentication:**
```python
from harvest_timesheet.harvest_api import test_authentication
from harvest_timesheet.config import get_harvest_credentials

token, account_id = get_harvest_credentials()
test_authentication(token, account_id)
```

**Validate project config:**
```python
from harvest_timesheet.config import load_project_config

config = load_project_config()
print(config)
```

## Common Configuration Issues

### Issue: "Credentials not found"

**Cause:** No `~/.harvest/credentials` and no environment variables

**Fix:**
```bash
mkdir -p ~/.harvest
cat > ~/.harvest/credentials << EOF
HARVEST_ACCESS_TOKEN=your_token
HARVEST_ACCOUNT_ID=your_account_id
EOF
chmod 600 ~/.harvest/credentials
```

### Issue: "Configuration not found"

**Cause:** No `.project.yaml` in current directory

**Fix:**
```bash
python3 ~/.claude/skills/harvest_timesheet/run.py setup
```

Or create manually:
```yaml
harvest:
  project_id: "12345678"
  task_id: "87654321"
  default_notes: "Development work"
  hours_per_day: 8.0
```

### Issue: "Invalid project_id"

**Cause:** Using project ID from wrong account, or wrong format

**Fix:**
1. List your projects:
```bash
python3 ~/.claude/skills/harvest_timesheet/list_all_entries.py
```

2. Copy correct numeric ID (not name)

3. Update `.project.yaml` with correct ID

### Issue: "Task ID must be numeric"

**Cause:** Used task name instead of task ID

**Wrong:**
```yaml
task_id: "Development"  # ❌ Name
```

**Correct:**
```yaml
task_id: "25016966"  # ✅ Numeric ID
```

**Fix:**
Run `list_all_entries.py` to find numeric task ID.

## Multi-Project Setup

### Approach 1: Separate directories
```
~/projects/
  project-a/
    .project.yaml  # Project A config
    ... code ...
  project-b/
    .project.yaml  # Project B config
    ... code ...
```

Run skill from each project directory.

### Approach 2: Switch configs
```bash
# Project A week
cp .project.yaml.project-a .project.yaml
python3 ~/.claude/skills/harvest_timesheet/run_auto.py

# Project B week
cp .project.yaml.project-b .project.yaml
python3 ~/.claude/skills/harvest_timesheet/run_auto.py
```

### Approach 3: Environment-based
```bash
# Set per-project
export HARVEST_PROJECT_ID=12345
export HARVEST_TASK_ID=67890

# Modify skill to read from env (future enhancement)
```

## Best Practices

1. **Keep credentials global:** One `~/.harvest/credentials` for all projects
2. **Per-project configs:** Each repo has its own `.project.yaml`
3. **Gitignore sensitive data:** Don't commit credentials
4. **Rotate tokens:** Update credentials file when rotating
5. **Validate on setup:** Test authentication immediately
6. **Document project IDs:** Add comment in `.project.yaml` with project name
7. **Consistent hours:** Use same `hours_per_day` across projects for consistency
