# 🏠 Home Assistant Dev Skill

> The most comprehensive agent skill for Home Assistant — automations, beautiful dashboards, AI/MCP integration, custom components, and operational best practices. All in one.

[![Install with npx skills](https://img.shields.io/badge/install%20with-npx%20skills-black?style=for-the-badge&logo=npm)](https://skills.sh)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-orange?style=for-the-badge)](https://skills.sh)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024--2026-41BDF5?style=for-the-badge&logo=home-assistant)](https://home-assistant.io)

---

## Install

```bash
npx skills add miticojo/ha-skill
```

Install globally (available across all projects):

```bash
npx skills add -g miticojo/ha-skill
```

Then invoke it:

```
/ha-dev
```

---

## What It Does

Once installed, your AI agent becomes an expert Home Assistant developer with deep 2024–2026 ecosystem knowledge. It will:

- **Always generate correct 2024+ syntax** — `triggers:` / `actions:` / `action:` — never the old `service:` / `platform:` patterns that AI models still get wrong
- **Apply 10 critical gotchas proactively** — Bubble Card pop-up ordering, Blueprint `!input` in templates, MCP entity exposure, motion light mode, card-mod shadow DOM, and more
- **Design family-friendly dashboards** — every UI works for all ages, on desktop and mobile
- **Connect AI agents to HA via MCP** — official MCP Server setup for the AI Code CLI, Desktop clients, Cursor, and 15+ MCP clients
- **Pick the right tool for the job** — native helper entities over template sensors, correct reload scope over full restart
- **Load only what's needed** — progressive disclosure keeps context lean; reference files load on demand

---

## Coverage

| Area | Reference File | What's Included |
|------|---------------|-----------------|
| **MCP & AI** | `reference/mcp.md` | Official MCP Server (HA 2025.2+), AI Code CLI / Desktop / Cursor setup, OAuth + token auth, 97-tool alternatives (ha-mcp, voska/hass-mcp), Assist pipeline stages, AI Tasks (2025.8+), local LLM via home-llm + Ollama |
| **Automations** | `reference/automations.md` | 2024+ syntax migration table, all trigger/condition/action types, automation modes, Blueprints with full selector reference, Jinja2 template cheat sheet, REST & WebSocket API with curl examples, family use cases (presence, lighting, energy, climate) |
| **Dashboards** | `reference/dashboards.md` | Sections view (default since 2024.3), Tile card, Mushroom (17 card types), Bubble Card pop-ups + bottom nav, card-mod CSS engine with shadow DOM, Auto-Entities, ApexCharts, mini-graph-card, top themes (Catppuccin, Material Rounded, visionOS), mobile-first + tablet wall panel patterns |
| **Custom Integrations** | `reference/integrations.md` | File structure, manifest.json fields, `__init__.py` config entry pattern, DataUpdateCoordinator, Config Flow wizard, entity platforms (sensor, switch, light, binary_sensor), service registration, Supervisor add-on authoring with `SUPERVISOR_TOKEN` API access |
| **Helpers & Ops** | `reference/helpers-and-ops.md` | Helper entity decision matrix (min_max, threshold, derivative, utility_meter, history_stats, counter, input_*), native-over-template rule with examples, reload vs restart decision table, 5-step safe entity refactoring checklist |

---

## Example Sessions

**Connect your AI agent to Home Assistant via MCP:**
```
You:   "How do I connect my AI agent to Home Assistant?"

Agent: [reads reference/mcp.md]
       → Explains HA 2025.2+ MCP Server at /api/mcp
       → Provides exact CLI command with OAuth or token auth
       → Notes the mcp-proxy requirement for Cursor
```

**Build a family dashboard:**
```
You:   "Create a dashboard for lights, climate and presence. Must work on phone."

Agent: [reads reference/dashboards.md]
       → Full Sections + Mushroom chips header + Bubble Card pop-ups YAML
       → Recommends Material Rounded theme + Fully Kiosk for tablet
       → Flags: pop-ups must be placed last in view YAML
```

**Write a bulletproof automation:**
```
You:   "Turn off all lights when everyone leaves home for 5+ minutes"

Agent: [uses SKILL.md built-in knowledge]
       → Correct 2024+ syntax with person entity + zone
       → area_id targeting instead of listing entity_ids
       → for: {minutes: 5} dict format, mode: single
```

**Choose the right helper entity:**
```
You:   "I want a sensor showing the average temperature across all rooms"

Agent: [reads reference/helpers-and-ops.md]
       → Recommends min_max helper (type: mean) over a template sensor
       → Explains why: templates fail silently, min_max has built-in validation
       → Provides complete YAML with entity_ids list
```

**Build a custom integration:**
```
You:   "Create a custom HA integration for my local IoT API"

Agent: [reads reference/integrations.md]
       → Full file structure: __init__.py, manifest.json, coordinator.py, sensor.py
       → DataUpdateCoordinator polling pattern with ConfigEntryAuthFailed handling
       → Config Flow with validation and unique_id deduplication
```

---

## Requirements

| Requirement | Notes |
|------------|-------|
| AI coding agent | Any agent supporting the [Agent Skills spec](https://skills.sh) |
| Home Assistant 2024.x+ | Sections dashboard requires 2024.3+, MCP Server requires 2025.2+, AI Tasks require 2025.8+ |
| HACS | Required for Mushroom, Bubble Card, card-mod, and other custom cards |

---

## File Structure

```
skills/ha-dev/
├── SKILL.md                   # Core — loaded when HA topic detected (134 lines)
├── LICENSE.txt
└── reference/
    ├── mcp.md                 # MCP Server, Assist pipeline, local LLM (179 lines)
    ├── automations.md         # YAML syntax, blueprints, API (485 lines)
    ├── dashboards.md          # Cards, themes, mobile (486 lines)
    ├── integrations.md        # Custom components, add-ons (364 lines)
    └── helpers-and-ops.md     # Helper entities, reload, refactoring (221 lines)
```

`SKILL.md` loads only when an HA topic is detected. Reference files load on demand — the agent reads only the file relevant to the current request.

---

## Contributing

Corrections, new patterns, and additional reference files are welcome — open an issue or PR.

---

## License

MIT — see [skills/ha-dev/LICENSE.txt](skills/ha-dev/LICENSE.txt)
