---
description: 'Display current moon phase with detailed ASCII art and lunar information'
allowed-tools: Skill(show-moon-phase)
---

<objective>
Delegate moon phase display to the show-moon-phase skill for: $ARGUMENTS

This routes to specialized skill containing astronomy calculations, ASCII art generation, and comprehensive lunar data workflows.
</objective>

<process>
1. Use Skill tool to invoke show-moon-phase skill
2. Pass user's request: $ARGUMENTS
3. Let skill handle Skyfield setup, calculations, and visualization
</process>

<success_criteria>
- Skill successfully invoked
- Current moon phase displayed with detailed ASCII art
- Illumination percentage, lunar age, and next events shown
- Location-specific moonrise/moonset times calculated
</success_criteria>
