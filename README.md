# Neal's Claude Code Plugins

A collection of custom Claude Code plugins for various productivity workflows.

## Quick Start

### 1. Add the Marketplace

In Claude Code, run:

```
/plugin marketplace add nealsanche/nealsanche-claude-plugins
```

### 2. Browse and Install Plugins

```
/plugin
```

Select "Browse Plugins" and choose which plugins to install. Or install directly:

```
/plugin install sprint-dashboard@nealsanche-plugins
/plugin install moon-phase@nealsanche-plugins
/plugin install figma-analyzer@nealsanche-plugins
/plugin install harvest-timesheets@nealsanche-plugins
```

### 3. Verify Installation

After installation, the plugin commands become available as slash commands in Claude Code.

---

## Plugins

### sprint-dashboard

Live sprint status dashboard with WebSocket updates for BMAD projects.

**Features:**
- Real-time dashboard served via Python WebSocket server
- Auto-refreshes when sprint-status.yaml or story files change
- Dark mode UI with status-colored story cards
- Auto-shutdown 30 seconds after browser tab closes
- Multiple dashboards can run simultaneously on different ports

**Prerequisites:**
- Python 3.10+
- `uv` package manager (`brew install uv` on macOS)
- A BMAD project with `sprint-status.yaml` file

**Usage:**
```
/status
```

The command will:
1. Find your `sprint-status.yaml` file
2. Start a local WebSocket server
3. Open your browser to the dashboard
4. Auto-shutdown when you close the tab

---

### moon-phase

Display current moon phase with detailed ASCII art visualization.

**Features:**
- Accurate astronomical calculations using Skyfield library
- ASCII art showing current illumination and phase
- Moonrise/moonset times for your location
- Next full moon and new moon dates
- Lunar age (days since new moon)

**Prerequisites:**
- Python 3.10+
- Virtual environment with Skyfield installed

**First-time Setup:**
```bash
python3 -m venv ~/.venvs/moon-phase
source ~/.venvs/moon-phase/bin/activate
pip install skyfield
```

**Usage:**
```
/moon
```

You'll be prompted for your latitude/longitude for accurate rise/set times.

---

### figma-analyzer

Analyze Figma designs via MCP tools for pixel-perfect implementation.

**Features:**
- Extracts design tokens, spacing, typography, colors
- Documents component hierarchy
- Generates structured implementation specs
- Supports variables and design system tokens

**Prerequisites:**
- Figma MCP server configured in Claude Code
- Figma file access (via URL)

**Setup Figma MCP Server:**

Add to your Claude Code MCP configuration (`~/.claude/mcp.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "figma": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-figma"],
      "env": {
        "FIGMA_ACCESS_TOKEN": "your_figma_token_here"
      }
    }
  }
}
```

Get your Figma token at: https://www.figma.com/developers/api#access-tokens

**Usage:**
```
/analyze-figma https://www.figma.com/file/xxxxx/Your-Design
```

---

### harvest-timesheets

Submit weekly Harvest timesheets through LLM-guided conversation.

**Features:**
- Analyzes git commits to auto-generate time entry descriptions
- Interactive workflow for reviewing entries before submission
- Supports marking days off (vacation, holidays)
- Handles multiple projects and tasks
- Idempotent - safe to re-run (updates existing entries)

**Prerequisites:**
- Python 3.10+
- Harvest account with API access
- Personal Access Token from Harvest

**Step 1: Get Harvest Credentials**

1. Go to https://id.getharvest.com/developers
2. Create a new Personal Access Token
3. Note your Account ID (shown on the same page)

**Step 2: Configure Credentials**

Create credentials file:
```bash
mkdir -p ~/.harvest
cat > ~/.harvest/credentials << 'EOF'
HARVEST_ACCESS_TOKEN=your_access_token_here
HARVEST_ACCOUNT_ID=your_account_id_here
EOF
chmod 600 ~/.harvest/credentials
```

**Step 3: Find Your Project/Task IDs**

After installing the plugin, run the list command to see available projects:
```bash
python3 ~/.claude/plugins/harvest-timesheets/skills/harvest_timesheet/list_all_entries.py
```

**Step 4: Configure Your Project**

In your git repository, create `.project.yaml`:
```yaml
harvest:
  project_id: "12345678"      # From step 3
  task_id: "87654321"         # From step 3
  default_notes: "Development work"
  hours_per_day: 8.0
```

**Usage:**
```
/timesheets
```

The command will:
1. Analyze your git commits for the current week
2. Generate time entries with commit summaries
3. Ask you to review and confirm
4. Submit to Harvest

---

## Updating Plugins

To update plugins when new versions are available:

```
/plugin update sprint-dashboard@nealsanche-plugins
```

Or update all:
```
/plugin update --all
```

## Uninstalling

Remove a specific plugin:
```
/plugin uninstall sprint-dashboard@nealsanche-plugins
```

Remove the marketplace:
```
/plugin marketplace remove nealsanche-plugins
```

## Troubleshooting

### Plugin commands not showing up
- Restart Claude Code after installing plugins
- Verify installation with `/plugin` and check "Installed Plugins"

### Python dependency issues
- Use `uv` for faster, more reliable Python package management
- Create isolated virtual environments per skill

### Harvest authentication fails
- Verify token hasn't expired
- Check credentials file permissions: `chmod 600 ~/.harvest/credentials`
- Ensure Account ID matches your Harvest account

### Figma MCP not connecting
- Verify MCP server is configured in `~/.claude/mcp.json`
- Check Figma token has read access to the file
- Restart Claude Code after MCP config changes

## License

MIT

## Author

Neal Sanche - https://github.com/nealsanche
