"""
ha_mcp.py — FastMCP server wrapping the Home Assistant REST + WebSocket APIs.

Provides 18 tools for querying entities, rendering templates, calling
services, managing automations & helper entities, reading/writing Lovelace
dashboards, and reading Alarmo alarm configuration.

Transport strategy:
  - Most reads/writes use the REST API (httpx).
  - Lovelace config, helper creation, and Alarmo config require the
    WebSocket API (this HA instance returns 404 on the REST equivalents).
    _ws_call() handles a single-shot authenticated WS request automatically.

Config (env vars or .env file):
    HA_URL   = https://homeassistant.local:8123
    HA_TOKEN = <long-lived access token>
"""

import os
import ssl
import json
from typing import Optional

import httpx
import websockets
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

HA_URL = os.getenv("HA_URL", "").rstrip("/")
TOKEN = os.getenv("HA_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# WebSocket URL derived from HA_URL (https → wss, http → ws)
_WS_URL = HA_URL.replace("https://", "wss://").replace("http://", "ws://") + "/api/websocket"

mcp = FastMCP("ha-mcp")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


async def _get(path: str, timeout: float = 10.0) -> dict | list:
    url = f"{HA_URL}{path}"
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        try:
            r = await client.get(url, headers=HEADERS)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            return {"error": str(e), "status_code": e.response.status_code}
        except Exception as e:
            return {"error": str(e)}


async def _post(path: str, data: dict, timeout: float = 10.0) -> dict | list:
    url = f"{HA_URL}{path}"
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        try:
            r = await client.post(url, headers=HEADERS, json=data)
            r.raise_for_status()
            # Some HA endpoints return plain text (e.g. /api/template)
            content_type = r.headers.get("content-type", "")
            if "application/json" in content_type:
                return r.json()
            return {"result": r.text}
        except httpx.HTTPStatusError as e:
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text
            return {"error": str(e), "status_code": e.response.status_code, "detail": body}
        except Exception as e:
            return {"error": str(e)}


async def _put(path: str, data: dict, timeout: float = 10.0) -> dict | list:
    url = f"{HA_URL}{path}"
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        try:
            r = await client.put(url, headers=HEADERS, json=data)
            r.raise_for_status()
            content_type = r.headers.get("content-type", "")
            if "application/json" in content_type:
                return r.json()
            return {"result": r.text}
        except httpx.HTTPStatusError as e:
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text
            return {"error": str(e), "status_code": e.response.status_code, "detail": body}
        except Exception as e:
            return {"error": str(e)}


async def _delete(path: str, timeout: float = 10.0) -> dict:
    url = f"{HA_URL}{path}"
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        try:
            r = await client.delete(url, headers=HEADERS)
            r.raise_for_status()
            return {"result": "ok"}
        except httpx.HTTPStatusError as e:
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text
            return {"error": str(e), "status_code": e.response.status_code, "detail": body}
        except Exception as e:
            return {"error": str(e)}


# ---------------------------------------------------------------------------
# WebSocket helper
# ---------------------------------------------------------------------------


async def _ws_call(msg_type: str, **kwargs) -> dict | list:
    """
    Single-shot authenticated WebSocket call to HA.

    Connects, authenticates, sends one message, returns the result, closes.
    Use for endpoints not available over REST (Lovelace config, helper
    creation, Alarmo config, etc.).
    """
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    use_ssl = _WS_URL.startswith("wss://")

    try:
        async with websockets.connect(
            _WS_URL, ssl=ssl_ctx if use_ssl else None
        ) as ws:
            # Auth handshake
            await ws.recv()  # auth_required
            await ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
            auth = json.loads(await ws.recv())
            if auth.get("type") != "auth_ok":
                return {"error": "WS auth failed", "detail": auth}

            # Send command
            msg = {"id": 1, "type": msg_type, **kwargs}
            await ws.send(json.dumps(msg))
            resp = json.loads(await ws.recv())

            if resp.get("success"):
                result = resp.get("result")
                return result if result is not None else {"result": "ok"}
            err = resp.get("error", {})
            return {"error": err.get("message", "Unknown WS error"), "code": err.get("code")}

    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Entity & state tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def ha_get_states(domain: Optional[str] = None) -> list[dict]:
    """
    Return all entity states, optionally filtered by domain.

    Args:
        domain: HA domain to filter by (e.g. 'light', 'switch', 'sensor').
                Omit to get every entity.

    Returns:
        List of {entity_id, state, attributes} dicts.
    """
    raw = await _get("/api/states")
    if isinstance(raw, dict) and "error" in raw:
        return [raw]
    entities = raw if isinstance(raw, list) else []
    if domain:
        entities = [e for e in entities if e.get("entity_id", "").startswith(f"{domain}.")]
    return [
        {
            "entity_id": e.get("entity_id"),
            "state": e.get("state"),
            "attributes": e.get("attributes", {}),
        }
        for e in entities
    ]


@mcp.tool()
async def ha_get_state(entity_id: str) -> dict:
    """
    Return the full state (including all attributes) for a single entity.

    Args:
        entity_id: The entity to query, e.g. 'light.living_room'.

    Returns:
        {entity_id, state, attributes, last_changed, last_updated} or {error}.
    """
    result = await _get(f"/api/states/{entity_id}")
    if isinstance(result, dict) and "error" in result:
        return result
    return {
        "entity_id": result.get("entity_id"),
        "state": result.get("state"),
        "attributes": result.get("attributes", {}),
        "last_changed": result.get("last_changed"),
        "last_updated": result.get("last_updated"),
    }


@mcp.tool()
async def ha_search_entities(query: str) -> list[dict]:
    """
    Search entities by friendly name or entity_id (case-insensitive substring).

    Args:
        query: Search string, e.g. 'living room' or 'sensor.temp'.

    Returns:
        Matching entities as {entity_id, state, friendly_name}.
    """
    raw = await _get("/api/states")
    if isinstance(raw, dict) and "error" in raw:
        return [raw]
    q = query.lower()
    results = []
    for e in raw if isinstance(raw, list) else []:
        eid = e.get("entity_id", "")
        fname = e.get("attributes", {}).get("friendly_name", "")
        if q in eid.lower() or q in fname.lower():
            results.append(
                {
                    "entity_id": eid,
                    "state": e.get("state"),
                    "friendly_name": fname,
                }
            )
    return results


@mcp.tool()
async def ha_get_areas() -> list[dict]:
    """
    Return all areas defined in Home Assistant.

    Returns:
        List of {area_id, name} dicts.
    """
    template = "{{ areas() | tojson }}"
    result = await _post("/api/template", {"template": template})
    if "error" in result:
        return [result]
    try:
        area_ids = json.loads(result.get("result", "[]"))
    except (json.JSONDecodeError, TypeError):
        return [{"error": f"Could not parse areas: {result}"}]

    areas = []
    for aid in area_ids:
        name_tpl = f"{{{{ area_name('{aid}') }}}}"
        name_result = await _post("/api/template", {"template": name_tpl})
        areas.append({"area_id": aid, "name": name_result.get("result", aid)})
    return areas


@mcp.tool()
async def ha_call_service(domain: str, service: str, data: Optional[dict] = None) -> dict:
    """
    Call any Home Assistant service.

    Args:
        domain:  Service domain, e.g. 'light', 'switch', 'automation'.
        service: Service name, e.g. 'turn_on', 'toggle', 'reload'.
        data:    Optional service data payload, e.g. {'entity_id': 'light.kitchen'}.

    Returns:
        HA response dict, or {error} on failure.
    """
    result = await _post(f"/api/services/{domain}/{service}", data or {})
    return result if isinstance(result, dict) else {"result": result}


@mcp.tool()
async def ha_render_template(template: str) -> str:
    """
    Render a Jinja2 template in the live HA context.

    Args:
        template: Jinja2 template string, e.g. "{{ states('sun.sun') }}".

    Returns:
        Rendered string, or error message.
    """
    result = await _post("/api/template", {"template": template})
    if "error" in result:
        return f"Error: {result['error']}"
    return result.get("result", "")


# ---------------------------------------------------------------------------
# Lovelace tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def ha_get_dashboards() -> list[dict]:
    """
    Return all Lovelace dashboards defined in HA.

    Returns:
        List of {id, title, url_path, mode} dicts.
    """
    raw = await _get("/api/lovelace/dashboards")
    if isinstance(raw, dict) and "error" in raw:
        return [raw]
    dashboards = raw if isinstance(raw, list) else []
    return [
        {
            "id": d.get("id"),
            "title": d.get("title"),
            "url_path": d.get("url_path"),
            "mode": d.get("mode"),
        }
        for d in dashboards
    ]


@mcp.tool()
async def ha_get_lovelace(dashboard_id: Optional[str] = None) -> dict:
    """
    Read the full YAML/JSON config of a Lovelace dashboard.

    Tries the REST API first; falls back to the WebSocket API automatically
    (required when HA is in storage/UI mode, which returns 404 on REST).

    Args:
        dashboard_id: URL path of the dashboard (e.g. 'lovelace-tablet').
                      Omit (or pass None) for the default dashboard.

    Returns:
        Dashboard config dict, or {error}.
    """
    # REST attempt
    path = f"/api/lovelace/dashboards/{dashboard_id}/config" if dashboard_id else "/api/lovelace/config"
    result = await _get(path)
    if not (isinstance(result, dict) and "error" in result):
        return result

    # WS fallback (storage-mode dashboards)
    kwargs = {"force": False}
    if dashboard_id:
        kwargs["url_path"] = dashboard_id
    return await _ws_call("lovelace/config", **kwargs)


@mcp.tool()
async def ha_save_lovelace(config: dict, dashboard_id: Optional[str] = None) -> dict:
    """
    Save (overwrite) a Lovelace dashboard config.

    Tries the REST API first; falls back to the WebSocket API automatically
    (required when HA is in storage/UI mode).

    Args:
        config:       Full dashboard config as a dict (views, title, etc.).
        dashboard_id: URL path of the dashboard to update.
                      Omit for the default dashboard.

    Returns:
        {result: 'ok'} on success, or {error} on failure.
    """
    # REST attempt
    path = f"/api/lovelace/dashboards/{dashboard_id}/config" if dashboard_id else "/api/lovelace/config"
    result = await _post(path, config, timeout=30.0)
    if not (isinstance(result, dict) and "error" in result):
        return {"result": "ok"}

    # WS fallback
    kwargs: dict = {"config": config}
    if dashboard_id:
        kwargs["url_path"] = dashboard_id
    ws_result = await _ws_call("lovelace/config/save", **kwargs)
    if isinstance(ws_result, dict) and "error" in ws_result:
        return ws_result
    return {"result": "ok"}


@mcp.tool()
async def ha_get_lovelace_resources() -> list[dict]:
    """
    Return all registered Lovelace resources (custom cards, HACS modules).

    Returns:
        List of {id, type, url} dicts.
    """
    raw = await _get("/api/lovelace/resources")
    if isinstance(raw, dict) and "error" in raw:
        return [raw]
    resources = raw if isinstance(raw, list) else []
    return [
        {
            "id": r.get("id"),
            "type": r.get("type"),
            "url": r.get("url"),
        }
        for r in resources
    ]


# ---------------------------------------------------------------------------
# Automation config tools
# ---------------------------------------------------------------------------

_AUTOMATION_CONFIG_BASE = "/api/config/automation/config"


@mcp.tool()
async def ha_automation_upsert(
    id: str,
    alias: str,
    triggers: list[dict],
    actions: list[dict],
    description: str = "",
    mode: str = "single",
    conditions: Optional[list[dict]] = None,
) -> dict:
    """
    Create or update an automation. Stored in automations.yaml and live
    immediately — no HA restart needed (reload is automatic).

    Always use modern HA syntax:
      - triggers use 'trigger:' key  (not 'platform:')
      - actions  use 'action:'  key  (not 'service:')

    Args:
        id:          Unique snake_case config key, e.g. 'lights_off_at_night'.
                     HA derives the entity_id from the alias, not this id.
        alias:       Human-readable name shown in the UI.
        triggers:    List of trigger dicts.
                     Example: [{"trigger": "time", "at": "23:00:00"}]
        actions:     List of action dicts.
                     Example: [{"action": "light.turn_off", "target": {"entity_id": "all"}}]
        description: Optional description (shown in automation editor).
        mode:        'single' | 'restart' | 'queued' | 'parallel'. Default: 'single'.
        conditions:  Optional list of condition dicts. Default: [] (no conditions).

    Returns:
        {'result': 'ok', 'reloaded': True} on success, or {'error': ...}.
    """
    payload = {
        "id":          id,
        "alias":       alias,
        "description": description,
        "mode":        mode,
        "triggers":    triggers,
        "conditions":  conditions or [],
        "actions":     actions,
    }
    result = await _post(f"{_AUTOMATION_CONFIG_BASE}/{id}", payload, timeout=15.0)
    if isinstance(result, dict) and "error" in result:
        return result
    await _post("/api/services/automation/reload", {})
    return {"result": "ok", "reloaded": True}


@mcp.tool()
async def ha_automation_get(id: str) -> dict:
    """
    Return the stored config of an automation by its config id.

    Args:
        id: The automation's config id (snake_case), e.g. 'lights_off_at_night'.
            This is the 'id:' field in the YAML, NOT the entity_id like
            'automation.lights_off_at_night'.

    Returns:
        Full automation config dict, or {'error': ..., 'not_found': True}.
    """
    result = await _get(f"{_AUTOMATION_CONFIG_BASE}/{id}")
    if isinstance(result, dict) and "error" in result:
        result["not_found"] = True
        return result
    return result


@mcp.tool()
async def ha_automation_delete(id: str) -> dict:
    """
    Delete an automation by its config id and reload automations.

    Args:
        id: The automation's config id (snake_case), e.g. 'lights_off_at_night'.

    Returns:
        {'result': 'ok', 'reloaded': True} on success, or {'error': ...}.
    """
    result = await _delete(f"{_AUTOMATION_CONFIG_BASE}/{id}")
    if isinstance(result, dict) and "error" in result:
        return result
    await _post("/api/services/automation/reload", {})
    return {"result": "ok", "reloaded": True}


@mcp.tool()
async def ha_automation_reload() -> dict:
    """
    Reload all automations from disk without restarting Home Assistant.

    Returns:
        {'result': 'ok'} on success, or {'error': ...}.
    """
    result = await _post("/api/services/automation/reload", {})
    if isinstance(result, dict) and "error" in result:
        return result
    return {"result": "ok"}


# ---------------------------------------------------------------------------
# Helper entity tools  (input_boolean, input_datetime, input_number …)
# ---------------------------------------------------------------------------

_HELPER_DOMAINS = frozenset({
    "input_boolean", "input_datetime", "input_number",
    "input_text", "input_select", "counter", "timer",
})

_YAML_MODE_MSG = (
    "The HA storage API for '{domain}' is not available. "
    "Your helpers are likely defined in configuration.yaml (YAML mode). "
    "Add the helper manually to your YAML and reload with "
    "ha_call_service('homeassistant', 'reload_all') or restart HA."
)


@mcp.tool()
async def ha_helper_upsert(
    domain: str,
    obj_id: str,
    name: str,
    icon: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict:
    """
    Create or update a UI helper entity via the HA storage API.

    Works when helpers are managed via the HA UI (storage mode, the default
    for new installations). Returns a descriptive error if your helpers are
    defined in configuration.yaml (YAML mode) — in that case add them to
    the YAML file and reload.

    Args:
        domain:  'input_boolean' | 'input_datetime' | 'input_number' |
                 'input_text' | 'input_select' | 'counter' | 'timer'.
        obj_id:  Unique snake_case id, e.g. 'night_mode_active'.
                 Full entity_id will be '<domain>.<obj_id>'.
        name:    Friendly name shown in the HA UI.
        icon:    Optional MDI icon string, e.g. 'mdi:weather-night'.
        extra:   Optional domain-specific config fields:
                   input_datetime → {'has_time': True, 'has_date': False}
                   input_number   → {'min': 0, 'max': 100, 'step': 1, 'mode': 'slider'}
                   input_select   → {'options': ['option_a', 'option_b']}
                   timer          → {'duration': '00:30:00', 'restore': True}

    Returns:
        {'result': 'ok', 'entity_id': '<domain>.<obj_id>'} on success,
        {'error': ..., 'yaml_mode': True} if YAML mode is detected.
    """
    if domain not in _HELPER_DOMAINS:
        return {"error": f"Unsupported domain '{domain}'. Use one of: {sorted(_HELPER_DOMAINS)}"}

    payload: dict = {"name": name}
    if icon:
        payload["icon"] = icon
    if extra:
        payload.update(extra)

    # Try automation-style upsert (POST with id in URL path)
    result = await _post(f"/api/config/{domain}/config/{obj_id}", payload, timeout=10.0)

    # If that 404s, try storage-collection style (POST to list endpoint with id in body)
    if isinstance(result, dict) and result.get("status_code") == 404:
        payload["id"] = obj_id
        result = await _post(f"/api/config/{domain}/config", payload, timeout=10.0)

    # If still 404, try PUT (update existing storage entity)
    if isinstance(result, dict) and result.get("status_code") == 404:
        result = await _put(f"/api/config/{domain}/config/{obj_id}", payload, timeout=10.0)

    if isinstance(result, dict) and result.get("status_code") == 404:
        # WS fallback: try domain/create then domain/update
        ws_payload: dict = {"name": name}
        if icon:
            ws_payload["icon"] = icon
        if extra:
            ws_payload.update(extra)

        ws_result = await _ws_call(f"{domain}/create", **ws_payload)
        if isinstance(ws_result, dict) and ws_result.get("code") in (
            "entry_exists", "already_exists", "id_exists"
        ):
            # Already exists — update instead (needs object_id)
            ws_result = await _ws_call(f"{domain}/update", object_id=obj_id, **ws_payload)

        if isinstance(ws_result, dict) and "error" in ws_result:
            # WS also failed → YAML mode guidance
            return {
                "error": _YAML_MODE_MSG.format(domain=domain),
                "yaml_mode": True,
                "yaml_snippet": _yaml_helper_snippet(domain, obj_id, name, icon, extra),
            }

        created_id = ws_result.get("id") if isinstance(ws_result, dict) else obj_id
        return {"result": "ok", "entity_id": f"{domain}.{created_id}"}

    if isinstance(result, dict) and "error" in result:
        return result

    return {"result": "ok", "entity_id": f"{domain}.{obj_id}"}


@mcp.tool()
async def ha_helper_delete(domain: str, obj_id: str) -> dict:
    """
    Delete a UI helper entity via the HA storage API.

    Args:
        domain: Helper domain (e.g. 'input_boolean').
        obj_id: Object id to delete (e.g. 'night_mode_active').

    Returns:
        {'result': 'ok'} on success, or {'error': ...}.
    """
    if domain not in _HELPER_DOMAINS:
        return {"error": f"Unsupported domain '{domain}'."}
    return await _delete(f"/api/config/{domain}/config/{obj_id}")


def _yaml_helper_snippet(
    domain: str,
    obj_id: str,
    name: str,
    icon: Optional[str],
    extra: Optional[dict],
) -> str:
    """Return a YAML snippet the user can paste into configuration.yaml."""
    lines = [f"{domain}:", f"  {obj_id}:", f"    name: \"{name}\""]
    if icon:
        lines.append(f"    icon: {icon}")
    if extra:
        for k, v in extra.items():
            lines.append(f"    {k}: {json.dumps(v)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# State write tool
# ---------------------------------------------------------------------------


@mcp.tool()
async def ha_set_state(
    entity_id: str,
    state: str,
    attributes: Optional[dict] = None,
) -> dict:
    """
    Directly write an entity state via the HA REST API.

    Useful for:
    - External / virtual sensors (e.g. sensor.my_custom_value)
    - Forcing a state to test automations
    - Resetting a value when service calls are unavailable

    NOTE: States written this way are ephemeral — they survive until the next
    HA restart or until the owning integration overwrites them. For persistent
    helpers use ha_helper_upsert instead.

    Args:
        entity_id:  Entity to update, e.g. 'sensor.outdoor_temp'.
        state:      New state string, e.g. '23.5', 'on', 'home'.
        attributes: Optional dict of attributes to write alongside the state.

    Returns:
        {'result': 'ok', 'entity_id': ..., 'state': ...} on success,
        or {'error': ...}.
    """
    payload: dict = {"state": state}
    if attributes:
        payload["attributes"] = attributes
    result = await _post(f"/api/states/{entity_id}", payload)
    if isinstance(result, dict) and "error" in result:
        return result
    return {"result": "ok", "entity_id": entity_id, "state": state}


# ---------------------------------------------------------------------------
# Alarmo alarm system tools
# ---------------------------------------------------------------------------

_ALARMO_CATEGORIES = ("sensors", "config", "areas", "automations", "users")


@mcp.tool()
async def ha_alarmo_get(category: str) -> dict | list:
    """
    Read Alarmo alarm-system configuration via the WebSocket API.

    Args:
        category: One of 'sensors' | 'config' | 'areas' | 'automations' | 'users'.
                  - sensors:     All configured sensors with modes, delays, enabled flag.
                  - config:      Global settings (code policy, MQTT, master area).
                  - areas:       Area definitions with armed_away / armed_home timing.
                  - automations: Internal Alarmo notification/action automations.
                  - users:       Configured users and their permissions.

    Returns:
        Dict (or list) with the requested Alarmo configuration, or {error}.
    """
    if category not in _ALARMO_CATEGORIES:
        return {"error": f"Invalid category '{category}'. Use one of: {_ALARMO_CATEGORIES}"}
    return await _ws_call(f"alarmo/{category}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not HA_URL or not TOKEN:
        raise SystemExit(
            "Missing env vars. Copy .env.example to .env and fill in HA_URL and HA_TOKEN."
        )
    mcp.run(transport="stdio")
