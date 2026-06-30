# Aladdin Notifications

Home Assistant custom component for fetching school notifications from [Aladdin.ie](https://www.aladdin.ie).

Provides a sensor (`sensor.aladdin_notifications`) showing the count of notifications, with full details available in its attributes.

## Features

- Config flow via UI — no YAML required
- Username/password authentication
- Configurable school ID
- Configurable scan interval
- Automatic session management and re-authentication
- Shows latest 20 notifications with sender, timestamp, preview, and full text

## Installation

### HACS (recommended)

1. Go to HACS → Integrations → ⋮ → Custom repositories
2. Add URL: `https://github.com/smcelhinney/aladdin-notifications`
3. Category: Integration
4. Click Install

### Manual

Copy the `custom_components/aladdin_notifications/` directory into your Home Assistant `custom_components/` directory and restart HA.

## Configuration

1. Go to Settings → Devices & Services → Add Integration
2. Search for "Aladdin Notifications"
3. Enter your Aladdin.ie username, password, and school ID
4. The default school ID is `5258313025454080`

### Options

- **Scan interval**: Update frequency in seconds (default: 300, min: 60, max: 3600)

## Sensor

`sensor.aladdin_notifications` is created with:

- **State**: Number of notifications
- **Icon**: `mdi:bell`
- **Attributes**: `notifications` — list of latest 20 notifications with `id`, `from`, `to`, `timestamp`, `preview`, `full_text`

## Dashboard

Add a markdown card to display notifications:

```yaml
type: markdown
content: |
  {% set notifs = state_attr('sensor.aladdin_notifications', 'notifications') or [] %}
  {% for n in notifs[:20] %}
  **{{ n.timestamp }}** — {{ n.from }}
  {{ n.preview }}
  {% if n.full_text %}
  > {{ n.full_text }}
  {% endif %}
  ---
  {% endfor %}
```
