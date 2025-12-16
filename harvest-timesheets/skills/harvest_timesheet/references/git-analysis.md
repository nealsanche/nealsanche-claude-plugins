# Git Commit Analysis

## Overview

The skill analyzes git commits to generate meaningful timesheet descriptions.

## Commit Extraction

### Week Boundaries
- Monday through Friday only
- Uses Monday 00:00:00 to Friday 23:59:59
- Ignores weekend commits

### Git Command Used
```bash
git log --all --since="2025-11-17 00:00:00" --until="2025-11-17 23:59:59" \
  --pretty=format:"%H|%s|%an|%ae|%ad" --date=short
```

**Format Fields:**
- `%H`: Commit hash
- `%s`: Subject (commit message)
- `%an`: Author name
- `%ae`: Author email
- `%ad`: Author date

### Filtering
- Groups commits by date (spent_date)
- Deduplicates commit messages
- Cleans up common patterns (WIP, fixup, merge commits)

## Commit Categorization

### Categories
Commits are classified by message patterns:

**Features:** (prefix match)
- "feat:", "feature:", "add:", "implement:"
- "new:", "create:", "build:"

**Fixes:** (prefix match)
- "fix:", "bug:", "bugfix:", "hotfix:"
- "patch:", "repair:"

**Refactoring:** (prefix match)
- "refactor:", "refac:", "restructure:"
- "cleanup:", "clean:"

**Documentation:** (prefix match)
- "docs:", "doc:", "documentation:"
- "readme:", "comment:"

**Tests:** (prefix match)
- "test:", "tests:", "testing:"
- "spec:", "coverage:"

**Chores:** (prefix match)
- "chore:", "deps:", "dependency:"
- "config:", "ci:", "build:"

**Other:**
- Anything not matching above patterns

### Summarization

**Per-day summary format:**
```
Features: [list]; Fixes: [list]; [other categories]
```

**Example:**
```
Features: Add user authentication, Implement API endpoints;
Fixes: Fix login validation, Resolve timeout issues;
Refactoring: Clean up middleware code
```

### Text Cleaning

**Removed patterns:**
- Git merge artifacts (`Merge branch 'main'`)
- WIP markers (`WIP:`, `[WIP]`)
- Fixup commits (`fixup!`, `squash!`)
- Auto-generated messages

**Deduplication:**
- Case-insensitive comparison
- Exact message matching
- Keeps first occurrence

**Truncation:**
- Individual messages: 100 characters max
- Total daily summary: ~200 characters (suitable for Harvest)
- Truncated messages end with "..."

## Statistics

The skill tracks:
- Total commit count for the week
- Days with commits vs. days without
- Commits per category
- Commits per day

**Example output:**
```
=== Git Commit Analysis ===
Total commits: 62
Days with commits: 4
Days without commits: 1
  (will use default notes)

Breakdown:
  Features: 25
  Fixes: 18
  Refactoring: 12
  Tests: 5
  Chores: 2
```

## Future Day Handling

### Scenario
Submitting on Thursday for full week (including Friday).

### Behavior
- Detects Friday is "future" (after today)
- Uses `default_notes` from config
- Or `future_day_notes` if specified in `.project.yaml`

### Configuration
```yaml
harvest:
  default_notes: "Development work"  # Used for past days with no commits
  future_day_notes: "Planned work"   # Used for future days
```

## Edge Cases

### No Commits
- Day has no commits → uses `default_notes`
- Entire week has no commits → all entries use `default_notes`
- Not an error, just informational

### Not in Git Repository
- Skill detects with `git rev-parse --show-toplevel`
- Falls back to `default_notes` for all days
- Warning displayed but continues

### Multiple Authors
- Includes all commits regardless of author
- Useful for pair programming
- Can filter by author if needed (future enhancement)

### Commit Message Formats

**Conventional Commits:**
```
feat(auth): add login endpoint
fix(api): resolve timeout issue
```
Skill extracts category and description.

**Simple Messages:**
```
Add user authentication
Fix login bug
```
Skill still categorizes based on keywords.

**Multi-line Messages:**
Only first line (subject) is used. Commit body ignored.

## Implementation Notes

### Performance
- Single git log command per day
- Parsing in Python (fast)
- Typical runtime: <1 second for 100+ commits

### Memory Usage
- Stores all commits in memory
- Typical: <1MB for week of commits
- No disk caching needed

### Error Handling
```python
try:
    commits = get_commits_by_day(week_dates)
except GitAnalysisError as e:
    # Fall back to default notes
    print(f"Warning: {e}")
    use_default_notes = True
```

### Testing
Helper scripts for testing analysis:
- `demo.py`: Shows analysis without submitting
- `test_thursday.py`: Tests Thursday submission with Friday
