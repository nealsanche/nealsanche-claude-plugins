---
description: Launch live sprint status dashboard with real-time WebSocket updates from BMAD sprint-status.yaml
---

<objective>
Launch the show-sprint-status skill to display a beautiful, real-time sprint dashboard.
</objective>

<process>
Execute these steps using SEPARATE tool calls (not one combined script):

## Step 1: Find sprint-status.yaml

Use the Glob tool to find `**/sprint-status.yaml` in the current project.

Common BMAD locations:
- `docs/sprint-artifacts/sprint-status.yaml`
- `sprint-status.yaml`
- `../docs/sprint-artifacts/sprint-status.yaml`

If no file found: Inform user that sprint-status.yaml is required and suggest running sprint-planning workflow. STOP.

## Step 2: Start the server in background

Use Bash with `run_in_background: true`:

```bash
PYTHONUNBUFFERED=1 uv run "${CLAUDE_PLUGIN_ROOT}/skills/show-sprint-status/server.py" --yaml-path "{absolute_yaml_path}"
```

**IMPORTANT:**
- Do NOT kill existing servers first. Multiple dashboards can run simultaneously on different ports.
- PYTHONUNBUFFERED=1 ensures output is immediately available for parsing.

Save the background task ID that is returned (e.g., "b5a7445").

## Step 3: Wait for server startup

```bash
sleep 2
```

## Step 4: Get the port from server output

Use the **TaskOutput** tool with `block: false` and the task_id from Step 2 to read the server's output.

Parse the output to find the `PORT=` line. Example output:
```
Starting server on http://localhost:9876
Watching: /path/to/sprint-status.yaml
PORT=9876
Server ready at http://localhost:9876
```

Extract the port number from the `PORT=` line.

**NEVER** use `lsof | grep python` to find the port - this finds ANY Python server, not necessarily the one you just started.

## Step 5: Open the browser

```bash
open "http://localhost:{extracted_port}"
```

## Step 6: Report success

Tell user:
- The dashboard URL: http://localhost:{extracted_port}
- The server will auto-close 30 seconds after they close the browser tab
- Changes to story files or sprint-status.yaml will update the dashboard in real-time
</process>

<success_criteria>
- Sprint status YAML file found
- Server started in background
- Port extracted from server output (NOT from lsof)
- Browser opened to dashboard at the correct port
- User informed of the port and auto-shutdown behavior
</success_criteria>
