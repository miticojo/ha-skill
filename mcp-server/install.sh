#!/bin/bash
# install.sh — Register ha-mcp with Claude Code
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure .env exists
if [ ! -f "$DIR/.env" ]; then
  echo "⚠  No .env found. Copying .env.example → .env"
  cp "$DIR/.env.example" "$DIR/.env"
  echo "   Edit $DIR/.env with your HA_URL and HA_TOKEN, then re-run."
  exit 1
fi

# Install Python deps if pip is available
if command -v pip3 &>/dev/null; then
  echo "Installing Python dependencies..."
  pip3 install -q -r "$DIR/requirements.txt"
fi

# Register with Claude Code
source "$DIR/.env"
claude mcp add ha-mcp \
  -s user \
  -e HA_URL="$HA_URL" \
  -e HA_TOKEN="$HA_TOKEN" \
  -- python3 "$DIR/ha_mcp.py"

echo ""
echo "✓ ha-mcp registered. Verify with: claude mcp list"
echo ""
echo "Quick test (inside Claude):"
echo "  ha_get_states(\"light\")"
echo "  ha_get_lovelace()"
echo "  ha_render_template(\"{{ states('sun.sun') }}\")"
