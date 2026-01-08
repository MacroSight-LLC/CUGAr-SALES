#!/bin/bash
# Test monitoring stack end-to-end

set -e

echo "🧪 Testing CUGAr-SALES Monitoring Stack"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Start metrics API
echo "📊 Step 1: Starting metrics API..."
cd /home/taylor/CUGAr-SALES
python3 src/cuga/api/metrics_endpoint.py &
API_PID=$!
sleep 3

# Check if API started
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓${NC} Metrics API running on port 8000"
else
    echo -e "${RED}✗${NC} Metrics API failed to start"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Step 2: Verify empty metrics
echo ""
echo "📈 Step 2: Verifying empty metrics..."
TOTAL_EXECS=$(curl -s http://localhost:8000/dashboard | python3 -c "import json, sys; print(json.load(sys.stdin)['executions']['total'])")
if [ "$TOTAL_EXECS" == "0" ]; then
    echo -e "${GREEN}✓${NC} Metrics initialized (0 executions)"
else
    echo -e "${RED}✗${NC} Unexpected initial state"
fi

# Step 3: Generate metrics by running demo
echo ""
echo "🚀 Step 3: Generating metrics (running 3 executions)..."
echo -e "${YELLOW}   This will take ~15-20 seconds...${NC}"
python3 demo_observability.py > /tmp/demo_output.log 2>&1 &
DEMO_PID=$!

# Wait for demo to complete
wait $DEMO_PID
DEMO_EXIT=$?

if [ $DEMO_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Demo completed successfully"
else
    echo -e "${RED}✗${NC} Demo failed (exit code: $DEMO_EXIT)"
    tail -n 20 /tmp/demo_output.log
fi

# Step 4: Verify metrics were recorded
echo ""
echo "📊 Step 4: Verifying metrics were recorded..."
sleep 2  # Give metrics time to update

METRICS_JSON=$(curl -s http://localhost:8000/dashboard)
TOTAL_EXECS=$(echo "$METRICS_JSON" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data['executions']['total'])")
SUCCESS_RATE=$(echo "$METRICS_JSON" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data['golden_signals']['success_rate'])")
LATENCY_P95=$(echo "$METRICS_JSON" | python3 -c "import json, sys; data=json.load(sys.stdin); print(int(data['golden_signals']['latency_p95_ms']))")

echo "   Total Executions: $TOTAL_EXECS"
echo "   Success Rate: $SUCCESS_RATE"
echo "   Latency P95: ${LATENCY_P95}ms"

if [ "$TOTAL_EXECS" == "3" ]; then
    echo -e "${GREEN}✓${NC} Metrics recorded correctly (3 executions)"
else
    echo -e "${YELLOW}⚠${NC} Expected 3 executions, got $TOTAL_EXECS"
fi

# Step 5: Verify Prometheus format
echo ""
echo "📈 Step 5: Verifying Prometheus export..."
PROM_OUTPUT=$(curl -s http://localhost:8000/metrics)

if echo "$PROM_OUTPUT" | grep -q "cugar_success_rate"; then
    echo -e "${GREEN}✓${NC} Prometheus metrics available"
else
    echo -e "${RED}✗${NC} Prometheus metrics missing"
fi

if echo "$PROM_OUTPUT" | grep -q "# HELP"; then
    echo -e "${GREEN}✓${NC} HELP annotations present"
else
    echo -e "${RED}✗${NC} Missing HELP annotations"
fi

if echo "$PROM_OUTPUT" | grep -q "# TYPE"; then
    echo -e "${GREEN}✓${NC} TYPE annotations present"
else
    echo -e "${RED}✗${NC} Missing TYPE annotations"
fi

# Step 6: Test all endpoints
echo ""
echo "🔍 Step 6: Testing all API endpoints..."

# Root
if curl -s http://localhost:8000/ | grep -q "CUGAr-SALES"; then
    echo -e "${GREEN}✓${NC} GET / (root) - OK"
else
    echo -e "${RED}✗${NC} GET / (root) - FAILED"
fi

# Health
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} GET /health - OK"
else
    echo -e "${RED}✗${NC} GET /health - FAILED"
fi

# Dashboard
if curl -s http://localhost:8000/dashboard | grep -q "golden_signals"; then
    echo -e "${GREEN}✓${NC} GET /dashboard - OK"
else
    echo -e "${RED}✗${NC} GET /dashboard - FAILED"
fi

# Metrics
if curl -s http://localhost:8000/metrics | grep -q "cugar_"; then
    echo -e "${GREEN}✓${NC} GET /metrics - OK"
else
    echo -e "${RED}✗${NC} GET /metrics - FAILED"
fi

# Docs
if curl -s http://localhost:8000/docs | grep -q "swagger"; then
    echo -e "${GREEN}✓${NC} GET /docs (Swagger UI) - OK"
else
    echo -e "${YELLOW}⚠${NC} GET /docs - May require browser"
fi

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $API_PID 2>/dev/null || true
sleep 1

echo ""
echo "========================================"
echo -e "${GREEN}✅ Monitoring stack test complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. docker-compose -f docker-compose.monitoring.yml up -d"
echo "  2. Open http://localhost:9090 (Prometheus)"
echo "  3. Open http://localhost:3000 (Grafana - admin/admin)"
echo ""
