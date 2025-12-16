---
description: Analyze Figma design URL and produce detailed implementation spec
argument-hint: <figma-url>
allowed-tools: Skill(analyze-figma-design), mcp__figma__get_screenshot, mcp__figma__get_design_context, mcp__figma__get_variable_defs, mcp__figma__get_metadata, mcp__figma__get_code_connect_map, mcp__figma__whoami, AskUserQuestion, Write, Edit, Read, Glob, Grep
---

<objective>
Analyze a Figma design and produce a detailed, structured specification for pixel-perfect implementation.

Figma URL: $ARGUMENTS

This routes to the analyze-figma-design skill which contains patterns for extracting design data via Figma MCP tools.
</objective>

<process>
1. Use Skill tool to invoke analyze-figma-design skill
2. Follow the skill's workflow to analyze the provided Figma URL
3. Ask clarifying questions about component mapping, responsive behavior, and states
4. Generate structured JSON spec and markdown summary
5. Save output files to appropriate location
</process>

<success_criteria>
- Complete design spec generated with all measurements
- Design tokens extracted and mapped
- Component hierarchy documented
- User clarifications incorporated
- Output files saved and ready for implementation
</success_criteria>
