# Neal's Claude Code Plugins

A collection of custom Claude Code plugins for various productivity workflows.

## Installation

Add this marketplace to Claude Code:

```
/plugin marketplace add nealsanche/nealsanche-claude-plugins
```

Then install individual plugins:

```
/plugin install sprint-dashboard@nealsanche-plugins
/plugin install moon-phase@nealsanche-plugins
/plugin install figma-analyzer@nealsanche-plugins
/plugin install harvest-timesheets@nealsanche-plugins
```

## Plugins

### sprint-dashboard

Live sprint status dashboard with WebSocket updates for BMAD projects.

- Real-time dashboard served via Python WebSocket server
- Auto-refreshes when sprint-status.yaml or story files change
- Dark mode UI with status-colored story cards
- Auto-shutdown when browser tab closes

**Usage:** `/status` in any BMAD project with a `sprint-status.yaml` file

### moon-phase

Display current moon phase with detailed ASCII art visualization.

- Accurate astronomical calculations using Skyfield
- ASCII art showing current illumination
- Moonrise/moonset times for your location
- Next full/new moon dates

**Usage:** `/moon`

### figma-analyzer

Analyze Figma designs via MCP tools for pixel-perfect implementation.

- Extracts design tokens, spacing, typography
- Documents component hierarchy
- Generates implementation specs
- Requires Figma MCP server configured

**Usage:** `/analyze-figma <figma-url>`

### harvest-timesheets

Submit weekly Harvest timesheets through LLM-guided conversation.

- Analyzes git commits to suggest time entries
- Interactive workflow for reviewing and submitting
- Supports multiple projects and tasks
- Requires Harvest API credentials

**Usage:** `/timesheets`

## Requirements

- Claude Code CLI
- Python 3.10+ (for sprint-dashboard and moon-phase)
- `uv` package manager recommended
- Figma MCP server (for figma-analyzer)
- Harvest API credentials (for harvest-timesheets)

## License

MIT
