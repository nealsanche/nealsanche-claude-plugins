---
name: analyze-figma-design
description: Analyzes Figma designs via MCP tools to produce structured design specifications for pixel-perfect implementation. Extracts layout, spacing, typography, colors, and component hierarchy. Use when given a Figma URL, asked to implement a Figma design, or when design-to-code accuracy is critical.
---

<objective>
Transform Figma designs into detailed, structured specifications that enable pixel-perfect UI implementation. Uses Figma MCP tools to extract complete design data including layout, spacing, typography, colors, variables, and component structure—producing machine-readable specs that eliminate guesswork during implementation.
</objective>

<quick_start>
<workflow>
1. **Parse Figma URL**: Extract fileKey and nodeId from URL
   - Format: `https://figma.com/design/:fileKey/:fileName?node-id=:nodeId`
   - Convert `node-id=1-2` to `nodeId=1:2`

2. **Gather initial context** using MCP tools in parallel:
   ```
   mcp__figma__get_screenshot    → Visual reference
   mcp__figma__get_design_context → Code hints, structure, assets
   mcp__figma__get_variable_defs  → Design tokens (colors, spacing, typography)
   ```

3. **Ask clarifying questions** about:
   - Component naming conventions for the project
   - Responsive behavior intentions
   - Interactive states not visible in static design
   - Which existing components might map to design elements

4. **Drill down** on complex elements using `get_metadata` for structural details

5. **Generate structured spec** with all extracted data

6. **Produce output file** in JSON format with companion markdown summary
</workflow>

<url_parsing>
```javascript
// Extract from: https://figma.com/design/ABC123/MyFile?node-id=1-2
const url = new URL(figmaUrl);
const fileKey = url.pathname.split('/')[2]; // ABC123
const nodeId = url.searchParams.get('node-id').replace('-', ':'); // 1:2

// Branch URLs: https://figma.com/design/:fileKey/branch/:branchKey/:fileName
// Use branchKey as fileKey when present
```
</url_parsing>
</quick_start>

<analysis_process>
<phase name="1_initial_capture">
**Goal**: Get complete visual and structural data

Run these MCP calls (parallel when possible):
1. `mcp__figma__get_screenshot` - Visual reference for verification
2. `mcp__figma__get_design_context` - Primary source: code hints, component structure, asset URLs
3. `mcp__figma__get_variable_defs` - Design tokens used in the node

**Key data from get_design_context**:
- Component hierarchy and nesting
- Computed styles and measurements
- Asset download URLs for images/icons
- Code Connect mappings (if configured in Figma)
</phase>

<phase name="2_clarifying_questions">
**Ask the user about**:

- **Component mapping**: "I see a button with rounded corners and shadow. Should this map to your existing Button component, or document as a new pattern?"
- **Responsive intent**: "This layout appears fixed-width. How should it adapt on mobile?"
- **States**: "I only see the default state. Are there hover/active/disabled states in other frames?"
- **Naming**: "What naming convention should I use for components? (e.g., PascalCase, kebab-case)"
- **Tokens**: "Should I use your existing design tokens or document Figma's exact values?"

Use AskUserQuestion tool for structured choices where applicable.
</phase>

<phase name="3_deep_analysis">
**When to drill down with get_metadata**:
- Complex nested layouts needing structural clarity
- Auto-layout configurations
- Constraint systems for responsive behavior
- Component variants and properties

**Extract and document**:
- Exact pixel measurements (width, height, padding, margin, gap)
- Typography (font-family, size, weight, line-height, letter-spacing)
- Colors (hex, rgba, with opacity)
- Border (width, style, color, radius per corner)
- Shadows (x, y, blur, spread, color)
- Layout mode (flex direction, alignment, distribution)
</phase>

<phase name="4_component_mapping">
**Hybrid approach**:
1. Document the Figma design element with exact specs
2. Suggest existing project components that could implement it
3. Note any delta between existing component and design

```json
{
  "figmaElement": "Primary Action Button",
  "specs": { /* exact figma values */ },
  "suggestedComponent": "Button",
  "suggestedProps": { "variant": "primary", "size": "lg" },
  "delta": ["Design uses 16px radius, component uses 12px"]
}
```
</phase>
</analysis_process>

<output_format>
<structure>
Generate two files:
1. `{design-name}-spec.json` - Machine-readable complete spec
2. `{design-name}-spec.md` - Human-readable summary

**JSON Structure**:
```json
{
  "meta": {
    "figmaUrl": "original URL",
    "fileKey": "extracted",
    "nodeId": "extracted",
    "nodeName": "from Figma",
    "analyzedAt": "ISO timestamp",
    "dimensions": { "width": 0, "height": 0 }
  },
  "tokens": {
    "colors": {
      "tokenName": { "figmaValue": "#hex", "cssVar": "--color-name" }
    },
    "spacing": { },
    "typography": { },
    "radii": { },
    "shadows": { }
  },
  "components": [
    {
      "id": "unique-id",
      "name": "ComponentName",
      "figmaNodeId": "1:234",
      "type": "frame|component|instance|text|etc",
      "bounds": { "x": 0, "y": 0, "width": 0, "height": 0 },
      "styles": {
        "layout": { "mode": "flex", "direction": "column", "gap": 16 },
        "spacing": { "padding": [16, 24, 16, 24] },
        "background": { "color": "#fff", "token": "color/background/primary" },
        "border": { "width": 1, "color": "#e0e0e0", "radius": [8,8,8,8] },
        "typography": { "font": "Inter", "size": 16, "weight": 500, "lineHeight": 24 },
        "shadow": [{ "x": 0, "y": 2, "blur": 4, "color": "rgba(0,0,0,0.1)" }]
      },
      "children": [ /* nested components */ ],
      "mapping": {
        "existingComponent": "Card",
        "props": { "variant": "elevated" },
        "delta": []
      }
    }
  ],
  "assets": {
    "assetId": {
      "name": "icon-name",
      "type": "svg|png|jpg",
      "downloadUrl": "figma CDN url",
      "usage": ["componentId1", "componentId2"]
    }
  },
  "interactions": {
    "notes": "User-provided interaction notes"
  }
}
```
</structure>

<markdown_summary>
The markdown file provides:
- Visual overview (screenshot reference)
- Component inventory with hierarchy
- Token usage summary
- Implementation notes from clarifying questions
- Asset download checklist
</markdown_summary>
</output_format>

<mcp_tools_reference>
**Available Figma MCP Tools**:

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `get_screenshot` | Visual reference image | Always first - verify what you're analyzing |
| `get_design_context` | Code hints, structure, assets | Primary data source for implementation specs |
| `get_variable_defs` | Design tokens (colors, spacing) | Extract design system tokens |
| `get_metadata` | XML structure overview | Drilling into complex nested layouts |
| `get_code_connect_map` | Component-to-code mappings | When Figma has Code Connect configured |
| `whoami` | Verify authentication | If permission errors occur |

**Always provide**: `fileKey`, `nodeId`, `clientLanguages`, `clientFrameworks`
</mcp_tools_reference>

<anti_patterns>
- **Don't guess measurements** - Always extract exact values from Figma
- **Don't skip variable extraction** - Design tokens enable consistent theming
- **Don't assume responsive behavior** - Ask about mobile/tablet adaptations
- **Don't document states you can't see** - Ask about hover/active/disabled states
- **Don't ignore Code Connect** - If configured, it provides authoritative component mappings
</anti_patterns>

<success_criteria>
- Generated spec includes all visible elements with exact measurements
- Design tokens extracted and mapped to CSS custom properties
- Component hierarchy accurately reflects Figma structure
- User's clarifying answers incorporated into spec
- Existing project components mapped where applicable
- Assets listed with download URLs
- Spec is sufficient for pixel-perfect implementation without returning to Figma
</success_criteria>

<reference_guides>
**For complex scenarios**: See [references/advanced-analysis.md](references/advanced-analysis.md)
- Handling component variants
- Responsive design documentation
- Multi-frame/prototype analysis
- Design system alignment strategies
</reference_guides>
