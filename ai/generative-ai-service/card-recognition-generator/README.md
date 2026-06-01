# Recognition Card Generator

Generates branded employee recognition cards, plus a web UI to upload employee CSV data, generate previews, download PNGs, and compose email drafts.

All application source and assets live in **`files/`**. This README stays at the repository root so the repo is easy to browse on GitHub.

---

## Repository layout

| Path | Purpose |
|------|--------|
| `files/src/` | FastAPI backend (`react_api.py`, image client) |
| `files/frontend/` | React (Vite + TypeScript) web UI |
| `files/data/` | Sample CSV files for testing |
| `files/requirements.txt` | Python dependencies |
| `files/output/` | Generated PNGs (created at runtime, **not** committed) |

---

## Prerequisites

- **Python 3.10+** (3.11+ recommended)
- **Node.js 20+** and npm
- API credentials for your image provider (set via environment variables; see `files/src/grok_openai_image.py` and `files/src/react_api.py`)

---

## Quick start (local)

### 1. Backend

```bash
cd files
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Configure environment (at minimum, the variables your `ENDPOINT` / OpenAI-compatible image API expects), then:

```bash
python -m uvicorn src.react_api:app --host 127.0.0.1 --port 8055 --reload
```

### 2. Frontend

In a second terminal:

```bash
cd files/frontend
npm install
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173/`). The dev server proxies `/api/*` to `http://127.0.0.1:8055`.

### 3. Optional: company logo assets

Place official wordmarks in `files/frontend/public/` as `oracle-logo-red.png` and `oracle-logo-white.png` for exact on-card branding. Employee photos go under `files/frontend/public/employee-photos/`.

---

## CSV format

Use a header row. Important columns include `full_name`, `manager_name`, `manager_position`, `photo_asset_id` (path under `employee-photos/`), and **`employee_email`** (or `email` / `work_email`) for the email button. See `files/data/sample_employees_hr_use_cases.csv`.

---

## If you see a stray `frontend` folder at the repository root

The real app is under `files/frontend/`. A near-empty `frontend` at the top level can appear if a dev server held files open during a move. **Stop** any running `npm run dev` / Vite process, then delete the root `frontend` folder. Use only `files/frontend/` for the UI.

---

## Production notes

- Do **not** commit `files/output/`, `.env`, or `node_modules/`.
- Tune API keys and base URLs via environment variables appropriate for your company’s deployment.
- For enterprise email delivery with attachments, consider a server-side mail integration instead of relying on `mailto:` alone.

---

## License / confidentiality

Use and distribution are subject to your employer’s policies. Do not commit secrets or production credentials.
