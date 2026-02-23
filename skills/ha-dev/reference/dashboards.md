# Home Assistant Dashboard Reference

## Contents
- [Layout System](#layout-system)
- [Sections View (Default)](#sections-view-default)
- [Tile Card (Native)](#tile-card-native)
- [Mushroom Cards](#mushroom-cards)
- [Bubble Card](#bubble-card)
- [Card-Mod CSS Engine](#card-mod-css-engine)
- [Auto-Entities](#auto-entities)
- [Charts & Graphs](#charts--graphs)
- [Themes](#themes)
- [Mobile & Responsive](#mobile--responsive)
- [Stack Recommendations](#stack-recommendations)

---

## Layout System

```
Dashboard
└── Views (type: sections | masonry | panel | sidebar)
    └── Sections (columns, title)
        └── Cards
```

| View Type | Best For |
|-----------|----------|
| `sections` | Modern structured layouts (default since 2024.3) |
| `masonry` | Quick setup, legacy configs |
| `panel` | Single full-screen card (cameras, maps) |
| `sidebar` | Multi-room navigation |

Grid spec (2024.7): 56px rows, 36px icons, 42px feature height, 8px gutter.

### HACS Install Order (critical — card-mod first)
1. `card-mod` (dependency for many cards)
2. `lovelace-mushroom`
3. `Bubble-Card`
4. `lovelace-auto-entities`
5. `apexcharts-card`
6. `mini-graph-card` (optional, for quick trend lines)

---

## Sections View (Default)

```yaml
views:
  - title: Home
    type: sections
    max_columns: 3
    dense_section_placement: true    # Fill gaps automatically
    sections:
      - title: Lights
        column_span: 1               # 1-3 columns
        cards:
          - type: tile
            entity: light.living_room
      - title: Climate
        column_span: 2
        cards:
          - type: tile
            entity: climate.thermostat
```

---

## Tile Card (Native)

HA's recommended card for Sections view. Use for most standard entity control.

```yaml
type: tile
entity: light.living_room
name: "Living Room"
color: amber                         # All 24 color tokens available
icon: mdi:ceiling-light
tap_action:
  action: toggle
hold_action:
  action: more-info
double_tap_action:
  action: navigate
  navigation_path: "#living-room"
features:
  - type: light-brightness
  - type: light-color-temp
  - type: climate-hvac-modes    # For climate entities
  - type: cover-open-close      # For covers
  - type: vacuum-commands       # For vacuums
hide_state: false
```

Color tokens: `primary`, `accent`, `red`, `pink`, `purple`, `deep-purple`, `indigo`, `blue`, `light-blue`, `cyan`, `teal`, `green`, `light-green`, `lime`, `yellow`, `amber`, `orange`, `deep-orange`, `brown`, `grey`, `blue-grey`, `black`, `white`, `disabled`

---

## Mushroom Cards

GitHub: https://github.com/piitaya/lovelace-mushroom (4.8K★)

### Chips Header (Status Bar)
```yaml
type: custom:mushroom-chips-card
chips:
  - type: weather
    entity: weather.home
    show_temperature: true
    show_conditions: true
  - type: entity
    entity: person.john
    icon_color: green
    content_info: state
  - type: template
    content: "{{ states('sensor.energy_today') }} kWh"
    icon: mdi:lightning-bolt
    icon_color: amber
    tap_action:
      action: navigate
      navigation_path: /lovelace/energy
  - type: alarm-control-panel
    entity: alarm_control_panel.home
```

### Room Navigation Card
```yaml
type: custom:mushroom-template-card
primary: Living Room
secondary: >
  {{ state_attr('climate.living', 'current_temperature') }}°C ·
  {{ expand(area_entities('Living Room')) | selectattr('state','eq','on') |
     selectattr('domain','eq','light') | list | count }} lights on
icon: mdi:sofa
icon_color: >
  {% if expand(area_entities('Living Room')) | selectattr('domain','eq','light') |
     selectattr('state','eq','on') | list | count > 0 %}amber{% else %}disabled{% endif %}
fill_container: true
tap_action:
  action: navigate
  navigation_path: "#living-room"
```

### Light Card
```yaml
type: custom:mushroom-light-card
entity: light.living_room
show_brightness_control: true
show_color_temp_control: true
show_color_control: true
collapsible_controls: true
```

### All 17 Mushroom Card Types
`mushroom-alarm-control-panel-card`, `mushroom-climate-card`, `mushroom-chips-card`,
`mushroom-cover-card`, `mushroom-entity-card`, `mushroom-fan-card`,
`mushroom-humidifier-card`, `mushroom-light-card`, `mushroom-lock-card`,
`mushroom-media-player-card`, `mushroom-number-card`, `mushroom-person-card`,
`mushroom-plant-card`, `mushroom-select-card`, `mushroom-template-card`,
`mushroom-title-card`, `mushroom-update-card`

---

## Bubble Card

GitHub: https://github.com/Clooos/Bubble-Card (4K★)
**Pop-up driven UX with URL hash navigation. ⚠️ Pop-ups MUST be placed LAST in view YAML.**

### Pop-up Definition (place at end of view)
```yaml
type: custom:bubble-card
card_type: pop-up
hash: "#living-room"
name: Living Room
icon: mdi:sofa
width_desktop: 600px           # Optional width override
margin_top_mobile: 50px
cards:
  - type: tile
    entity: light.living_room
  - type: custom:mushroom-climate-card
    entity: climate.living
  - type: custom:mini-graph-card
    entity: sensor.living_temperature
```

### Navigation Button (opens pop-up)
```yaml
type: custom:bubble-card
card_type: button
name: Living Room
icon: mdi:sofa
entity: light.living_room     # Optional: shows state color
tap_action:
  action: navigate
  navigation_path: "#living-room"
```

### Bottom Navigation Bar
```yaml
type: custom:bubble-card
card_type: horizontal-buttons-stack
auto_order: true               # Sort by active state
buttons:
  - name: Home
    icon: mdi:home
    tap_action:
      action: navigate
      navigation_path: /lovelace/home
  - name: Living
    icon: mdi:sofa
    entity: light.living_group
    tap_action:
      action: navigate
      navigation_path: "#living-room"
  - name: Bedroom
    icon: mdi:bed
    entity: light.bedroom_group
    tap_action:
      action: navigate
      navigation_path: "#bedroom"
  - name: Kitchen
    icon: mdi:countertop
    entity: light.kitchen
    tap_action:
      action: navigate
      navigation_path: "#kitchen"
```

---

## Card-Mod CSS Engine

GitHub: https://github.com/thomasloven/lovelace-card-mod (1.6K★)
Injects CSS into any Lovelace card. Can use Jinja2 for state-based styles.

### Basic Styling
```yaml
type: tile
entity: light.living_room
card_mod:
  style: |
    ha-card {
      border-radius: 20px;
      background: rgba(255, 200, 0, 0.08);
      border: none;
    }
```

### State-Based Conditional Style
```yaml
type: tile
entity: binary_sensor.door_front
card_mod:
  style: |
    ha-card {
      border: 2px solid {% if is_state('binary_sensor.door_front','on') %}
        var(--error-color)
      {% else %}
        transparent
      {% endif %};
      transition: border-color 0.3s ease;
    }
```

### Shadow DOM Piercing (advanced)
```yaml
# Use $ to pierce shadow DOM boundaries
card_mod:
  style:
    .: |
      ha-card {
        border-radius: 20px;
      }
    ha-tile-icon$: |
      div {
        color: var(--warning-color);
      }
    mushroom-state-info$: |
      .primary { font-weight: bold; }
```

### Global Theme-Level Injection
```yaml
# In themes/my_theme.yaml — applies to all cards of that type
card-mod-theme: |
  ha-card {
    border-radius: 16px;
    box-shadow: none;
  }
```

---

## Auto-Entities

GitHub: https://github.com/thomasloven/lovelace-auto-entities (1.5K★)

```yaml
# Active lights
type: custom:auto-entities
card:
  type: entities
  title: Lights On
  show_header_toggle: false
filter:
  include:
    - domain: light
      state: "on"
    - domain: switch
      area: living_room
  exclude:
    - entity_id: "light.outdoor_*"
    - attributes:
        device_class: occupancy
sort:
  method: area
  reverse: false
show_empty: false

# Low battery sensors
type: custom:auto-entities
card:
  type: glance
  title: Low Battery
filter:
  include:
    - attributes:
        device_class: battery
      state: < 20
sort:
  method: state
  numeric: true
```

---

## Charts & Graphs

### Mini-Graph-Card (quick trend)
```yaml
type: custom:mini-graph-card
entity: sensor.temperature_living
name: Temperature
hours_to_show: 24
points_per_hour: 4
line_width: 2
color: "#ff6600"
show:
  legend: false
  fill: true
```

### ApexCharts Card (full power)
```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Energy Today
graph_span: 24h
series:
  - entity: sensor.energy_daily_kwh
    type: area
    color: "#00aa44"
    stroke_width: 2
    fill_raw: last
  - entity: sensor.solar_production_kwh
    type: line
    color: "#ffaa00"
yaxis:
  - min: 0
    decimals: 1
    apex_config:
      tickAmount: 5
```

---

## Themes

```yaml
# configuration.yaml
frontend:
  themes: !include_dir_merge_named themes/
```

Install themes via HACS → Frontend → Themes. Top themes:

| Theme | Style | Author |
|-------|-------|--------|
| **Catppuccin** | Elegant pastel (dark + light variants) | catppuccin |
| **Material Rounded** | Material You, pairs with Mushroom | piitaya |
| **visionOS** | Apple Vision Pro glass aesthetic | — |
| **Google Home** | Clean, minimal, flat | — |
| **Nordic** | Scandinavian muted tones | — |

Activate: Profile → Theme (or via automation for auto-switching):
```yaml
actions:
  - action: frontend.set_theme
    data:
      name: Catppuccin Mocha
```

---

## Mobile & Responsive

### Companion App Capabilities
- **iOS**: Assist via action button, CarPlay, Apple Watch, lock screen widgets, Siri shortcuts
- **Android**: Wear OS, Android Auto, Quick Settings tiles, rich notifications with images
- Both: expose device sensors (GPS, battery, motion, WiFi SSID) back to HA as entities

### Wall Tablet Setup
```
Fully Kiosk Browser (HACS add-on) OR WallPanel (Android)
Settings: kiosk mode, screen wake on motion, auto-launch URL
```

### Mobile-First Design Tips
- Use `Bubble Card` horizontal-buttons-stack as bottom nav
- Keep pop-ups for detail; main view shows summaries only
- Tile cards with large touch targets (min 56px height)
- Test with iOS Safari (most restrictive) first
- Use `card_mod` `@media (hover: none)` for touch-specific styles

---

## Stack Recommendations

| Use Case | Stack |
|----------|-------|
| **Family (all ages)** | Sections + Tile + Mushroom + Material Rounded |
| **Power user desktop** | Sections + Mushroom + card-mod + Catppuccin |
| **Tablet wall panel** | Bubble Card bottom nav + pop-ups + Fully Kiosk |
| **Zero-YAML auto-gen** | Dwains Dashboard v3 |
| **Data/energy focus** | Sections + Tile + ApexCharts + mini-graph-card |

### Complete Family Dashboard Example
```yaml
views:
  - title: Home
    type: sections
    max_columns: 2
    sections:
      # Section 1: Status header
      - cards:
          - type: custom:mushroom-chips-card
            chips:
              - type: weather
                entity: weather.home
                show_temperature: true
              - type: entity
                entity: person.john
              - type: entity
                entity: person.jane

      # Section 2: Rooms
      - title: Rooms
        cards:
          - type: custom:mushroom-template-card
            primary: Living Room
            icon: mdi:sofa
            tap_action:
              action: navigate
              navigation_path: "#living-room"
          - type: custom:mushroom-template-card
            primary: Kitchen
            icon: mdi:countertop
            tap_action:
              action: navigate
              navigation_path: "#kitchen"

  # Pop-ups (ALWAYS AT END)
      - type: custom:bubble-card
        card_type: pop-up
        hash: "#living-room"
        name: Living Room
        cards:
          - type: tile
            entity: light.living_room
            features:
              - type: light-brightness
          - type: tile
            entity: climate.living
```
