# Harvest API Reference

## Overview

The skill uses Harvest API v2 for all timesheet operations.

Base URL: `https://api.harvestapp.com/v2`

## Authentication

**Required Headers:**
```
Authorization: Bearer {access_token}
Harvest-Account-ID: {account_id}
Content-Type: application/json
User-Agent: Harvest-Timesheet-Automation/1.0
```

## Endpoints Used

### Get Current User
```
GET /users/me
```
Returns authenticated user information. Used to verify credentials.

**Response:**
```json
{
  "id": 123456,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com"
}
```

### List Time Entries
```
GET /time_entries?from={date}&to={date}&project_id={id}
```

**Parameters:**
- `from`: Start date (YYYY-MM-DD)
- `to`: End date (YYYY-MM-DD)
- `project_id`: Filter by project (optional)

**Response:**
```json
{
  "time_entries": [
    {
      "id": 123456789,
      "spent_date": "2025-11-17",
      "hours": 8.0,
      "notes": "Development work",
      "project": {
        "id": 12345,
        "name": "Project Name"
      },
      "task": {
        "id": 67890,
        "name": "Task Name"
      }
    }
  ]
}
```

### Create Time Entry
```
POST /time_entries
```

**Payload:**
```json
{
  "project_id": 12345,
  "task_id": 67890,
  "spent_date": "2025-11-17",
  "hours": 8.0,
  "notes": "Work description"
}
```

**Response:**
Returns created entry object.

### Update Time Entry
```
PATCH /time_entries/{entry_id}
```

**Payload:**
```json
{
  "hours": 8.0,
  "notes": "Updated work description"
}
```

**Response:**
Returns updated entry object.

### Delete Time Entry
```
DELETE /time_entries/{entry_id}
```

**Response:**
200 OK (no body)

## Error Handling

**Common Error Codes:**
- `401`: Invalid credentials
- `403`: Not authorized (wrong account ID or insufficient permissions)
- `404`: Resource not found (invalid project/task ID)
- `422`: Validation error (invalid date format, missing required fields)

**Error Response Format:**
```json
{
  "error": "Error type",
  "error_description": "Detailed error message"
}
```

## Rate Limits

Harvest API has rate limits:
- 100 requests per 15 seconds per account
- Skill typically makes 5-10 requests per run
- Well within limits for normal usage

## Implementation Notes

### Idempotent Updates
The skill makes updates idempotent by:
1. Querying existing entries for the week
2. If entry exists for date/project, UPDATE instead of CREATE
3. Notes are replaced (not appended) to prevent duplication

### Duplicate Detection
```python
# Check for existing entries by date and project
existing_by_date = check_for_existing_entries(entries, client)

# For each entry to submit
if entry.spent_date in existing_by_date:
    # Find matching project entry
    matching_entry = find_by_project_id(existing_by_date[entry.spent_date])
    if matching_entry:
        # UPDATE existing
        client.update_time_entry(matching_entry['id'], hours, notes)
    else:
        # CREATE new
        client.create_time_entry(...)
```

### Batch Operations
The skill processes entries sequentially (not in batch) because:
- Harvest API doesn't support batch operations
- Need to check for existing entries individually
- Error handling is clearer per-entry

## Security Considerations

**Credential Storage:**
- Never in code or skill files
- Stored in `~/.harvest/credentials` (600 permissions)
- Or environment variables

**API Token Permissions:**
- Requires "time_entries" scope
- Read and write access needed
- No admin permissions required

**Data Privacy:**
- Commit messages become timesheet notes
- Review generated notes before submission
- Don't include sensitive info in commits
