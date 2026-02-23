# Home Assistant Helpers, Reload & Safe Refactoring

## Contents
- [Helper Entity Decision Matrix](#helper-entity-decision-matrix)
- [Reload vs Restart](#reload-vs-restart)
- [Safe Entity Refactoring](#safe-entity-refactoring)

---

## Helper Entity Decision Matrix

**Rule**: always prefer a native helper or statistical function over a template sensor when one exists. Template sensors bypass HA's built-in validation and fail silently.

### Which helper to use

| Need | Helper / Integration | Notes |
|------|---------------------|-------|
| Track min/max/mean of a sensor over time | `min_max` helper | `entity_ids`, `type: min/max/mean/median/range/sum` |
| Detect when a value crosses a threshold | `threshold` binary sensor | `lower`/`upper`, optional `hysteresis` |
| Calculate rate of change (W→kW/h, L→L/min) | `derivative` sensor | `unit_time: h/min/s`, `time_window` |
| Track cumulative energy / utility consumption | `utility_meter` | Supports `cycle: daily/weekly/monthly`, tariff periods |
| Percentage of time in a state (% motion active today) | `history_stats` sensor | `type: ratio`, `duration`, or `count` |
| Running total / counter | `counter` helper | Simple increment/decrement via service |
| Boolean toggle (persistent across restart) | `input_boolean` | Prefer over `variable` for persistent flags |
| Store a number (persistent) | `input_number` | `min`, `max`, `step`, `mode: slider/box` |
| Store a text value | `input_text` | Use `input_select` when values are enumerated |
| Group lights/switches for joint control | `light group` / `switch group` | `platform: group` in config, or via UI |
| Virtual thermostat from a heater + sensor | `generic_thermostat` | `heater`, `target_sensor`, `min/max_temp` |
| Combine binary sensors (any/all on) | `binary_sensor group` | `all_entities_on` to require unanimous state |
| Trending sensor (rising/falling/stable) | `trend` binary sensor | `sample_duration`, `min_gradient` |
| Track person location changes | `person` + `zone` | Never use raw `device_tracker` in automations |

### Configuration examples

```yaml
# min_max: track temperature across rooms
sensor:
  - platform: min_max
    name: "House Temperature Average"
    type: mean
    round_digits: 1
    entity_ids:
      - sensor.bedroom_temperature
      - sensor.living_temperature
      - sensor.kitchen_temperature

# threshold: binary sensor for high power draw
binary_sensor:
  - platform: threshold
    name: "High Power Draw"
    entity_id: sensor.power_consumption_w
    upper: 3000
    hysteresis: 100        # won't flip back until drops below 2900

# derivative: calculate power from energy sensor
sensor:
  - platform: derivative
    name: "Power from Energy"
    source: sensor.energy_kwh
    unit_time: h           # kWh/h = kW
    time_window: "00:05:00"

# utility_meter: daily energy tracking with tariff
utility_meter:
  energy_daily:
    source: sensor.grid_import_kwh
    cycle: daily
    tariffs:
      - peak
      - offpeak

# history_stats: % of time motion active today
sensor:
  - platform: history_stats
    name: "Motion Active Today"
    entity_id: binary_sensor.motion_living
    state: "on"
    type: ratio
    start: "{{ now().replace(hour=0, minute=0, second=0) }}"
    end: "{{ now() }}"
```

### When templates ARE appropriate

Use a template sensor only when no native helper matches:

```yaml
# ✅ Template is appropriate: complex multi-entity derived value
template:
  - sensor:
      - name: "House Comfort Score"
        unit_of_measurement: "%"
        state: >
          {% set temp_ok = is_state_attr('climate.living', 'current_temperature') | float(20) | between(20, 24) %}
          {% set humidity_ok = states('sensor.living_humidity') | float(50) | between(40, 60) %}
          {{ (temp_ok | int + humidity_ok | int) * 50 }}

# ❌ Template not needed: use min_max instead
template:
  - sensor:
      - name: "Average Temp"  # BAD — use min_max platform
        state: >
          {{ ((states('sensor.temp_a') | float + states('sensor.temp_b') | float) / 2) | round(1) }}
```

---

## Reload vs Restart

**Rule**: always reload the minimum scope. A full HA restart interrupts automations, drops WebSocket connections, and takes 30–90 seconds.

### Reload decision matrix

| Changed | Reload service | Full restart needed? |
|---------|---------------|----------------------|
| Automations YAML | `automation.reload` | No |
| Scripts YAML | `script.reload` | No |
| Scenes YAML | `scene.reload` | No |
| Groups YAML | `group.reload` | No |
| Template sensors/binary sensors | `template.reload` | No |
| Input helpers (input_boolean, etc.) | `input_boolean.reload` / `input_number.reload` etc. | No |
| Themes | `frontend.reload_themes` | No |
| Core `configuration.yaml` includes | `homeassistant.reload_config_entry` (specific integration) or `homeassistant.reload_all` | No |
| Added a new HACS integration | Restart required | **Yes** |
| Added a new `custom_component` | Restart required | **Yes** |
| Changed `configuration.yaml` top-level keys (not includes) | Restart required | **Yes** |
| Changed secrets.yaml | Restart required | **Yes** |

### Reload via automation / script

```yaml
# Reload automations after editing
actions:
  - action: automation.reload

# Reload a specific integration's config entry
actions:
  - action: homeassistant.reload_config_entry
    target:
      entity_id: sensor.my_integration_sensor  # any entity from that integration

# Check config validity before restart (from terminal / SSH)
# ha core check     → validates config
# ha core restart   → only if check passes
```

### Check config without restarting (Developer Tools)

`Developer Tools → YAML → Check Configuration` — validates all YAML before applying.

Also callable via REST:
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" https://<ha>/api/config/core/check_config
```

---

## Safe Entity Refactoring

Renaming or removing an entity breaks everything that references it silently. Follow this checklist before any entity rename or deletion.

### 5-step pre-rename checklist

```
Pre-rename checklist for: <entity_id>
- [ ] 1. Find all automations referencing it
- [ ] 2. Find all scripts referencing it
- [ ] 3. Find all dashboard cards referencing it
- [ ] 4. Find all template sensors referencing it
- [ ] 5. Update all references, then rename
```

### Search patterns (from HA config folder via SSH or File Editor)

```bash
# SSH into HA or use Studio Code Server add-on

# Search automations, scripts, scenes
grep -r "old_entity_id" /config/automations.yaml
grep -r "old_entity_id" /config/scripts.yaml
grep -r "old_entity_id" /config/scenes.yaml

# Search dashboard YAML (Lovelace stored as files)
grep -r "old_entity_id" /config/ui-lovelace.yaml
grep -r "old_entity_id" /config/lovelace/

# Search template sensors and binary sensors
grep -r "old_entity_id" /config/configuration.yaml
grep -r "old_entity_id" /config/templates/

# Search all YAML files recursively
grep -r "old_entity_id" /config/ --include="*.yaml"
```

### Entity rename strategy (zero-downtime)

When renaming a critical entity (e.g., `sensor.old_name` → `sensor.new_name`):

1. **Add the new entity** alongside the old one (if it's a template/helper, create both)
2. **Update all references** to use `new_name` (automations, dashboards, scripts)
3. **Test** that everything works with `new_name`
4. **Remove the old entity**
5. **Reload** the appropriate domains (`automation.reload`, `template.reload`, etc.)

### Entity ID stability (custom integrations)

In custom integrations, entity ID is derived from `unique_id`. Set it once and never change it:

```python
class MySensor(CoordinatorEntity, SensorEntity):
    @property
    def unique_id(self) -> str:
        # Never change this — it anchors the entity_id forever
        return f"{self._device_id}_temperature"
```

If you must change a `unique_id`, use a [migration in the config entry](https://developers.home-assistant.io/docs/entity_registry_index/) to avoid creating orphaned entities.

### Entity registry cleanup

After removing an old entity, orphaned registry entries appear in `Settings → Devices & Services → Entities` (filter by "Unavailable"). Clean them up to prevent clutter and false alerts.
