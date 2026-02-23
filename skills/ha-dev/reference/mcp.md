# Home Assistant MCP Server Reference

## Contents
- [Architecture](#architecture)
- [Enable & Configure](#enable--configure)
- [Connect AI Clients](#connect-ai-clients)
- [Exposed Tools](#exposed-tools)
- [HA as MCP Client](#ha-as-mcp-client)
- [Third-Party MCP Servers](#third-party-mcp-servers)
- [Assist Pipeline & AI Tasks](#assist-pipeline--ai-tasks)
- [Local LLM Setup](#local-llm-setup)

---

## Architecture

HA 2025.2 (Feb 5, 2025) ships both roles simultaneously:

```
External AI Clients (Cursor, Copilot, etc.)
        ↓  POST /api/mcp  (Streamable HTTP)
   HA MCP Server  →  Assist Intent System  →  Exposed Entities

HA Assist Agent
        ↓  SSE transport
   External MCP Servers (memory, web search, etc.)
```

- **`mcp_server`** integration: HA as MCP server (`/api/mcp`)
- **`mcp`** integration: HA Assist as MCP client consuming external servers
- HA 2025.5: multiple MCP servers per conversation agent

---

## Enable & Configure

```
Settings → Devices & Services → Add Integration → "Model Context Protocol Server"
Settings → Voice Assistants → Exposed Entities  ← toggles what AI can control
```

Option available: "Control Home Assistant" toggle (read-only if disabled).

Auth options:
- **OAuth 2.0 / IndieAuth** (recommended): no pre-registration. Client ID = base URL of redirect URI
- **Long-Lived Access Token**: Profile → Security → Long-lived access tokens (shown once, 10y validity)

---

## Connect AI Clients

### AI Code CLI
```bash
# OAuth (interactive browser popup)
claude mcp add --transport http --url https://<your-ha>/api/mcp home-assistant

# Long-lived token (simpler for automation)
claude mcp add --transport http \
  --header "Authorization: Bearer <token>" \
  --url https://<your-ha>/api/mcp home-assistant
```

### Desktop AI Client
```json
{
  "mcpServers": {
    "home-assistant": {
      "url": "https://<your-ha>/api/mcp",
      "transport": "http",
      "auth": { "type": "oauth", "clientId": "https://claude.ai" }
    }
  }
}
```

### Cursor / stdio-only clients
Requires `mcp-proxy` to bridge stdio ↔ Streamable HTTP:
```bash
pip install mcp-proxy
# Cursor MCP config:
# command: mcp-proxy
# args: ["https://<ha>/api/mcp"]
# env: { "MCP_PROXY_AUTH_TOKEN": "<token>" }
```

### HA as MCP Client (add tools to Assist)
```bash
# Bridge stdio MCP server to SSE for HA to consume
uv tool install git+https://github.com/allenporter/mcp-proxy.git
mcp-proxy --sse-port 42783 -- uvx mcp-server-fetch

# Then in HA: Settings → Integrations → Add → "Model Context Protocol"
# SSE Server URL: http://127.0.0.1:42783/sse
```

---

## Exposed Tools

All tools via the Assist intent system. Only entities listed in "Exposed Entities" are accessible.

| Tool | Description |
|------|-------------|
| `HassTurnOn` / `HassTurnOff` | Control any entity by name or area |
| `HassLightSet` | Brightness, color temp, RGB |
| `HassGetState` | Query entity state |
| `HassListEntities` | List with filters |
| `HassClimateSetTemperature` | Thermostat target |
| `HassClimateGetTemperature` | Read temperature |
| `HassFanSetSpeed` | Fan speed |
| `HassMediaPause/Unpause/Next/Previous` | Media control |
| `HassSetVolume` / `HassSetVolumeRelative` | Volume |
| `HassMediaPlayerMute/Unmute` | Mute |
| `HassMediaSearchAndPlay` | Search and play |
| `HassTimerStart/Cancel` | Timer management |
| `HassShoppingListAdd` | Shopping list |
| `HassGetWeather` | Weather query |
| `HassSetPosition` | Cover/blind 0–100% |

**Not implemented**: Resources, Sampling, Notifications in official server.

---

## Third-Party MCP Servers (more powerful)

### homeassistant-ai/ha-mcp (902★, 97+ tools)
Full entity control, history, templates, automations. Supports Gemini CLI, ChatGPT, VSCode, Cursor, 15+ clients.
Install via HACS → Integrations → ha-mcp.

### voska/hass-mcp (275★)
Focused, clean. Good AI Code CLI support.
```bash
# Install as HA add-on or run externally
# Config: HASS_URL + HASS_TOKEN env vars
```

---

## Assist Pipeline & AI Tasks

### Assist Pipeline Stages
```
Wake Word → STT → Intent Recognition → TTS
                         ↓
           Rule-based Assist  OR  LLM Agent (any provider / Ollama)
                                         ↓
                                  Native Intents + MCP Tools
```

Key milestones:
- **2025.7**: Voice questions (AI asks clarifying questions)
- **2025.8**: Streaming TTS (~0.5s first audio, was ~7s), AI Tasks, OpenRouter (400+ models)
- **2025.11**: Multilingual, dual wake word

### AI Tasks Framework (2025.8+)
Async AI-powered tasks running in background:
```yaml
actions:
  - action: conversation.process
    data:
      text: "Generate a weekly energy report and notify me"
      agent_id: conversation.openai  # or any configured LLM agent
```

---

## Local LLM Setup

### home-llm + Ollama (1.2K★)
```
HACS → Integrations → home-llm
Settings → Voice Assistants → Add Agent → home-llm
```
Models: `home-3b-v3` (RPi5/NUC), `home-1b-v3` (lighter).
Fine-tuned specifically for HA entity control — works fully offline.

### extended_openai_conversation
For function-calling with any OpenAI-compatible endpoint (Ollama, LM Studio, OpenRouter).
HACS → Integrations → extended_openai_conversation.
