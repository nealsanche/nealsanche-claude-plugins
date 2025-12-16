<objective>
Advanced patterns for analyzing complex Figma designs including component variants, responsive layouts, multi-frame prototypes, and design system alignment.
</objective>

<component_variants>
<detection>
When `get_design_context` returns component instances, check for:
- Variant properties (size, state, type variations)
- Boolean properties (showIcon, disabled)
- Instance swaps (different icon options)

**In the spec, document**:
```json
{
  "component": "Button",
  "variants": {
    "size": ["sm", "md", "lg"],
    "variant": ["primary", "secondary", "ghost"],
    "state": ["default", "hover", "active", "disabled"]
  },
  "defaultVariant": {
    "size": "md",
    "variant": "primary",
    "state": "default"
  }
}
```
</detection>

<multi_variant_analysis>
When the user provides multiple variant frames:

1. Analyze each variant frame separately
2. Identify which properties change between variants
3. Document the delta per variant
4. Generate a unified component spec with all variants

**Workflow**:
```
For each variant frame URL:
  1. get_design_context → extract specs
  2. Compare to base variant
  3. Note style differences as variant-specific overrides
```
</multi_variant_analysis>
</component_variants>

<responsive_design>
<extracting_constraints>
Use `get_metadata` to understand constraint systems:
- Fixed vs. flexible sizing
- Min/max constraints
- Percentage-based sizing
- Auto-layout grow/shrink behavior

**Document responsive behavior**:
```json
{
  "responsive": {
    "strategy": "fluid|adaptive|fixed",
    "breakpoints": [
      { "name": "mobile", "maxWidth": 767, "layout": "single-column" },
      { "name": "tablet", "minWidth": 768, "maxWidth": 1023, "layout": "two-column" },
      { "name": "desktop", "minWidth": 1024, "layout": "three-column" }
    ],
    "containerBehavior": {
      "maxWidth": 1200,
      "centering": true,
      "padding": { "mobile": 16, "tablet": 24, "desktop": 32 }
    }
  }
}
```
</extracting_constraints>

<multi_breakpoint_frames>
When Figma contains frames for multiple breakpoints:

1. Identify breakpoint frames by name (often "Mobile", "Tablet", "Desktop")
2. Analyze each with `get_design_context`
3. Cross-reference components across breakpoints
4. Document layout transformations
5. Note any components that hide/show at certain breakpoints
</multi_breakpoint_frames>
</responsive_design>

<prototype_analysis>
<interaction_flows>
If the design is part of a prototype:

1. Ask user if they want interaction flows documented
2. Request related frame URLs for the flow
3. Analyze each state/frame
4. Document transitions and triggers

**Interaction spec format**:
```json
{
  "interactions": [
    {
      "trigger": "click",
      "element": "Submit Button",
      "action": "navigate",
      "destination": "Success Modal",
      "animation": {
        "type": "fade",
        "duration": 200,
        "easing": "ease-out"
      }
    }
  ]
}
```
</interaction_flows>

<state_documentation>
For components with multiple states (not visible in single frame):

**Ask the user**:
- "Can you provide the Figma URL for the hover state?"
- "Are there error/validation state frames?"
- "Is there a loading state for this component?"

**Document states as variants**:
```json
{
  "component": "TextField",
  "states": {
    "default": { "borderColor": "#e0e0e0" },
    "focused": { "borderColor": "#2196f3", "shadow": "0 0 0 2px rgba(33,150,243,0.2)" },
    "error": { "borderColor": "#f44336" },
    "disabled": { "background": "#f5f5f5", "opacity": 0.6 }
  }
}
```
</state_documentation>
</prototype_analysis>

<design_system_alignment>
<token_mapping_strategy>
When mapping Figma variables to project tokens:

1. **Extract Figma tokens** via `get_variable_defs`
2. **Scan project** for existing design tokens (CSS custom properties, theme files)
3. **Create mapping table**:

```json
{
  "tokenMapping": {
    "figma": {
      "color/primary/500": "#2196f3"
    },
    "project": {
      "--color-primary": "#2196f3"
    },
    "status": "exact-match"
  }
}
```

**Status values**:
- `exact-match` - Values identical
- `close-match` - Within acceptable tolerance (e.g., #2196f3 vs #2194f1)
- `mismatch` - Values differ significantly, document delta
- `new` - Figma token has no project equivalent
</token_mapping_strategy>

<component_library_alignment>
When project has existing component library:

1. **Identify design element type** (button, card, input, etc.)
2. **Check project components** for similar patterns
3. **Compare specifications**:
   - Size/dimensions match?
   - Color tokens align?
   - Spacing follows same scale?

**Output alignment report**:
```json
{
  "alignment": {
    "figmaComponent": "Call to Action Button",
    "projectMatch": "Button",
    "confidence": "high",
    "propMapping": {
      "variant": "primary",
      "size": "lg"
    },
    "discrepancies": [
      {
        "property": "border-radius",
        "figma": "16px",
        "project": "12px",
        "recommendation": "Update project component OR accept deviation"
      }
    ]
  }
}
```
</component_library_alignment>
</design_system_alignment>

<complex_layouts>
<auto_layout_extraction>
Auto-layout in Figma maps to CSS flexbox:

| Figma Property | CSS Equivalent |
|---------------|----------------|
| Direction: Vertical | flex-direction: column |
| Direction: Horizontal | flex-direction: row |
| Primary axis: Space between | justify-content: space-between |
| Primary axis: Center | justify-content: center |
| Counter axis: Center | align-items: center |
| Gap | gap |
| Padding | padding |
| Hug contents | width: fit-content |
| Fill container | flex: 1 |
| Fixed | width: [value]px |

**Extract and document**:
```json
{
  "layout": {
    "display": "flex",
    "flexDirection": "column",
    "justifyContent": "space-between",
    "alignItems": "stretch",
    "gap": 16,
    "padding": [24, 16, 24, 16]
  }
}
```
</auto_layout_extraction>

<grid_layouts>
For grid-based layouts:

1. Identify grid structure from Figma
2. Document columns, rows, gaps
3. Note which elements span multiple cells

```json
{
  "grid": {
    "display": "grid",
    "columns": "repeat(3, 1fr)",
    "gap": { "row": 24, "column": 16 },
    "items": [
      { "id": "header", "gridColumn": "1 / -1" },
      { "id": "sidebar", "gridRow": "2 / 4" }
    ]
  }
}
```
</grid_layouts>
</complex_layouts>

<asset_handling>
<image_extraction>
From `get_design_context`, extract asset download URLs:

```json
{
  "assets": {
    "hero-image": {
      "type": "image",
      "format": "png",
      "dimensions": { "width": 800, "height": 600 },
      "downloadUrl": "https://figma-alpha-api.s3...",
      "usage": "Background image in Hero section",
      "optimization": "Consider WebP, lazy loading"
    }
  }
}
```

**Asset checklist for spec**:
- All images with download URLs
- SVG icons (request SVG format when available)
- Fonts used (with fallback recommendations)
- Any embedded media
</image_extraction>

<icon_handling>
For icons:

1. Check if icon is from a known icon library (Lucide, Heroicons, etc.)
2. If library icon, document library name and icon name
3. If custom, include download URL

```json
{
  "icon": {
    "name": "arrow-right",
    "source": "lucide-react",
    "size": 24,
    "color": "currentColor"
  }
}
```
</icon_handling>
</asset_handling>

<validation_checklist>
Before finalizing complex design specs:

- [ ] All component variants documented with delta from base
- [ ] Responsive behavior specified for all breakpoints
- [ ] Interaction states documented (even if from user input, not Figma)
- [ ] Token mapping complete with alignment status
- [ ] Auto-layout/grid translated to CSS equivalents
- [ ] All assets listed with download URLs
- [ ] Discrepancies from project design system noted
- [ ] Implementation notes from user clarifications included
</validation_checklist>
