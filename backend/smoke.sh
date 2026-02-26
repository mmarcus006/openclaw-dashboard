#!/usr/bin/env bash
set -euo pipefail

# OpenClaw Dashboard E2E Smoke Test
# ----------------------------------
# This script tests all API endpoints to verify basic functionality.
# It creates a minimal OPENCLAW_HOME, starts the backend server,
# runs curl tests against all endpoints, and cleans up afterward.

# ==============================
# Configuration
# ==============================

# Find a random available port
PORT=$(python3 -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')
BASE_URL="http://127.0.0.1:${PORT}"
API_URL="${BASE_URL}/api"

# Determine OPENCLAW_HOME
if [[ -n "${OPENCLAW_HOME:-}" ]] && [[ -d "$OPENCLAW_HOME" ]]; then
    echo "Using existing OPENCLAW_HOME: $OPENCLAW_HOME"
    TEMP_HOME=""
else
    TEMP_HOME=$(mktemp -d -t openclaw-smoke-XXXXXX)
    export OPENCLAW_HOME="$TEMP_HOME"
    echo "Created temporary OPENCLAW_HOME: $OPENCLAW_HOME"
fi

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==============================
# Cleanup trap
# ==============================

SERVER_PID=""

cleanup() {
    echo ""
    echo "Cleaning up..."

    # Kill server if running
    if [[ -n "$SERVER_PID" ]]; then
        echo "Stopping server (PID: $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi

    # Remove temp directory if created
    if [[ -n "$TEMP_HOME" ]] && [[ -d "$TEMP_HOME" ]]; then
        echo "Removing temporary OPENCLAW_HOME: $TEMP_HOME"
        rm -rf "$TEMP_HOME"
    fi

    echo "Cleanup complete."
}

trap cleanup EXIT INT TERM

# ==============================
# Setup minimal OPENCLAW_HOME
# ==============================

setup_openclaw_home() {
    echo "Setting up minimal OPENCLAW_HOME structure..."

    mkdir -p "$OPENCLAW_HOME/workspace"
    mkdir -p "$OPENCLAW_HOME/sessions"

    # Create minimal openclaw.json
    cat > "$OPENCLAW_HOME/openclaw.json" <<'EOF'
{
  "agents": {
    "main": {
      "model": "claude-sonnet-4-5",
      "workspace": "workspace"
    }
  },
  "cron_jobs": []
}
EOF

    # Create minimal sessions.json
    cat > "$OPENCLAW_HOME/sessions/sessions.json" <<'EOF'
{
  "agent:main:main": {
    "key": "agent:main:main",
    "agent": "main",
    "context": "main",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z",
    "messageCount": 0
  }
}
EOF

    echo "OPENCLAW_HOME setup complete."
}

# Only setup if we created a temp directory
if [[ -n "$TEMP_HOME" ]]; then
    setup_openclaw_home
fi

# ==============================
# Start backend server
# ==============================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${SCRIPT_DIR}/.venv/bin/python"
UVICORN="${SCRIPT_DIR}/.venv/bin/uvicorn"

if [[ ! -f "$UVICORN" ]]; then
    echo -e "${RED}ERROR: uvicorn not found at $UVICORN${NC}"
    echo "Please run 'make setup' first to create the virtual environment."
    exit 1
fi

echo ""
echo "Starting backend server on port $PORT..."
cd "$SCRIPT_DIR"
"$UVICORN" app.main:app --host 127.0.0.1 --port "$PORT" --log-level error > /dev/null 2>&1 &
SERVER_PID=$!

echo "Server started (PID: $SERVER_PID)"

# ==============================
# Wait for server to be ready
# ==============================

echo "Waiting for server to be ready..."
MAX_RETRIES=10
RETRY_COUNT=0

while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
    if curl -s -f "${API_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}Server is ready!${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [[ $RETRY_COUNT -eq $MAX_RETRIES ]]; then
        echo -e "${RED}ERROR: Server did not become ready after $MAX_RETRIES attempts${NC}"
        exit 1
    fi
    sleep 1
done

# ==============================
# Test runner
# ==============================

PASS_COUNT=0
FAIL_COUNT=0

test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local expected_status="$3"
    local description="$4"
    local data="${5:-}"

    echo -n "Testing $description... "

    local curl_args=(-s -w "%{http_code}" -o /tmp/smoke_response.json)

    if [[ "$method" == "POST" ]]; then
        curl_args+=(-X POST -H "Content-Type: application/json")
        if [[ -n "$data" ]]; then
            curl_args+=(-d "$data")
        fi
    fi

    local status_code
    status_code=$(curl "${curl_args[@]}" "${API_URL}${endpoint}")

    if [[ "$status_code" -eq "$expected_status" ]]; then
        echo -e "${GREEN}PASS${NC} (status: $status_code)"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}FAIL${NC} (expected: $expected_status, got: $status_code)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        # Show response body for debugging
        if [[ -f /tmp/smoke_response.json ]]; then
            echo -e "${YELLOW}Response:${NC}"
            cat /tmp/smoke_response.json | head -n 20
            echo ""
        fi
    fi
}

# ==============================
# Run endpoint tests
# ==============================

echo ""
echo "========================================"
echo "Running API endpoint tests"
echo "========================================"
echo ""

# Health check
test_endpoint "GET" "/health" 200 "GET /api/health"

# Agents
test_endpoint "GET" "/agents" 200 "GET /api/agents"

# Config
test_endpoint "GET" "/config" 200 "GET /api/config"

# Config validation
VALID_CONFIG='{"config": {"agents": {"main": {"model": "claude-sonnet-4-5", "workspace": "workspace"}}, "cron_jobs": []}}'
test_endpoint "POST" "/config/validate" 200 "POST /api/config/validate" "$VALID_CONFIG"

# Gateway
test_endpoint "GET" "/gateway/status" 200 "GET /api/gateway/status"
test_endpoint "GET" "/gateway/history" 200 "GET /api/gateway/history"

# Cron
test_endpoint "GET" "/cron" 200 "GET /api/cron"

# Sessions (if agent exists)
test_endpoint "GET" "/agents/main/sessions" 200 "GET /api/agents/main/sessions"

# ==============================
# Summary
# ==============================

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "Total tests: $((PASS_COUNT + FAIL_COUNT))"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

# Cleanup happens via trap
if [[ $FAIL_COUNT -eq 0 ]]; then
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some smoke tests failed.${NC}"
    exit 1
fi
