# Home Assistant Automations Reference

## Contents
- [Syntax Migration (2024+)](#syntax-migration-2024)
- [Automation Structure](#automation-structure)
- [Automation Modes](#automation-modes)
- [Trigger Types](#trigger-types)
- [Conditions](#conditions)
- [Actions & Scripts](#actions--scripts)
- [Templates (Jinja2)](#templates-jinja2)
- [Blueprints](#blueprints)
- [REST & WebSocket API](#rest--websocket-api)
- [Family Use Cases](#family-use-cases)
- [Debugging](#debugging)

---

## Syntax Migration (2024+)

| Old key | New key | Notes |
|---------|---------|-------|
| `trigger:` (top level) | `triggers:` | Old syntax still works, don't generate it |
| `condition:` | `conditions:` | |
| `action:` | `actions:` | |
| `service:` (in actions) | `action:` | Renamed 2024.8 |
| `platform:` (inside trigger) | `trigger:` | Inside trigger blocks |

Automation editor auto-migrates to new syntax on save.

---

## Automation Structure

```yaml
automation:
  - id: "unique_snake_case_id"          # Required for UI editor
    alias: "Human Readable Name"
    description: "Why this exists"
    initial_state: true                  # Force enable/disable at startup
    mode: single                         # single|restart|queued|parallel
    max: 10                              # For queued/parallel only
    max_exceeded: warning
    trace:
      stored_traces: 10                  # Debug history
    variables:
      threshold: 25                      # Template-accessible
    trigger_variables:
      sensor_id: "abc"                   # Limited use: only for triggers
    triggers:
      - trigger: ...
    conditions:
      - condition: ...
    actions:
      - action: ...
```

---

## Automation Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `single` (default) | Ignores new triggers while running | Most automations |
| `restart` | Cancels current run, starts fresh | Motion light timers |
| `queued` | Queues runs, processes sequentially | Sequential operations |
| `parallel` | Runs simultaneously, up to `max` | Independent tasks |

---

## Trigger Types

```yaml
triggers:
  # State change
  - trigger: state
    entity_id: binary_sensor.motion_living
    to: "on"
    from: "off"               # Optional
    for:
      minutes: 5              # Must stay in state for duration

  # Numeric threshold
  - trigger: numeric_state
    entity_id: sensor.power_w
    above: 3000
    below: 5000               # Both optional

  # Fixed time
  - trigger: time
    at: "07:00:00"

  # Time pattern (every 30min)
  - trigger: time_pattern
    minutes: "/30"
    hours: "/1"               # Every hour

  # Sun
  - trigger: sun
    event: sunset             # sunset|sunrise
    offset: "-00:30:00"       # Before sunset

  # Reactive template (fires when becomes true)
  - trigger: template
    value_template: "{{ states('sensor.temp') | float > 25 }}"

  # Webhook (external POST)
  - trigger: webhook
    webhook_id: "secret-id"
    allowed_methods: [POST, PUT]

  # MQTT
  - trigger: mqtt
    topic: "home/sensor/temp"
    payload: "on"             # Optional filter

  # HA startup
  - trigger: homeassistant
    event: start              # start|shutdown

  # Calendar
  - trigger: calendar
    entity_id: calendar.family
    event: start
```

---

## Conditions

```yaml
conditions:
  - condition: state
    entity_id: person.john
    state: "home"

  - condition: numeric_state
    entity_id: sensor.humidity
    below: 60

  - condition: time
    after: "07:00:00"
    before: "23:00:00"
    weekday: [mon, tue, wed, thu, fri]

  - condition: sun
    after: sunset
    before: sunrise

  - condition: template
    value_template: "{{ is_state('input_boolean.guest_mode', 'off') }}"

  # Logic
  - condition: or
    conditions:
      - condition: state
        entity_id: person.john
        state: "home"
      - condition: state
        entity_id: person.jane
        state: "home"
```

---

## Actions & Scripts

```yaml
actions:
  # Call a service/action
  - action: light.turn_on
    target:
      entity_id: light.living_room
      area_id: living_room      # Target whole area
    data:
      brightness_pct: 80
      color_temp: 370

  # Delay
  - delay:
      minutes: 5

  # Wait for condition
  - wait_template: "{{ is_state('cover.garage', 'closed') }}"
    timeout:
      seconds: 30
    continue_on_timeout: false

  # Wait for trigger
  - wait_for_trigger:
      - trigger: state
        entity_id: binary_sensor.door
        to: "off"
        for:
          minutes: 2

  # Conditional
  - if:
      - condition: state
        entity_id: sun.sun
        state: "below_horizon"
    then:
      - action: light.turn_on
        target:
          entity_id: light.porch
    else:
      - action: light.turn_off
        target:
          entity_id: light.porch

  # Choose (multi-branch)
  - choose:
      - conditions:
          - condition: time
            after: "22:00:00"
        sequence:
          - action: light.turn_on
            data:
              brightness_pct: 10
      - conditions:
          - condition: time
            after: "06:00:00"
        sequence:
          - action: light.turn_on
            data:
              brightness_pct: 80
    default:
      - action: light.turn_on

  # Repeat
  - repeat:
      count: 3
      sequence:
        - action: notify.mobile_app_phone
          data:
            message: "Alert!"
        - delay:
            seconds: 5

  # Parallel
  - parallel:
      - action: light.turn_off
        target:
          area_id: bedroom
      - action: climate.set_preset_mode
        data:
          preset_mode: away

  # Send notification
  - action: notify.mobile_app_iphone
    data:
      title: "Motion Detected"
      message: "Motion in {{ trigger.to_state.attributes.friendly_name }}"
```

Scripts vs Automations vs Scenes:
| Type | Trigger | Best For |
|------|---------|----------|
| `automation` | Events automatically | Reactive behavior |
| `script` | Manual / called | Reusable sequences |
| `scene` | Manual / called | Snapshot states |

---

## Templates (Jinja2)

```yaml
# State
"{{ states('sensor.temperature') }}"
"{{ states('sensor.temp') | float(0) }}"
"{{ is_state('person.john', 'home') }}"

# Attributes
"{{ state_attr('light.living', 'brightness') | int(0) }}"
"{{ state_attr('climate.living', 'current_temperature') }}"

# Time
"{{ now().hour >= 22 or now().hour < 6 }}"
"{{ now().strftime('%H:%M') }}"
"{{ (now() - states.sensor.motion.last_changed).total_seconds() > 300 }}"

# Area entities
"{{ area_entities('Living Room') | selectattr('domain','eq','light') | list }}"
"{{ expand(area_entities('Living Room')) | selectattr('state','eq','on') | list }}"

# Ternary
"{{ iif(is_state('sun.sun', 'above_horizon'), 'day', 'night') }}"

# Guard unavailable
"{{ states('sensor.temp') not in ['unavailable','unknown'] and states('sensor.temp') | float > 20 }}"

# Trigger context (inside automation)
"{{ trigger.to_state.state }}"
"{{ trigger.to_state.attributes.friendly_name }}"
"{{ trigger.entity_id }}"
```

---

## Blueprints

```yaml
blueprint:
  name: "Motion-Activated Light"
  description: "Turn on light on motion, off after delay"
  domain: automation
  input:
    motion_sensor:
      name: Motion Sensor
      selector:
        entity:
          domain: binary_sensor
          device_class: motion
    light_target:
      name: Light(s)
      selector:
        target:
          entity:
            domain: light
    off_delay:
      name: Off Delay (minutes)
      default: 5
      selector:
        number:
          min: 1
          max: 60
          unit_of_measurement: min

variables:
  delay: !input off_delay    # MUST expose !input as variable before use in templates

triggers:
  - trigger: state
    entity_id: !input motion_sensor
    to: "on"

actions:
  - action: light.turn_on
    target: !input light_target
  - wait_for_trigger:
      - trigger: state
        entity_id: !input motion_sensor
        to: "off"
        for:
          minutes: "{{ delay }}"
  - action: light.turn_off
    target: !input light_target

mode: restart
```

Key selector types: `entity`, `target`, `device`, `area`, `number`, `boolean`, `select`, `time`, `duration`, `text`, `action`, `trigger`, `condition`, `color_temp`, `color_rgb`, `template`

---

## REST & WebSocket API

### REST (all endpoints need `Authorization: Bearer <token>`)

```bash
BASE="https://<ha>"
HDR="Authorization: Bearer $TOKEN"

# Get states
curl -H "$HDR" $BASE/api/states
curl -H "$HDR" $BASE/api/states/light.living_room

# Call service
curl -X POST -H "$HDR" -H "Content-Type: application/json" \
  -d '{"entity_id":"light.living_room","brightness_pct":80}' \
  $BASE/api/services/light/turn_on

# Render template
curl -X POST -H "$HDR" -H "Content-Type: application/json" \
  -d '{"template":"{{ states(\"sensor.temp\") }}°C"}' \
  $BASE/api/template

# History
curl -H "$HDR" "$BASE/api/history/period?filter_entity_id=sensor.temp&minimal_response"
```

### WebSocket

```json
// Connect: ws://<ha>/api/websocket
// Receive: {"type":"auth_required"}
// Send auth:
{"type":"auth","access_token":"<token>"}
// Receive: {"type":"auth_ok"}

// Subscribe to events
{"id":1,"type":"subscribe_events","event_type":"state_changed"}

// Call service
{"id":2,"type":"call_service","domain":"light","service":"turn_on",
 "target":{"entity_id":"light.living_room"},"service_data":{"brightness_pct":80}}

// Get states
{"id":3,"type":"get_states"}

// Render template
{"id":4,"type":"render_template","template":"{{ states('sensor.temp') }}"}
```

---

## Family Use Cases

### Presence Detection (Best Practice)
```yaml
# Use person entity (aggregates multiple trackers)
triggers:
  - trigger: state
    entity_id: person.john, person.jane
    to: "home"
conditions:
  - condition: template
    value_template: "{{ trigger.to_state.state == 'home' }}"
actions:
  - action: script.welcome_home
    data:
      who: "{{ trigger.to_state.attributes.friendly_name }}"
```

### Motion Light with Lux Threshold
```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.motion_kitchen
    to: "on"
conditions:
  - condition: numeric_state
    entity_id: sensor.kitchen_illuminance
    below: 50                  # Only activate when dark
  - condition: time
    after: "06:00:00"
    before: "23:00:00"
actions:
  - action: light.turn_on
    target:
      entity_id: light.kitchen
    data:
      brightness_pct: 90
  - wait_for_trigger:
      - trigger: state
        entity_id: binary_sensor.motion_kitchen
        to: "off"
        for:
          minutes: 3
  - action: light.turn_off
    target:
      entity_id: light.kitchen
mode: restart
```

### Everyone Left Home
```yaml
triggers:
  - trigger: state
    entity_id: group.all_people
    to: "not_home"
    for:
      minutes: 2
actions:
  - action: climate.set_preset_mode
    target:
      entity_id: climate.thermostat
    data:
      preset_mode: away
  - action: light.turn_off
    target:
      area_id: all
  - action: alarm_control_panel.alarm_arm_away
    target:
      entity_id: alarm_control_panel.home
```

---

## Debugging

- **Trace viewer**: Developer Tools → Automations → trace icon
- **Template editor**: Developer Tools → Template (live preview)
- **Log book**: Settings → System → Logs
- Set `stored_traces: 20` to keep more trace history
- Use `trigger.description` in notifications to identify which trigger fired
