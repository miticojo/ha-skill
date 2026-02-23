---
name: ha-dev
description: >
  Expert Home Assistant (HA) developer skill for building automations, beautiful dashboards (desktop + mobile),
  AI agent integration via MCP, and custom integrations. Activates when working on Home Assistant topics:
  Lovelace dashboards, YAML automations, Blueprints, HACS custom cards (Mushroom, Bubble Card, card-mod),
  MCP/AI agent integration, custom components, ESPHome, or the Assist voice pipeline.
  Covers 2024–2026 HA ecosystem with modern syntax, best practices, and family-friendly UX patterns.
---

# Home Assistant Expert Developer

Assists with all Home Assistant development using 2024–2026 best practices. Always uses modern syntax.
Always thinks mobile-first and family-friendly. Prefers local-first solutions.

## Core Principles

- **Modern syntax always**: `triggers:` / `actions:` / `action:` (not `service:` / `platform:`)
- **Local-first**: prefer Ollama + home-llm over cloud LLMs where possible
- **Family UX**: every dashboard works on all ages, on desktop + mobile
- **MCP-first AI**: connect AI agents via official MCP Server (`/api/mcp`)
- **HACS for UI**: custom cards and themes via HACS, not manual installs

## Quick Orientation

| Task | Where to look |
|------|---------------|
| MCP Server, AI integration, Assist pipeline | [reference/mcp.md](reference/mcp.md) |
| Automations, Blueprints, templates, API | [reference/automations.md](reference/automations.md) |
| Dashboards, cards, themes, mobile | [reference/dashboards.md](reference/dashboards.md) |
| Custom integrations, add-ons | [reference/integrations.md](reference/integrations.md) |
| Helper entities, reload vs restart, safe refactoring | [reference/helpers-and-ops.md](reference/helpers-and-ops.md) |

## Critical Gotchas (Read Before Generating Code)

1. **Old syntax trap**: AI often generates old HA syntax. Always convert:
   `service:` → `action:` | `trigger:` (top) → `triggers:` | `platform:` → `trigger:` (inside block)

2. **Blueprint `!input` in templates**: expose as `variables:` first — `{{ !input x }}` never works in templates:
   ```yaml
   variables:
     delay: !input delay_minutes  # then use {{ delay }} in templates
   ```

3. **Bubble Card pop-ups**: MUST be placed LAST in the view YAML or they break

4. **MCP entity visibility**: only entities "Exposed" in `Settings → Voice Assistants → Exposed Entities` appear as MCP tools

5. **Automation mode for motion lights**: use `restart` (not `single`) so new motion resets the timer

6. **Unavailable guard**: always guard sensor templates:
   `{{ states('sensor.temp') not in ['unavailable','unknown'] and ... }}`

7. **MCP + stdio clients** (Cursor): requires `mcp-proxy` bridge — official HA MCP is Streamable HTTP only

8. **card-mod Shadow DOM**: use `$` to pierce shadow boundaries:
   ```yaml
   card_mod:
     style:
       .: |
         ha-card { border-radius: 20px; }
       ha-tile-icon$: |
         div { color: red; }
   ```

9. **Presence detection**: use `person` entity + `zone`, not raw `device_tracker`

10. **HA version gates**: MCP from 2025.2+ | Sections dashboard from 2024.3+ | AI Tasks from 2025.8+
    Always check user's HA version for version-gated features.

## Core Architecture (Quick Reference)

```
homeassistant.core.HomeAssistant (hass)
├── hass.bus     — Event Bus (pub/sub, fires state_changed, call_service, ...)
├── hass.states  — State Machine (all entity states + attributes)
├── hass.services — Service Registry
└── Timer        — fires time_changed every second (asyncio single-threaded loop)

Entity ID: <domain>.<object_id>  e.g. light.living_room, sensor.temp_bedroom
```

Key domains: `light`, `switch`, `sensor`, `binary_sensor`, `climate`, `media_player`,
`cover`, `person`, `zone`, `automation`, `script`, `scene`, `input_*`, `timer`, `counter`, `calendar`, `todo`

## Essential Automation Template (Always Start Here)

```yaml
automation:
  - id: "unique_snake_case_id"
    alias: "Human Readable Name"
    description: "Why this exists"
    mode: single          # single|restart|queued|parallel
    triggers:
      - trigger: state
        entity_id: binary_sensor.motion_living
        to: "on"
    conditions:
      - condition: time
        after: "07:00:00"
        before: "23:00:00"
    actions:
      - action: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness_pct: 80
```

## Essential Dashboard Stack

Install via HACS in this order: `card-mod` → `lovelace-mushroom` → `Bubble-Card` → `lovelace-auto-entities` → `apexcharts-card`

Recommended per use case:
- **Family**: Sections + Tile + Mushroom + Material Rounded theme
- **Power user**: Sections + Mushroom + card-mod + Catppuccin theme
- **Tablet wall**: Bubble Card bottom nav + pop-ups + Fully Kiosk Browser

## Connect AI Agent to Home Assistant (MCP)

```bash
# AI Code CLI
claude mcp add --transport http --url https://<your-ha>/api/mcp home-assistant
```

For full MCP setup, auth, available tools, and third-party implementations → [reference/mcp.md](reference/mcp.md)

## Key Resources

- Developer docs: https://developers.home-assistant.io/
- MCP Server docs: https://www.home-assistant.io/integrations/mcp_server/
- Blueprint Exchange: https://community.home-assistant.io/c/blueprints-exchange/
- Awesome HA: https://github.com/frenck/awesome-home-assistant
- Top repos: mushroom (4.8K★), Bubble-Card (4K★), ha-mcp (902★), home-llm (1.2K★), HACS (7K★)
