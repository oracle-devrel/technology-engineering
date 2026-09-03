# cuOPT Route Optimizer Frontend

Professional single-page React application for NVIDIA cuOPT route optimization with AI-powered natural language interface.

## Quick Start

```bash
# 1. Navigate to the frontend application
cd app

# 2. Install dependencies
npm install

# 3. Start the frontend and API proxy
../scripts/run.sh

# Or use the npm convenience script:
npm run start
```

**Open in browser:** http://localhost:5173

## Configured Endpoints

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **Proxy Server** | http://localhost:3001 |
| **cuOPT API** | https://cuopt-2-cuopt.137-131-27-21.nip.io |
| **OCI GenAI** | Configured in `.env` |

## Prerequisites

### 1. OCI CLI Configuration
The application uses OCI SDK authentication. Ensure you have OCI CLI configured:

```bash
# Check if OCI config exists
cat ~/.oci/config

# If not configured, run:
oci setup config
```

Your `~/.oci/config` should look like:
```ini
[DEFAULT]
user=ocid1.user.oc1..xxxx
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..xxxx
region=eu-frankfurt-1
key_file=~/.oci/oci_api_key.pem
```

### 2. Node.js 18+
```bash
node -v  # Should be v18 or higher
```

## Features

### Mode 1: Route Optimizer Dashboard
- Full optimization interface with fleet configuration
- Stop management with map visualization
- Constraint settings (time windows, capacities)
- Interactive Leaflet map with route display
- Real-time performance charts
- Parallel job execution monitoring

### Mode 2: AI Chat Interface
- Natural language route optimization
- Powered by OCI GenAI (GPT-4o Mini)
- Automatic prompt → cuOPT JSON conversion
- Debug panel for request/response inspection
- Natural language result explanations

## Development Commands

```bash
# Start frontend only (port 5173)
npm run dev

# Start proxy server only (port 3001)
npm run server

# Start both concurrently
npm run start
```

## Environment Configuration

Create `.env` from `.env.example`, then configure the service endpoints and OCI values:

```env
# cuOPT
CUOPT_ENDPOINT=https://cuopt-2-cuopt.137-131-27-21.nip.io

# OCI GenAI
OCI_GENAI_ENDPOINT=https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com
OCI_GENAI_MODEL_ID=ocid1.generativeaimodel.oc1.eu-frankfurt-1.your-model-ocid
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..your-compartment-ocid
```

## Verifying Connectivity

### Test cuOPT API
```bash
curl -X GET https://cuopt-2-cuopt.137-131-27-21.nip.io/cuopt/health
```

### Test via Proxy Server
```bash
# Start server first, then:
curl http://localhost:3001/api/cuopt-health
curl http://localhost:3001/api/genai/health
```

## Project Structure

```
app/
├── src/
│   ├── api/              # cuOPT and GenAI clients
│   ├── components/
│   │   ├── Chat/         # AI chat interface
│   │   ├── Dashboard/    # Route optimizer
│   │   ├── Map/          # Leaflet map
│   │   └── shared/       # UI components
│   ├── store/            # Zustand state
│   └── types/            # TypeScript types
├── server/
│   └── index.js          # Express proxy with OCI SDK
├── .env.example          # Configuration template
├── .env                  # Local configuration (not committed)
└── package.json
```

## Troubleshooting

### "OCI client not initialized"
- Ensure `~/.oci/config` exists with valid credentials
- Check the DEFAULT profile is configured correctly
- Verify the API key file exists at the path specified in config

### cuOPT connection failed
- Verify the cuOPT endpoint is accessible: `curl https://cuopt-2-cuopt.137-131-27-21.nip.io/cuopt/health`
- Check if you're on the same network/VPN as the OKE cluster

### Port already in use
```bash
# Kill existing processes
lsof -ti:5173 | xargs kill -9
lsof -ti:3001 | xargs kill -9
```

## cuOPT API Reference

### Request Format
```json
{
  "cost_matrix_data": { "data": { "0": [[...]] } },
  "travel_time_matrix_data": { "data": { "0": [[...]] } },
  "task_data": {
    "task_locations": [0, 1, 2, ...],
    "demand": [[1], [1], ...]
  },
  "fleet_data": {
    "vehicle_locations": [[0, 0], [0, 0], ...],
    "capacities": [[100], [100], ...]
  },
  "solver_config": { "time_limit": 300 }
}
```

### Performance Baselines (A10G GPU)
| Stops | Payload Size | Solve Time |
|-------|-------------|------------|
| 1,000 | 37 MB | 136s |
| 2,500 | 230 MB | 184s |
| 5,000 | 922 MB | 270s |

## Theming

NVIDIA + Oracle enterprise dark theme:
- Primary Green: `#76B900`
- Background: `#0D1117`
- Card: `#1B1F2E`
