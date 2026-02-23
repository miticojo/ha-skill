# HA MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server that wraps the Home Assistant REST API,
giving Claude Code direct read/write access to your HA instance — no manual copy-paste required.

## Setup (3 commands)

```bash
# 1. Copy env template and fill in your details
cp .env.example .env
# Edit .env: set HA_URL and HA_TOKEN

# 2. Install Python deps
pip install -r requirements.txt

# 3. Register with Claude Code
bash install.sh
```

> **HA_TOKEN**: In HA go to *Profile → Security → Long-lived access tokens → Create token*.

## Available tools (17)

### Entities & States
| Tool | What it does |
|------|-------------|
| `ha_get_states(domain?)` | List entities with entity_id + state, optionally filtered by domain |
| `ha_get_state(entity_id)` | Full state + all attributes for one entity |
| `ha_search_entities(query)` | Search by friendly name or entity_id substring |
| `ha_get_areas()` | List all areas with area_id and name |
| `ha_call_service(domain, service, data?)` | Call any HA service |
| `ha_render_template(template)` | Render a Jinja2 template in live HA context |
| `ha_set_state(entity_id, state, attributes?)` | Write an entity state directly (ephemeral; for virtual sensors / testing) |

### Automations
| Tool | What it does |
|------|-------------|
| `ha_automation_upsert(id, alias, triggers, actions, …)` | Create or update an automation — reloads automatically, no restart needed |
| `ha_automation_get(id)` | Read the stored config of an automation by its config `id` |
| `ha_automation_delete(id)` | Delete an automation by config `id` and reload |
| `ha_automation_reload()` | Reload all automations from disk |

### Helper Entities
| Tool | What it does |
|------|-------------|
| `ha_helper_upsert(domain, obj_id, name, icon?, extra?)` | Create or update an `input_boolean`, `input_datetime`, `input_number`, etc. via the HA storage API. Returns a ready-to-paste YAML snippet if YAML mode is detected. |
| `ha_helper_delete(domain, obj_id)` | Delete a storage-managed helper entity |

### Lovelace Dashboards
| Tool | What it does |
|------|-------------|
| `ha_get_dashboards()` | List all dashboards with id, title, url_path |
| `ha_get_lovelace(dashboard_id?)` | Read a dashboard config (default if omitted) |
| `ha_save_lovelace(config, dashboard_id?)` | Overwrite a dashboard config |
| `ha_get_lovelace_resources()` | List custom cards / HACS resources |

## Verification

After `bash install.sh`, open Claude and run:

```
ha_get_states("light")          # → list of lights with states
ha_get_lovelace()               # → default dashboard config
ha_render_template("{{ states('sun.sun') }}")   # → "above_horizon"
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Missing env vars` on startup | Check `.env` has `HA_URL` and `HA_TOKEN` |
| `401 Unauthorized` | Token is wrong or expired — create a new one in HA |
| SSL error with self-signed cert | Server uses `verify=False`; ensure HA_URL uses `https://` |
| `ha-mcp` not in `claude mcp list` | Re-run `bash install.sh` |

## Requirements

- Python 3.10+
- Home Assistant 2023.4+ (REST API required)
- Claude Code CLI
