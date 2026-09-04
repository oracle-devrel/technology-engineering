# Context For Agents

This file keeps the technical background out of the main README. Use it when you need to understand or modify the codebase.

## Project Summary

OCI GenAI Video Analysis Studio is a React + FastAPI demo for analyzing uploaded videos with Gemini models on Oracle Cloud Infrastructure Generative AI.

The app is built for two uses:

- A standalone GitHub demo asset.
- A reusable React component that can be embedded in another website.

The browser collects only non-secret OCI connection settings, prompt details, and the video file. Real OCI authentication stays on the Python backend.

## Features

- Upload and preview a video in the browser.
- Use OCI API key profile authentication from the backend host.
- Enter non-secret OCI connection settings in the UI.
- Choose Gemini 2.5 Pro, Gemini 2.5 Flash, or Gemini 2.5 Flash-Lite.
- Compare up to three public Gemini model IDs with the same uploaded video and prompt.
- Optionally provide a model OCID instead of selecting a public Gemini model ID.
- Pick an analysis mode with a default prompt, or use a custom prompt.
- Send the video and prompt to `POST /api/analyze-video`.
- Call OCI GenAI from FastAPI with `langchain-oci`.
- Show input tokens, output tokens, and backend-measured latency for processed videos and model comparisons.
- Copy or download the model output or comparison report.

## Project Structure

```text
backend/
  main.py
  model_catalog.py
  oci_video_analysis.py
src/
  components/
    video-analysis-studio.tsx
    index.ts
  studio-app.tsx
  main.tsx
  styles.css
.env.example
requirements.txt
package.json
vite.config.ts
```

## Setup Details

The repository includes `setup.ps1`, `setup.sh`, `start.ps1`, and `start.sh`.

The setup scripts:

- Install `uv` if needed.
- Create `.venv`.
- Install Python dependencies with `uv pip install -r requirements.txt`.
- Create `.env` from `.env.example` if `.env` is missing.
- Offer to run `npm install` when `node_modules` is missing.

If your network requires VPN or proxy access for npm, enable it before running `npm install`; otherwise package downloads can time out or fail.

The start scripts run FastAPI and Vite together. Default ports:

- Backend: `http://127.0.0.1:8002`
- Frontend: `http://127.0.0.1:5173`

Ports can be overridden with `BACKEND_PORT` and `FRONTEND_PORT`.

## Manual Frontend Commands

Install Node dependencies:

```bash
npm install
```

Run the Vite app:

```bash
npm run dev
```

The frontend proxies `/api` calls to the FastAPI backend. If the backend is on a non-default port, set `VITE_API_PROXY_TARGET`.

Windows example:

```powershell
$env:VITE_API_PROXY_TARGET="http://localhost:8002"
npm run dev
```

macOS/Linux example:

```bash
VITE_API_PROXY_TARGET=http://localhost:8002 npm run dev
```

## Manual Backend Commands

Create and activate a Python virtual environment with `uv`:

```bash
uv venv .venv
```

Windows activation:

```powershell
.\.venv\Scripts\activate
```

macOS/Linux activation:

```bash
source .venv/bin/activate
```

Install backend dependencies:

```bash
uv pip install -r requirements.txt
```

Run FastAPI:

```bash
uvicorn backend.main:app --reload --port 8002
```

Health check:

```bash
curl http://127.0.0.1:8002/api/health
```

## OCI Local Configuration

Configure OCI authentication on the server machine, not in the browser. The app uses OCI API key profile authentication through the backend host.

The frontend lets the user enter:

- OCI compartment OCID.
- OCI GenAI service endpoint from a public region dropdown.
- Optional model OCID.

The frontend must not collect private keys, API signing keys, config file contents, auth tokens, tenancy secrets, or other private credentials.

The backend first assumes the OCI config profile is `DEFAULT` and the config file path is `~/.oci/config`. If that profile or file cannot be found, the UI reveals fields for explicitly entering the server-side profile name and config file path.

After a successful analysis, the backend saves non-secret settings to a runtime env file for the next run. By default this is outside the project at `~/.oci-genai-video-analysis-studio.env`, which avoids Vite/uvicorn reloads while the app is running. Override the location with `OCI_VIDEO_STUDIO_ENV_FILE`.

Saved runtime settings:

- `OCI_COMPARTMENT_ID`
- `GENAI_ENDPOINT`
- `GENAI_REGION`
- `DEFAULT_MODEL_ID`
- `OCI_CONFIG_PROFILE`
- `OCI_CONFIG_FILE`

The app does not save private keys, tokens, config file contents, or uploaded video data to the runtime env file.

Optional `.env` fallback values:

```env
OCI_COMPARTMENT_ID=YOUR_COMPARTMENT_OCID
GENAI_ENDPOINT=https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com
GENAI_REGION=eu-frankfurt-1
OCI_CONFIG_FILE=~/.oci/config
OCI_CONFIG_PROFILE=DEFAULT
DEFAULT_MODEL_ID=google.gemini-2.5-flash
MAX_UPLOAD_MB=37
ALLOWED_ORIGIN_REGEX=https?://(localhost|127\.0\.0\.1)(:\d+)?
```

## Model Catalog

The model selector is populated from `GET /api/model-catalog` with Gemini models that support video understanding.

Supported public Gemini model IDs are validated server-side from the model catalog:

- `google.gemini-2.5-pro`
- `google.gemini-2.5-flash`
- `google.gemini-2.5-flash-lite`

If `model_ocid` is provided, it takes precedence over `model_id` and the public model dropdown is disabled in the UI.

The endpoint dropdown includes the OCI Generative AI inference endpoints whose regions list Gemini 2.5 support in Oracle's model endpoint region documentation:

- `us-ashburn-1` with identity domain G
- `us-chicago-1`
- `us-phoenix-1`
- `eu-frankfurt-1` with identity domain G
- `ap-hyderabad-1`
- `ap-osaka-1`

Use Refresh from OCI in the settings panel to query OCI Generative AI `list_models` for the configured compartment and supported regions. The refresh uses the selected OCI config profile/path, filters active Google Gemini chat base models, updates the model dropdown, and keeps the selected region on an endpoint that supports the selected model when possible.

Pricing and feature metadata are loaded from environment variables on each backend run. `.env.example` includes the supported `OCI_VIDEO_MODEL_*` keys for input/output token pricing, modality support, token limits, function/tool support, structured output, context caching, and thinking. Flash and Flash-Lite also include separate audio input prices because Oracle lists audio as a distinct billing line item for those models. These are non-secret values and can be updated when Oracle changes public pricing or model documentation.

## Gemini Video Call

The backend function is in `backend/oci_video_analysis.py`:

```python
analyze_video_with_oci_gemini(
    video_path,
    prompt,
    model_id,
    mime_type,
    compartment_id,
    service_endpoint,
    auth_profile,
    auth_file_location,
)
```

It reads the temporary uploaded video, base64 encodes it, creates a `HumanMessage` containing the text prompt and video media payload, invokes `ChatOCIGenAI`, and returns `response.content`.

The backend also captures response metadata needed by the UI:

- Input tokens when returned by LangChain/OCI metadata.
- Output tokens when returned by LangChain/OCI metadata.
- Backend-measured `latency_ms` for the `llm.invoke(...)` call.

The UI does not estimate or invent token counts. If a token value is not returned by LangChain/OCI metadata, the UI shows `Not returned`.

The comparison view reuses `POST /api/analyze-video` by sending one request per selected public model ID. It keeps successful model outputs visible even if another selected model returns an error.

## API

### `POST /api/analyze-video`

Multipart form fields:

- `video`
- `prompt`
- `model_id`
- `analysis_mode`
- `compartment_id`
- `service_endpoint`
- `region`
- `model_ocid` optional
- `auth_profile`
- `auth_file_location`

Response:

```json
{
  "output": "model response text",
  "model_id": "google.gemini-2.5-flash",
  "analysis_mode": "video-summary",
  "api_metadata": {
    "latency_ms": 2400,
    "input_tokens": 123,
    "output_tokens": 45
  }
}
```

### `GET /api/model-catalog`

Returns the built-in public model catalog and per-region endpoint availability.

### `POST /api/model-catalog/discover`

Multipart form fields:

- `compartment_id`
- `auth_profile`
- `auth_file_location`

Returns the same catalog shape as `GET /api/model-catalog`, but with availability refreshed from OCI Generative AI `list_models` where the configured profile has access.

## Embedding The Component

Import the reusable component from `src/components`:

```tsx
import { VideoAnalysisStudio } from "./components";

export function MyPage() {
  return <VideoAnalysisStudio mode="embedded" />;
}
```

Pass an explicit backend URL when embedding into another app:

```tsx
<VideoAnalysisStudio
  mode="embedded"
  apiUrl="https://your-backend.example.com/api/analyze-video"
  initialRegion="eu-frankfurt-1"
  initialServiceEndpoint="https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
/>
```

For a personal website hosted on a different origin, update the backend CORS environment setting before exposing the backend.

## Analysis Modes

- Video summary
- Timeline / key events
- Compliance or safety review
- Object / scene description
- Custom prompt

Each non-custom mode loads a default prompt that can still be edited before analysis. Custom prompt sends exactly what the user typed.

## Security Notes

- Do not expose OCI credentials in frontend code.
- Do not commit `.env` files.
- Keep OCI authentication server-side.
- Validate uploaded file type and size. This demo caps uploads at 37 MB because larger video payloads are not supported by the target API path.
- Delete temporary uploaded files after analysis.
- Restrict backend CORS origins before deploying beyond local development.
- Consider adding user authentication and rate limits before sharing a public endpoint.

## Known Limitations

- The demo stores uploaded videos only as temporary files during a request, then deletes them.
- Browser upload and OCI model limits still apply. The app blocks files larger than 37 MB in both the frontend and backend.
- Optional model OCID is accepted by the API and takes precedence over the public model selector.
- Model comparison is limited to public model IDs from the selected endpoint. Clear the optional model OCID field before running a comparison.
- The app is intended as a demo asset, not a hardened production service.
