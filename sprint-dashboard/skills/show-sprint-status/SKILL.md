---
name: show-sprint-status
description: Launch a live sprint status dashboard from BMAD sprint-status.yaml. Creates a Python web server with WebSocket updates, dark mode UI, auto-shutdown when no clients connected. Use when user wants to view sprint progress, monitor story status, or needs a visual dashboard for BMAD projects.
---

<objective>
Launch a beautiful, real-time sprint status dashboard that reads from BMAD's sprint-status.yaml file. The server runs in the background, updates via WebSocket when the YAML file changes, and auto-shuts down when all browser clients disconnect.
</objective>

<quick_start>
<workflow>
1. Find sprint-status.yaml in the current BMAD project using Glob tool
2. Start a NEW server in background (auto-assigns a free port)
3. Parse the server output to get the assigned port
4. Open the dashboard in the default browser at the correct port
5. Server auto-shuts down when browser tab closes (no clients connected for 30s)
</workflow>

<locate_sprint_status>
Use Glob tool to find `**/sprint-status.yaml` in the current project.

Expected locations:
- `docs/sprint-artifacts/sprint-status.yaml`
- `sprint-status.yaml`

If not found, inform user that sprint-status.yaml is required and suggest running sprint-planning workflow.
</locate_sprint_status>
</quick_start>

<server_implementation>
<important>
- DO NOT kill existing servers - multiple dashboards can run simultaneously on different ports
- Each server auto-assigns its own free port (no conflicts)
- Parse the server's stdout to get the actual port, not lsof/grep
</important>

<startup_sequence>
Execute these as SEPARATE Bash tool calls:

**Step 1: Start server in background**
Use Bash with `run_in_background: true`:
```bash
PYTHONUNBUFFERED=1 uv run "${CLAUDE_PLUGIN_ROOT}/skills/show-sprint-status/server.py" --yaml-path "{absolute_yaml_path}"
```
Note: Do NOT specify --port; let it auto-assign a free port.
PYTHONUNBUFFERED=1 ensures output is immediately available for parsing.
Save the background task ID returned.

**Step 2: Wait for server startup**
```bash
sleep 2
```

**Step 3: Get port from server output**
Use TaskOutput tool with the background task ID (non-blocking: `block: false`) to read the server's output.
Parse the output to find the line containing `PORT=` and extract the port number.

Example output to parse:
```
Starting server on http://localhost:9876
Watching: /path/to/sprint-status.yaml
PORT=9876
Server ready at http://localhost:9876
```

**Step 4: Open browser with correct port**
```bash
open "http://localhost:{extracted_port}"
```
</startup_sequence>
</server_implementation>

<dashboard_features>
<display_elements>
- Project name and current date
- Epic progress bars with completion percentage
- Story cards grouped by epic showing status (backlog, ready-for-dev, in-progress, review, done)
- Color-coded status indicators
- Last updated timestamp
- Auto-refresh indicator
</display_elements>

<status_colors>
- backlog: gray (#6b7280)
- ready-for-dev: blue (#3b82f6)
- in-progress: yellow (#eab308)
- review: purple (#a855f7)
- done: green (#22c55e)
</status_colors>

<real_time_updates>
- WebSocket connection to server
- File watcher on sprint-status.yaml
- Pushes updates when file changes
- Reconnection logic if connection drops
</real_time_updates>
</dashboard_features>

<auto_shutdown>
<behavior>
Server tracks connected WebSocket clients. When last client disconnects, starts 30-second countdown. If no new clients connect within 30 seconds, server shuts down gracefully.
</behavior>

<manual_shutdown>
```bash
# Find and kill a specific server by its port
lsof -ti :{port} | xargs kill

# Or kill all sprint dashboard servers
pkill -f "show-sprint-status/server.py"
```
</manual_shutdown>
</auto_shutdown>

<success_criteria>
- Sprint status YAML file found in project
- Server started successfully in background
- Port extracted from server output (not guessed via lsof)
- Browser opens to dashboard at the correct port
- Dashboard displays current sprint status with correct data
- WebSocket connection established (green indicator)
- Server shuts down automatically when browser tab closed
</success_criteria>

<troubleshooting>
<no_yaml_found>
If sprint-status.yaml not found, inform user:
"No sprint-status.yaml found. This skill requires a BMAD project with sprint tracking enabled. Run sprint-planning workflow first."
</no_yaml_found>

<server_not_starting>
If TaskOutput shows an error or no PORT= line:
1. Check the full error message in the task output
2. Ensure `uv` is installed (`brew install uv` or `pip install uv`)
3. Check that the yaml path is valid and readable
</server_not_starting>

<wrong_port_opened>
NEVER use `lsof | grep python` to find the port - this finds ANY Python server.
ALWAYS parse the background task output for the `PORT=` line to get the correct port.
</wrong_port_opened>
</troubleshooting>
