from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

from core.models import TranslateRequest, TranslateResponse
from core.translator import translate_stream, translate_sync, translate_async

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Translation API", version="1.0.0")


@app.get("/", response_class=HTMLResponse)
def welcome():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OCI Translator</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #fef2f2 0%, #f0f4ff 100%);
    }
    .card {
      background: #fff;
      border-radius: 16px;
      padding: 48px;
      max-width: 560px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }
    h1 {
      font-size: 2rem;
      font-weight: 700;
      color: #1a1a1a;
      margin-bottom: 12px;
    }
    .subtitle {
      color: #6b7280;
      font-size: 1rem;
      margin-bottom: 16px;
    }
    .endpoints {
      color: #4b5563;
      font-size: 0.95rem;
      margin-bottom: 32px;
      line-height: 1.6;
    }
    code {
      background: #f3f4f6;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.875rem;
    }
    .buttons { display: flex; gap: 12px; }
    .btn {
      display: inline-block;
      padding: 10px 24px;
      border-radius: 24px;
      font-size: 0.95rem;
      font-weight: 500;
      text-decoration: none;
      cursor: pointer;
      transition: opacity 0.2s;
    }
    .btn:hover { opacity: 0.85; }
    .btn-primary {
      background: #b91c1c;
      color: #fff;
      border: none;
    }
    .btn-secondary {
      background: #fff;
      color: #1a1a1a;
      border: 1px solid #d1d5db;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>OCI Translator</h1>
    <p class="subtitle">Welcome to the OCI Translator API.</p>
    <p class="endpoints">
      Use <code>POST /translate</code> for synchronous translation and
      <code>POST /translate/stream</code> for streaming responses.
    </p>
    <div class="buttons">
      <a href="/docs" class="btn btn-primary">Open API Docs</a>
      <a href="/redoc" class="btn btn-secondary">Open ReDoc</a>
    </div>
  </div>
</body>
</html>"""


@app.post("/translate", response_model=TranslateResponse)
#def translate(req: TranslateRequest):
async def translate(req: TranslateRequest):
    try:
        #return translate_sync(req)
        return await translate_async(req)
    except HTTPException:
        raise
    except Exception as e:
        #logger.exception("Sync translation failed")
        logger.exception("Async translation failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate/stream")
def translate_sse(req: TranslateRequest):
    def event_generator():
        try:
            for chunk in translate_stream(req):
                if chunk == "[DONE]":
                    yield "data: [DONE]\n\n"
                else:
                    yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.exception("Stream translation failed")
            yield f"data: {{\"error\": \"{e}\"}}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
