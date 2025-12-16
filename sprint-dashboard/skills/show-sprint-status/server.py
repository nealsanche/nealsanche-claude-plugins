#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "websockets>=13.0",
#     "pyyaml>=6.0",
# ]
# ///
"""
BMAD Sprint Status Dashboard Server

A minimal web server that serves a real-time sprint status dashboard.
- Watches sprint-status.yaml for changes
- Pushes updates to connected clients via WebSocket
- Auto-shuts down when no clients connected for 30 seconds

Run with: uv run ~/.claude/skills/show-sprint-status/server.py --yaml-path <path>
"""

import argparse
import asyncio
import json
import os
import re
import socket
import sys
from http import HTTPStatus
from typing import Set

import websockets
import yaml


def find_free_port() -> int:
    """Find a free port by binding to port 0 and letting the OS assign one."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

# Global state
connected_clients: Set = set()
shutdown_task = None
yaml_path: str = ""
story_dir: str = ""
last_modified: float = 0
last_story_modified: float = 0
server_port: int = 8765

# HTML template embedded
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sprint Status Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html {
            background: #1a1a2e;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e7;
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        h1 {
            font-size: 1.75rem;
            font-weight: 600;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: #9ca3af;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            animation: pulse 2s infinite;
        }

        .status-dot.disconnected {
            background: #ef4444;
            animation: none;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .epic-section {
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255,255,255,0.05);
        }

        .epic-section.collapsed .stories-grid {
            display: none;
        }

        .epic-section.collapsed .progress-bar {
            margin-bottom: 0;
        }

        .epic-section.done {
            opacity: 0.7;
        }

        .epic-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            cursor: pointer;
            user-select: none;
        }

        .epic-header:hover {
            opacity: 0.8;
        }

        .epic-title {
            font-size: 1.125rem;
            font-weight: 500;
            color: #f4f4f5;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .epic-toggle {
            font-size: 0.75rem;
            transition: transform 0.2s;
        }

        .epic-section.collapsed .epic-toggle {
            transform: rotate(-90deg);
        }

        .epic-progress {
            font-size: 0.875rem;
            color: #9ca3af;
        }

        .progress-bar {
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 1rem;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6, #22c55e);
            border-radius: 3px;
            transition: width 0.5s ease;
        }

        .epic-section.done .progress-fill {
            background: #22c55e;
        }

        .stories-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }

        .story-card {
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            padding: 1rem;
            border-left: 3px solid;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .story-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .story-card.backlog { border-color: #6b7280; }
        .story-card.ready-for-dev { border-color: #3b82f6; }
        .story-card.in-progress { border-color: #eab308; }
        .story-card.review { border-color: #a855f7; }
        .story-card.done { border-color: #22c55e; }

        .story-key {
            font-size: 0.75rem;
            color: #9ca3af;
            margin-bottom: 0.25rem;
            font-family: 'SF Mono', 'Fira Code', monospace;
        }

        .story-title {
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: #e4e4e7;
        }

        .story-status {
            display: inline-block;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: 500;
        }

        .story-status.backlog { background: rgba(107,114,128,0.2); color: #9ca3af; }
        .story-status.ready-for-dev { background: rgba(59,130,246,0.2); color: #60a5fa; }
        .story-status.in-progress { background: rgba(234,179,8,0.2); color: #fbbf24; }
        .story-status.review { background: rgba(168,85,247,0.2); color: #c084fc; }
        .story-status.done { background: rgba(34,197,94,0.2); color: #4ade80; }

        .last-updated {
            text-align: center;
            font-size: 0.75rem;
            color: #6b7280;
            margin-top: 2rem;
        }

        .no-data {
            text-align: center;
            padding: 4rem;
            color: #6b7280;
        }

        .summary-bar {
            display: flex;
            gap: 1.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .summary-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
        }

        .summary-count {
            font-weight: 600;
            font-size: 1.25rem;
        }

        .summary-item .summary-count { color: #9ca3af; }
        .summary-item.done .summary-count { color: #4ade80; }
        .summary-item.in-progress .summary-count { color: #fbbf24; }
        .summary-item.review .summary-count { color: #c084fc; }
        .summary-item.ready-for-dev .summary-count { color: #60a5fa; }
        .summary-item.backlog .summary-count { color: #9ca3af; }
        .summary-item.drafted .summary-count { color: #818cf8; }
        .summary-item.optional .summary-count { color: #6b7280; }

        .status-mismatch {
            border: 2px dashed #f59e0b !important;
        }

        .status-dual {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .status-source {
            font-size: 0.6rem;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .status-row {
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Sprint Status</h1>
            <div class="status-indicator">
                <div class="status-dot" id="connectionDot"></div>
                <span id="connectionStatus">Connected</span>
            </div>
        </header>

        <div class="summary-bar" id="summaryBar"></div>

        <main id="dashboard">
            <div class="no-data">Loading sprint status...</div>
        </main>

        <div class="last-updated" id="lastUpdated"></div>
    </div>

    <script>
        let ws;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        function connect() {
            // Use same host:port as the page was loaded from
            ws = new WebSocket(`ws://${window.location.host}/ws`);

            ws.onopen = () => {
                console.log('WebSocket connected');
                reconnectAttempts = 0;
                document.getElementById('connectionDot').classList.remove('disconnected');
                document.getElementById('connectionStatus').textContent = 'Connected';
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                renderDashboard(data);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                document.getElementById('connectionDot').classList.add('disconnected');
                document.getElementById('connectionStatus').textContent = 'Disconnected';

                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    setTimeout(connect, 2000 * reconnectAttempts);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }

        // Format status for display: uppercase, replace - and _ with spaces
        function formatStatus(status) {
            return status.replace(/[-_]/g, ' ').toUpperCase();
        }

        // Get CSS class for status (normalize to use hyphens)
        function statusClass(status) {
            return status.replace(/_/g, '-');
        }

        function renderDashboard(data) {
            const dashboard = document.getElementById('dashboard');
            const summaryBar = document.getElementById('summaryBar');

            if (!data.epics || data.epics.length === 0) {
                dashboard.innerHTML = '<div class="no-data">No sprint data available</div>';
                return;
            }

            // Dynamically collect all status values and their counts
            const counts = {};
            data.epics.forEach(epic => {
                epic.stories.forEach(story => {
                    const status = statusClass(story.status);
                    counts[status] = (counts[status] || 0) + 1;
                });
            });

            // Sort statuses: done first, then alphabetically
            const statusOrder = Object.keys(counts).sort((a, b) => {
                if (a === 'done') return -1;
                if (b === 'done') return 1;
                if (a === 'in-progress') return -1;
                if (b === 'in-progress') return 1;
                return a.localeCompare(b);
            });

            // Render summary bar dynamically
            summaryBar.innerHTML = statusOrder.map(status => `
                <div class="summary-item ${status}">
                    <span class="summary-count">${counts[status]}</span>
                    <span>${formatStatus(status)}</span>
                </div>
            `).join('');

            // Render epics
            let html = '';
            data.epics.forEach((epic, index) => {
                const doneCount = epic.stories.filter(s => s.status === 'done').length;
                const totalCount = epic.stories.length;
                const progress = totalCount > 0 ? (doneCount / totalCount * 100) : 0;
                const isEpicDone = doneCount === totalCount && totalCount > 0;
                const epicClasses = ['epic-section'];
                if (isEpicDone) {
                    epicClasses.push('done', 'collapsed');
                }

                html += `
                    <div class="${epicClasses.join(' ')}" data-epic-index="${index}">
                        <div class="epic-header" onclick="toggleEpic(${index})">
                            <div class="epic-title">
                                <span class="epic-toggle">▼</span>
                                ${epic.title || epic.key}
                                ${isEpicDone ? '<span style="color: #22c55e; font-size: 0.75rem; margin-left: 0.5rem;">✓ Complete</span>' : ''}
                            </div>
                            <div class="epic-progress">${doneCount}/${totalCount} stories</div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                        <div class="stories-grid">
                            ${epic.stories.map(story => {
                                const stClass = statusClass(story.status);
                                const mismatchClass = story.status_mismatch ? 'status-mismatch' : '';

                                // Render status section - dual if mismatch, single otherwise
                                let statusHtml;
                                if (story.status_mismatch) {
                                    const fileClass = statusClass(story.file_status);
                                    const yamlClass = statusClass(story.yaml_status);
                                    statusHtml = `
                                        <div class="status-dual">
                                            <div class="status-row">
                                                <span class="status-source">file:</span>
                                                <span class="story-status ${fileClass}">${formatStatus(story.file_status)}</span>
                                            </div>
                                            <div class="status-row">
                                                <span class="status-source">yaml:</span>
                                                <span class="story-status ${yamlClass}">${formatStatus(story.yaml_status)}</span>
                                            </div>
                                        </div>
                                    `;
                                } else {
                                    statusHtml = `<span class="story-status ${stClass}">${formatStatus(story.status)}</span>`;
                                }

                                return `
                                    <div class="story-card ${stClass} ${mismatchClass}">
                                        <div class="story-key">${story.key}</div>
                                        <div class="story-title">${story.title || story.key}</div>
                                        ${statusHtml}
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;
            });

            dashboard.innerHTML = html;

            // Update timestamp
            document.getElementById('lastUpdated').textContent =
                `Last updated: ${new Date().toLocaleTimeString()}`;
        }

        function toggleEpic(index) {
            const epic = document.querySelector(`[data-epic-index="${index}"]`);
            if (epic) {
                epic.classList.toggle('collapsed');
            }
        }

        // Start connection
        connect();

        // Handle page visibility for reconnection
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && ws.readyState !== WebSocket.OPEN) {
                reconnectAttempts = 0;
                connect();
            }
        });
    </script>
</body>
</html>
'''


def get_status_from_story_file(story_dir: str, story_key: str) -> str | None:
    """Read status directly from story markdown file.

    Story files have format:
    ```
    # Story X.Y: Title

    Status: done
    ...
    ```

    Returns normalized status or None if not found.
    Handles variations like "Done", "Ready for Review", "In Progress", etc.
    """
    story_file = os.path.join(story_dir, f"{story_key}.md")
    if not os.path.exists(story_file):
        return None

    try:
        with open(story_file, 'r') as f:
            # Read first 10 lines to find Status line
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                # Match "Status: <value>" - capture everything after Status:
                match = re.match(r'^Status:\s*(.+)', line, re.IGNORECASE)
                if match:
                    raw_status = match.group(1).strip().lower()
                    # Normalize common status variations
                    return normalize_status(raw_status)
    except Exception:
        pass

    return None


def normalize_status(raw_status: str) -> str:
    """Normalize status string to standard values.

    Maps various status formats to: backlog, drafted, ready-for-dev, in-progress, review, done
    """
    raw = raw_status.lower().strip()

    # Remove common suffixes like "(100% complete...)" or parenthetical notes
    raw = re.sub(r'\s*\([^)]*\)\s*$', '', raw).strip()

    # Direct matches (already normalized)
    if raw in ('backlog', 'drafted', 'ready-for-dev', 'in-progress', 'review', 'done'):
        return raw

    # Map variations
    if raw in ('done', 'complete', 'completed', 'finished'):
        return 'done'
    if raw.startswith('ready for review') or raw == 'ready-for-review':
        return 'review'
    if raw.startswith('in progress') or raw.startswith('in-progress') or raw == 'wip':
        return 'in-progress'
    if raw.startswith('ready for dev') or raw.startswith('ready-for-dev') or raw == 'ready':
        return 'ready-for-dev'
    if raw == 'draft' or raw == 'drafted':
        return 'drafted'

    # Fallback: return first word, hyphenated
    first_word = raw.split()[0] if raw else 'backlog'
    return first_word.replace('_', '-')


def parse_sprint_status(yaml_file: str) -> dict:
    """Parse sprint-status.yaml and extract structured data for the dashboard.

    Story status is read from individual story .md files as primary source,
    falling back to the YAML file if the story file doesn't exist.
    """
    try:
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return {"error": str(e), "epics": []}

    if not data:
        return {"epics": []}

    # Determine story directory from YAML metadata or default to same directory
    story_location = data.get('story_location', '')
    yaml_dir = os.path.dirname(yaml_file)

    if story_location:
        # story_location is relative to project root, but we need absolute path
        # Walk up from yaml_dir to find project root (where story_location exists)
        story_dir = None
        check_dir = yaml_dir
        for _ in range(5):  # Max 5 levels up
            candidate = os.path.join(check_dir, story_location)
            if os.path.isdir(candidate):
                story_dir = candidate
                break
            # Also check if yaml_dir IS the story_location
            if os.path.basename(yaml_dir) == os.path.basename(story_location):
                story_dir = yaml_dir
                break
            check_dir = os.path.dirname(check_dir)

        if not story_dir:
            story_dir = yaml_dir  # Fallback
    else:
        story_dir = yaml_dir

    # Extract development_status section
    dev_status = data.get('development_status', {})

    # Group stories by epic
    epics = {}
    epic_order = []

    for key, status in dev_status.items():
        # Skip retrospective entries
        if 'retrospective' in key:
            continue

        # Check if this is an epic (format: epic-N or just the epic status)
        if key.startswith('epic-') and not any(c.isalpha() for c in key.split('-')[-1] if c != 'e'):
            # This is an epic entry like "epic-1: in-progress"
            epic_num = key
            if epic_num not in epics:
                epics[epic_num] = {
                    'key': epic_num,
                    'title': f'Epic {key.split("-")[-1]}',
                    'status': status,
                    'stories': []
                }
                epic_order.append(epic_num)
        else:
            # This is a story (format: N-N-name)
            parts = key.split('-')
            if len(parts) >= 2 and parts[0].isdigit():
                epic_num = f"epic-{parts[0]}"
                if epic_num not in epics:
                    epics[epic_num] = {
                        'key': epic_num,
                        'title': f'Epic {parts[0]}',
                        'status': 'in-progress',
                        'stories': []
                    }
                    epic_order.append(epic_num)

                # Create story entry
                # Get status from both sources to detect disagreements
                file_status = get_status_from_story_file(story_dir, key)
                yaml_status = status

                # Use file status as primary, YAML as fallback
                actual_status = file_status if file_status else yaml_status

                story_title = '-'.join(parts[2:]).replace('-', ' ').title() if len(parts) > 2 else key
                story_entry = {
                    'key': key,
                    'title': story_title,
                    'status': actual_status
                }

                # If statuses disagree, include both for display
                if file_status and file_status != yaml_status:
                    story_entry['file_status'] = file_status
                    story_entry['yaml_status'] = yaml_status
                    story_entry['status_mismatch'] = True

                epics[epic_num]['stories'].append(story_entry)

    # Sort stories within each epic by numeric story number
    # Keys are like "1-2-story-name" where first number is epic, second is story
    def story_sort_key(story):
        """Extract numeric epic and story numbers for proper sorting."""
        import re
        # Extract all numbers from the key
        numbers = re.findall(r'\d+', story['key'])
        if len(numbers) >= 2:
            # Return (epic_num, story_num) as integers for numeric sorting
            return (int(numbers[0]), int(numbers[1]))
        elif len(numbers) == 1:
            return (int(numbers[0]), 0)
        else:
            # Fallback to string sort if no numbers found
            return (float('inf'), story['key'])

    for epic in epics.values():
        epic['stories'].sort(key=story_sort_key)

    # Return epics in order, plus story_dir for file watching
    return {
        "epics": [epics[k] for k in epic_order if k in epics],
        "_story_dir": story_dir  # Internal: used by file watcher
    }


async def handle_http_request(connection, request):
    """Handle HTTP requests - serve HTML for root, upgrade for /ws."""
    if request.path == '/ws':
        # Allow WebSocket upgrade
        return None

    # Serve HTML with correct content-type for any other path
    response = connection.respond(HTTPStatus.OK, HTML_TEMPLATE)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response


async def websocket_handler(websocket):
    """Handle WebSocket connections."""
    global connected_clients, shutdown_task

    # Cancel any pending shutdown
    if shutdown_task:
        shutdown_task.cancel()
        shutdown_task = None

    connected_clients.add(websocket)
    print(f"Client connected. Total clients: {len(connected_clients)}", flush=True)

    try:
        # Send initial data (filter out internal fields)
        data = parse_sprint_status(yaml_path)
        send_data = {k: v for k, v in data.items() if not k.startswith('_')}
        await websocket.send(json.dumps(send_data))

        # Keep connection alive and handle messages
        async for message in websocket:
            # Client can request refresh
            if message == "refresh":
                data = parse_sprint_status(yaml_path)
                send_data = {k: v for k, v in data.items() if not k.startswith('_')}
                await websocket.send(json.dumps(send_data))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(connected_clients)}", flush=True)

        # Start shutdown timer if no clients
        if len(connected_clients) == 0:
            shutdown_task = asyncio.create_task(shutdown_timer())


async def shutdown_timer():
    """Shutdown server after 30 seconds of no clients."""
    print("No clients connected. Shutting down in 30 seconds...", flush=True)
    await asyncio.sleep(30)

    if len(connected_clients) == 0:
        print("Shutting down server (no clients).", flush=True)
        sys.exit(0)


def get_story_files_mtime(dir_path: str) -> float:
    """Get the max mtime of all .md files in the story directory."""
    if not dir_path or not os.path.isdir(dir_path):
        return 0

    max_mtime = 0
    try:
        for filename in os.listdir(dir_path):
            if filename.endswith('.md') and not filename.startswith('epic-'):
                filepath = os.path.join(dir_path, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    if mtime > max_mtime:
                        max_mtime = mtime
                except OSError:
                    pass
    except OSError:
        pass
    return max_mtime


async def file_watcher():
    """Watch the YAML file and story files for changes and notify clients."""
    global last_modified, last_story_modified, story_dir

    while True:
        try:
            changed = False

            # Check YAML file
            current_modified = os.path.getmtime(yaml_path)
            if current_modified != last_modified:
                last_modified = current_modified
                changed = True

            # Check story files
            current_story_modified = get_story_files_mtime(story_dir)
            if current_story_modified != last_story_modified:
                last_story_modified = current_story_modified
                changed = True

            if changed:
                data = parse_sprint_status(yaml_path)
                # Update story_dir from parsed data
                story_dir = data.get('_story_dir', story_dir)

                # Notify all connected clients
                if connected_clients:
                    # Remove internal field before sending
                    send_data = {k: v for k, v in data.items() if not k.startswith('_')}
                    message = json.dumps(send_data)
                    await asyncio.gather(
                        *[client.send(message) for client in connected_clients],
                        return_exceptions=True
                    )
                    print(f"Files changed, notified {len(connected_clients)} clients", flush=True)
        except Exception as e:
            print(f"File watcher error: {e}", flush=True)

        await asyncio.sleep(1)  # Check every second


async def main(yaml_file: str, port: int):
    """Main entry point."""
    global yaml_path, last_modified, last_story_modified, story_dir, server_port

    yaml_path = yaml_file
    server_port = port

    # Verify YAML file exists
    if not os.path.exists(yaml_path):
        print(f"Error: YAML file not found: {yaml_path}", flush=True)
        sys.exit(1)

    last_modified = os.path.getmtime(yaml_path)

    # Initialize story_dir by parsing once
    initial_data = parse_sprint_status(yaml_path)
    story_dir = initial_data.get('_story_dir', '')
    last_story_modified = get_story_files_mtime(story_dir)

    print(f"Starting server on http://localhost:{port}", flush=True)
    print(f"Watching: {yaml_path}", flush=True)
    if story_dir:
        print(f"Watching story files in: {story_dir}", flush=True)

    # Start file watcher
    watcher_task = asyncio.create_task(file_watcher())

    # Start combined HTTP/WebSocket server
    async with websockets.serve(
        websocket_handler,
        "0.0.0.0",
        port,
        process_request=handle_http_request
    ):
        # Output port in easily parseable format for command scripts
        print(f"PORT={port}", flush=True)
        print(f"Server ready at http://localhost:{port}", flush=True)

        # Run forever (until shutdown)
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            watcher_task.cancel()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='BMAD Sprint Status Dashboard Server')
    parser.add_argument('--yaml-path', required=True, help='Path to sprint-status.yaml')
    parser.add_argument('--port', type=int, default=0, help='Server port (default: auto-assign free port)')

    args = parser.parse_args()

    # Find a free port if not specified or 0
    port = args.port if args.port > 0 else find_free_port()

    try:
        asyncio.run(main(args.yaml_path, port))
    except KeyboardInterrupt:
        print("\nServer stopped.", flush=True)
