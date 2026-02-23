# Home Assistant Custom Integration Development Reference

## Contents
- [File Structure](#file-structure)
- [manifest.json](#manifestjson)
- [\_\_init\_\_.py Pattern](#__init__py-pattern)
- [DataUpdateCoordinator](#dataupdatecoordinator)
- [Config Flow](#config-flow)
- [Entity Platforms](#entity-platforms)
- [Services / Actions](#services--actions)
- [Supervisor Add-on (AI Agent)](#supervisor-add-on-ai-agent)
- [Boilerplate & Tools](#boilerplate--tools)

---

## File Structure

```
custom_components/<domain>/
├── __init__.py         # async_setup_entry / async_unload_entry
├── manifest.json       # Integration metadata
├── config_flow.py      # UI configuration wizard (ConfigFlow)
├── coordinator.py      # DataUpdateCoordinator for polling
├── sensor.py           # Sensor platform
├── switch.py           # Switch platform
├── light.py            # Light platform (etc.)
├── strings.json        # UI translations (en)
└── services.yaml       # Service descriptions
```

---

## manifest.json

```json
{
  "domain": "my_integration",
  "name": "My Integration",
  "version": "1.0.0",
  "codeowners": ["@yourgithub"],
  "requirements": ["my-python-lib==1.2.3"],
  "dependencies": [],
  "after_dependencies": ["mqtt"],
  "iot_class": "local_polling",
  "integration_type": "device",
  "config_flow": true,
  "documentation": "https://github.com/you/my_integration"
}
```

`iot_class` values:
| Value | Description |
|-------|-------------|
| `local_polling` | Polls local device |
| `local_push` | Device pushes updates |
| `cloud_polling` | Polls cloud API |
| `cloud_push` | Cloud pushes updates |
| `calculated` | Derived from other entities |
| `assumed_state` | State is assumed, not known |

`integration_type`: `device` | `service` | `helper` | `system` | `hub` | `virtual`

---

## \_\_init\_\_.py Pattern

```python
from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .coordinator import MyCoordinator

PLATFORMS: list[str] = ["sensor", "switch", "binary_sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from config entry."""
    coordinator = MyCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()  # Raises ConfigEntryNotReady on failure
    entry.runtime_data = coordinator                       # Store coordinator on entry (HA 2024.4+)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload on options update."""
    await hass.config_entries.async_reload(entry.entry_id)
```

---

## DataUpdateCoordinator

Standard polling pattern — all platform entities share one coordinator.

```python
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed
from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)

class MyCoordinator(DataUpdateCoordinator[dict]):
    """Coordinate data updates for all entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="My Integration",
            update_interval=timedelta(seconds=30),
        )
        self.api = MyApiClient(
            host=entry.data["host"],
            token=entry.data["token"],
        )
        self.entry = entry

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        try:
            return await self.api.fetch_all()
        except ApiAuthError as err:
            raise ConfigEntryAuthFailed("Auth failed, re-auth required") from err
        except ApiConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
```

### Entity Using Coordinator
```python
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class MySensor(CoordinatorEntity[MyCoordinator], SensorEntity):
    """Sensor entity backed by coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MyCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_temperature"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name="My Device",
            manufacturer="ACME",
            model="Sensor v2",
        )

    @property
    def native_value(self) -> float | None:
        """Return sensor value from coordinator data."""
        return self.coordinator.data.get(self._device_id, {}).get("temperature")

    @property
    def native_unit_of_measurement(self) -> str:
        return UnitOfTemperature.CELSIUS
```

---

## Config Flow

```python
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
import voluptuous as vol

class MyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config entry setup wizard."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_connection(user_input["host"], user_input["token"])
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                # Prevent duplicate entries
                await self.async_set_unique_id(user_input["host"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input["host"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("token"): str,
                vol.Optional("scan_interval", default=30): int,
            }),
            errors=errors,
        )
```

---

## Entity Platforms

Key entity base classes and their required properties:

```python
# Sensor
class MySensor(SensorEntity):
    native_value: StateType           # Current value
    native_unit_of_measurement: str   # "°C", "W", "kWh"...
    device_class: SensorDeviceClass   # temperature, power, energy...
    state_class: SensorStateClass     # measurement, total, total_increasing

# Binary Sensor
class MyBinarySensor(BinarySensorEntity):
    is_on: bool
    device_class: BinarySensorDeviceClass  # motion, door, window, smoke...

# Switch
class MySwitch(SwitchEntity):
    is_on: bool
    async def async_turn_on(self, **kwargs) -> None: ...
    async def async_turn_off(self, **kwargs) -> None: ...

# Light
class MyLight(LightEntity):
    is_on: bool
    brightness: int | None            # 0-255
    color_temp_kelvin: int | None
    color_mode: ColorMode
    supported_color_modes: set[ColorMode]
    async def async_turn_on(self, **kwargs) -> None: ...
    async def async_turn_off(self, **kwargs) -> None: ...
```

---

## Services / Actions

```python
# Register a custom service in async_setup_entry
async def async_setup_entry(hass, entry):
    ...
    async def handle_my_service(call: ServiceCall) -> None:
        entity_id = call.data["entity_id"]
        value = call.data["value"]
        # do something

    hass.services.async_register(
        DOMAIN,
        "my_service",
        handle_my_service,
        schema=vol.Schema({
            vol.Required("entity_id"): cv.entity_id,
            vol.Required("value"): vol.All(vol.Coerce(int), vol.Range(0, 100)),
        }),
    )
```

`services.yaml` (for UI description):
```yaml
my_service:
  name: My Service
  description: Does something useful
  fields:
    entity_id:
      name: Entity
      description: The entity to control
      required: true
      selector:
        entity:
          domain: sensor
    value:
      name: Value
      description: 0–100
      required: true
      selector:
        number:
          min: 0
          max: 100
```

---

## Supervisor Add-on (AI Agent)

Run an AI agent or custom service as a native HA add-on (appears in sidebar).

### config.yaml (add-on metadata)
```yaml
name: "My AI Agent"
version: "1.0.0"
slug: "my_ai_agent"
description: "AI automation agent for Home Assistant"
arch: [aarch64, amd64, armv7]
startup: application
boot: auto
watchdog: http://[HOST]:8080/healthz
hassio_api: true              # Access Supervisor REST API
homeassistant_api: true       # Access HA REST API
ingress: true                 # Web UI via HA sidebar
ingress_port: 8080
ports:
  8080/tcp: null              # null = not exposed externally (ingress only)
options: {}
schema: {}
map:
  - share:rw
  - config:ro
```

### Calling HA API from Add-on
```python
import os, httpx

HA_URL = "http://supervisor/core/api"
TOKEN = os.environ["SUPERVISOR_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

async def get_states():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{HA_URL}/states", headers=HEADERS)
        return r.json()

async def call_service(domain, service, data):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{HA_URL}/services/{domain}/{service}",
            headers=HEADERS, json=data
        )
        return r.json()
```

### Add-on Repository Structure
```
my-addon-repo/
├── repository.yaml           # repo metadata
└── my_ai_agent/
    ├── config.yaml
    ├── Dockerfile
    ├── run.sh
    └── src/
        └── agent.py
```

---

## Boilerplate & Tools

- **Official blueprint**: https://github.com/ludeeus/integration_blueprint (562★)
  Start here — includes CI, translations, config flow, coordinator
- **AI-assisted blueprint**: https://github.com/jpawlowski/hacs.integration_blueprint
  Modern `uv`-based workflow, AI/Copilot integration
- **Dev container**: HA provides a `.devcontainer` setup for VS Code
- **Hassfest**: `python -m script.hassfest` validates manifest.json
- **pytest-homeassistant-custom-component**: testing framework for custom integrations
