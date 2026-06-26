# LiveKit Hotel Assistant + OCI NL2SQL Setup

This project includes three parts:

1. The **LiveKit voice agent** (Python) — `main.py`
2. The **OCI Semantic Store / NL2SQL setup and enrichment script** (Python) — `demo_nl2sql.py`
3. The **React frontend UI**

The agent uses two separate OCI knowledge backends:

* **OCI Vector Store (file search)** — stores hotel documents (PDFs, policies, amenities) and is queried via the OCI OpenAI-compatible API for unstructured hotel information
* **OCI NL2SQL Semantic Store** — translates natural language into SQL queries against the Oracle Autonomous Database for room availability and booking data

This README explains everything that must be configured before the system will run successfully.

---

## 1) What you need installed

### Required software

* **Python 3.11+**
* **Node.js 18+** and **npm**
* **OCI CLI**
* Access to an **OCI profile** in `~/.oci/config`
* Access to the **Oracle Autonomous Database wallet**
* A **LiveKit** project / room backend configured for your environment

### Python environment setup

Create and activate a virtual environment first, then install all dependencies:

```bash
python3 -m venv livekit
.\livekit\Scripts\activate        # Windows
# source livekit/bin/activate     # Mac/Linux
pip install --upgrade pip
pip install -r requirements.txt
```

Then install all required packages:

```bash
pip install torch
pip install python-dotenv
pip install fastmcp
pip install pdoc
pip install ruff
pip install oracledb oci openai httpx oci-genai-auth
pip install "livekit-agents[deepgram,openai,cartesia,silero,turn-detector] ~= 1.2.0"
pip install "livekit-plugins-oracle ~= 1.2"
pip install "livekit-plugins-noise-cancellation >= 0.2.5"
pip install "oci-ai-speech-realtime ~= 2.2"
```

After installing, run the agent file download step before starting the agent for the first time:

```bash
python3 main.py download-files
```

This downloads the models required by Silero VAD and the turn detector. It only needs to be run once.

When you are done working, deactivate the virtual environment:

```bash
deactivate
```

> **Note:** Always activate the virtual environment (`source myenv/bin/activate`) before running any of the scripts in this project.

---

## 2) OCI authentication setup

The scripts in this repo use OCI signing from the local config file.

### Option A: API key profile

Make sure `~/.oci/config` contains a valid `DEFAULT` profile, for example:

```ini
[DEFAULT]
user=ocid1.user.oc1....
tenancy=ocid1.tenancy.oc1....
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
key_file=/path/to/oci_api_key.pem
region=us-chicago-1
```

### Option B: Security token profile

If you use a security token, authenticate first with OCI and make sure the config file includes the token settings required by your environment.

The script reads:

* `~/.oci/config`
* the token file referenced by `security_token_file`
* the private key referenced by `key_file`

---

## 3) OCI policies required for NL2SQL / Semantic Store

The semantic store needs both **human-user permissions** and **runtime permissions**.

### 3.1 Admin permissions

For users who create and manage the semantic store:

```text
allow group semantic-store-admin to manage generative-ai-semantic-store in compartment <your-compartment>
allow group semantic-store-admin to manage generative-ai-nl2sql in compartment <your-compartment>
```

### 3.2 User permissions

For users who only need to use an existing semantic store:

```text
allow group semantic-store-users to read generative-ai-semantic-store in compartment <your-compartment>
allow group semantic-store-users to read generative-ai-nl2sql in compartment <your-compartment>
```

### 3.3 Runtime permissions for the Semantic Store resource principal

These are the important service permissions that let the semantic store enrich and query data:

```text
allow any-user to use database-tools-family in compartment <your-compartment> where all {request.principal.type='generativeaisemanticstore'}
allow any-user to read database-family in compartment <your-compartment> where all {request.principal.type='generativeaisemanticstore'}
allow any-user to read autonomous-database-family in compartment <your-compartment> where all {request.principal.type='generativeaisemanticstore'}
allow any-user to use generative-ai-family in tenancy where all {request.principal.type='generativeaisemanticstore'}
allow any-user to read secret-family in compartment <your-compartment> where all {request.principal.type='generativeaisemanticstore'}
```

### 3.4 DB Tools admin prerequisite policies

DB Tools administrators must already have the needed infrastructure permissions:

```text
allow group DatabaseToolsConnectionAdministrators to manage virtual-network-family in compartment <your-compartment>
allow group DatabaseToolsConnectionAdministrators to manage database-family in compartment <your-compartment>
allow group DatabaseToolsConnectionAdministrators to manage autonomous-database-family in compartment <your-compartment>
allow group DatabaseToolsConnectionAdministrators to manage vaults in compartment <your-compartment>
allow group DatabaseToolsConnectionAdministrators to manage secret-family in compartment <your-compartment>
allow group DatabaseToolsConnectionAdministrators to manage database-tools-family in compartment <your-compartment>
```

---

## 4) Database / wallet setup

The agent connects to Oracle DB through a wallet and the Autonomous Database connect string.

### Required environment variables

Create a `.env` file with values like:

```env
DB_USER=ADMIN
DB_PASSWORD=your_password
DB_DSN=(description=(retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.{REGION}.oraclecloud.com))(connect_data=(service_name=your_service_name))(security=(ssl_server_dn_match=yes)))
WALLET_PASSWORD=your_wallet_password
LIVEKIT_API_SECRET=livekit_server_secret_key
LIVEKIT_API_KEY=api_key
LIVEKIT_URL=livekit_url
```

### Wallet folder

Place the wallet in the project root as:

```text
./Wallet_daTest
```

If the folder name is different, update the code or the path accordingly.

---

## 5) Semantic Store setup and enrichment

The project uses the following semantic store values in `demo_nl2sql.py`:

* `REGION`
* `SCHEMA_NAME`
* `COMPARTMENT_ID`
* `QUERYING_CONNECTION_ID`
* `ENRICHMENT_CONNECTION_ID`
* `SSO_WALLET_SECRET_ID`

Make sure these point to your actual OCI resources before running anything. The `SEMANTIC_STORE_ID` is derived automatically from the create response at runtime.

### 5.1 What `demo_nl2sql.py` does

`demo_nl2sql.py` is the single consolidated script that handles the full setup and enrichment pipeline in one run. It replaces the previously separate `update.py`, `setup_nl2sql.py`, and `enrich_semantic_store.py` scripts.

It performs all of the following steps in sequence:

1. **Update DB Tools connections** — patches both the querying and enrichment connections with the SSO wallet secret
2. **Create the semantic store** — provisions a new semantic store for NL2SQL
3. **Trigger enrichment** — kicks off a `FULL_BUILD` enrichment job against the configured schema
4. **Poll enrichment progress** — waits for the job to reach `SUCCEEDED` or `FAILED`, checking every 30 seconds for up to 12 minutes
5. **Test `generateSqlFromNl`** — sends a sample natural language query to confirm the pipeline is working end-to-end

### 5.2 Run the script

```bash
python demo_nl2sql.py
```

The script will print status updates at each step. When enrichment completes successfully, it will run the NL2SQL test automatically.

### 5.3 Validate the semantic store

The final step of `demo_nl2sql.py` calls `generateSqlFromNl` with the sample prompt:

```text
Which rooms are available from June 20 to June 25?
```

If this returns SQL, the semantic store is ready.

---

## 6) Vector store setup (hotel documents / file search)

The agent's `search_hotel_documents` tool uses an OCI vector store to answer questions about hotel policies, amenities, room descriptions, dining, and anything else captured in your hotel documents. This is separate from the NL2SQL semantic store — it handles unstructured content (PDFs, text files) rather than database queries.

### 6.1 Required values in `main.py`

```python
PROJECT_ID      = "ocid1.generativeaiproject.oc1.us-chicago-1...."
VECTOR_STORE_ID = "vs_ord_..."
```

Both values must point to your actual OCI Generative AI project and vector store before running the agent.

### 6.2 What the vector store is used for

The agent calls `file_search` via the OCI OpenAI-compatible API endpoint:

```
https://inference.generativeai.<region>.oci.oraclecloud.com/openai/v1
```

It passes `VECTOR_STORE_ID` as the target store. The model used for document search responses is `openai.gpt-4.1-mini`.

### 6.3 Uploading hotel documents

Before the agent can answer hotel questions, you must upload your hotel documents (PDFs, policy files, room descriptions, etc.) to the vector store referenced by `VECTOR_STORE_ID`.

Use the OCI Console or the OCI CLI to upload files to your Generative AI vector store. Once uploaded, the file search tool will automatically retrieve relevant chunks at query time.

### 6.4 OCI authentication for file search

File search calls use `OciUserPrincipalAuth` from the `oci-genai-auth` package, reading from the `DEFAULT` profile in `~/.oci/config`. Make sure the user in that profile has access to the Generative AI project and vector store.

### 6.5 Verify the vector store is working

Run the agent and ask a hotel-specific question such as:

```text
What is the check-in time?
What is your pet policy?
```

If the agent returns a relevant answer drawn from your documents, the vector store is connected correctly.

---

## 7) LiveKit setup and token server

### 7.1 LiveKit requirements

Before the agent and frontend can talk to each other, you need a working LiveKit deployment and credentials.

You need:

* a **LiveKit server URL** (`LIVEKIT_URL`)
* a **LiveKit API key** (`LIVEKIT_API_KEY`)
* a **LiveKit API secret** (`LIVEKIT_API_SECRET`)
* a room name that both the frontend and agent will join

You can use either **LiveKit Cloud** or your own self-hosted LiveKit server.

### 7.2 Token server setup

The frontend should not generate LiveKit tokens directly in the browser. Instead, run the FastAPI token server in `token_server.py` and let the frontend request a token from it.

Create a `.env` file next to `token_server.py` with values like:

```env
LIVEKIT_URL=wss://your-livekit-server
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
```

Install the token server dependencies:

```bash
pip install fastapi uvicorn livekit-api python-dotenv pydantic
```

Run the token server from the project root (where `token_server.py` lives):

```bash
uvicorn token_server:app --host 0.0.0.0 --port 8000 --reload
```

The token server will be available at `http://localhost:8000`.

Your frontend can call:

```text
POST /api/token
```

with a body like:

```json
{
  "room_name": "harbor-view-room",
  "participant_identity": "web-user",
  "participant_name": "Web User"
}
```

The response returns:

* `server_url`
* `participant_token`

### 7.3 Install dependencies

Make sure the Python environment contains the LiveKit agent packages and OCI packages listed above.

### 7.4 Project structure

The agent expects the local project layout to include:

* the Python agent file
* the `Wallet_daTest` directory
* the `src` directory on the Python path

### 7.5 OCI model / service configuration

The agent uses:

* OCI Generative AI inference endpoint
* OCI speech endpoint
* OCI STT websocket endpoint
* LiveKit agent session with turn detection and VAD

Confirm that the region values in the code match your deployment.

### 7.6 Run the agent

Make sure your virtual environment is active. On first run only, download the required model files:

```bash
python main.py download-files
```

This only needs to be run once. Then start the agent:

```bash
python main.py dev
```

### 7.7 What the agent does

The agent is configured to:

* answer hotel policy and amenity questions from hotel docs
* use NL2SQL for room availability and booking queries
* use web search for Chicago-related questions
* create bookings in the Oracle database

---

## 8) React frontend UI setup

### 8.1 Install frontend dependencies

From the frontend directory:

```bash
npm install
```

### 8.2 Environment variables for the frontend

Create a frontend `.env` file if your app needs one. Common values look like:

```env
REACT_APP_LIVEKIT_URL=ws://your-livekit-server
REACT_APP_API_BASE_URL=http://your-backend-url
```

If your frontend uses Vite instead of Create React App, the variables may look like:

```env
VITE_LIVEKIT_URL=ws://your-livekit-server
VITE_API_BASE_URL=http://your-backend-url
```

### 8.3 Run the React app locally

This project uses Vite. From the `my-react-app` directory:

```bash
cd my-react-app
npm run dev
```

The frontend will be available at `http://localhost:5173/`.

### 8.4 Build for production

```bash
npm run build
```

---

## 9) Running the project

Once everything is set up, you need **4 terminals** running simultaneously. Run these in order:

**Terminal 1 — LiveKit server** (if running locally)
```bash
livekit-server --dev
```

**Terminal 2 — Token server** (from the project root)
```bash
.\livekit\Scripts\activate
uvicorn token_server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 — Agent** (from the project root, first run only needs download-files)
```bash
.\livekit\Scripts\activate
python main.py download-files
python main.py dev
```

**Terminal 4 — React frontend** (from the `my-react-app` directory)
```bash
cd my-react-app
npm run dev
```

The frontend will be available at `http://localhost:5173/`.

> **Note:** `python main.py download-files` only needs to be run once. After the first time, just run `python main.py dev` directly.

---

## 10) Recommended first-time setup order

1. Confirm OCI auth works (`oci session authenticate --region us-chicago-1`)
2. Confirm the Autonomous Database is **Started** in the OCI Console
3. Confirm the database wallet is in place and `.env` values are correct
4. Upload hotel documents to the OCI vector store and confirm `VECTOR_STORE_ID` is set in `main.py`
5. Run `demo_nl2sql.py` and wait for enrichment to complete
6. Confirm `GenerateSqlFromNl` succeeds at the end of the script
7. Run `python main.py download-files` (once only)
8. Start all four terminals as described in section 9

---

## 11) Troubleshooting

### Agent crashes with `DPY-6001: Service is not registered with the listener`

The Autonomous Database is stopped. Go to the OCI Console → Oracle Database → Autonomous Database, find your instance, and click **Start**. The agent will connect successfully once the database shows **Available**.

### Agent hangs on startup or times out connecting

This usually means the database connection is wrong, the wallet path is wrong, or the DB password / wallet password is incorrect.

Check:

* `DB_USER`
* `DB_PASSWORD`
* `DB_DSN`
* `WALLET_PASSWORD`
* `./Wallet_daTest`

### `search_hotel_documents` returns empty or irrelevant answers

Check that:

* hotel documents have been uploaded to the vector store referenced by `VECTOR_STORE_ID`
* `PROJECT_ID` and `VECTOR_STORE_ID` in `main.py` are correct
* the OCI user in `~/.oci/config` has access to the Generative AI project and vector store
* the `oci-genai-auth` package is installed

### `generateSqlFromNl` fails

Check that:

* enrichment finished successfully
* the semantic store ID is correct
* policies allow the semantic store resource principal to access DB Tools, secrets, database metadata, and Generative AI inference

### Frontend cannot connect

Check:

* the LiveKit URL
* API URLs
* CORS / proxy settings
* that the backend is actually running

---

## 12) Useful commands

Run the full semantic store setup, enrichment, and NL2SQL validation:

```bash
python demo_nl2sql.py
```

Download agent model files (first run only):

```bash
python main.py download-files
```

Start the token server:

```bash
uvicorn token_server:app --host 0.0.0.0 --port 8000 --reload
```

Start the LiveKit agent:

```bash
python main.py dev
```

Start the React frontend (from `my-react-app` directory):

```bash
npm run dev
```

---

## 13) Notes

* Replace placeholder OCIDs, schema names, and connection IDs in `demo_nl2sql.py` and `main.py` with your real OCI values.
* Keep OCI credentials and wallet files out of source control.
* If you change the semantic store schema or DB connections, rerun `demo_nl2sql.py` to rebuild enrichment.
* If you update hotel documents, re-upload them to the vector store — no script rerun is needed for the agent itself.
* The `GenerateSqlFromNl` test at the end of `demo_nl2sql.py` is the quickest way to confirm the NL2SQL path is healthy.
* Asking the running agent a hotel policy question (e.g. "What is check-in time?") is the quickest way to confirm the vector store path is healthy.
