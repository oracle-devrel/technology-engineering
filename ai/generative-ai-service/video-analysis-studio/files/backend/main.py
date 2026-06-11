# Copyright (c) 2026 Oracle and/or its affiliates.
# SPDX-License-Identifier: UPL-1.0

import mimetypes
import logging
import os
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv, set_key

from .model_catalog import (
    build_static_model_catalog,
    discover_model_catalog,
    get_supported_model_ids,
    is_supported_public_model_id,
)
from .oci_video_analysis import VideoAnalysisConfigurationError, analyze_video_with_oci_gemini

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ENV_PATH = Path(
    os.getenv(
        "OCI_VIDEO_STUDIO_ENV_FILE",
        str(Path.home() / ".oci-genai-video-analysis-studio.env"),
    )
)

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(RUNTIME_ENV_PATH, override=True)

MAX_UPLOAD_MB = min(int(os.getenv("MAX_UPLOAD_MB", "37")), 37)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
CHUNK_SIZE = 1024 * 1024

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", ",".join(DEFAULT_ALLOWED_ORIGINS)).split(",")
    if origin.strip()
]

app = FastAPI(title="OCI GenAI Video Analysis Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=os.getenv(
        "ALLOWED_ORIGIN_REGEX",
        r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    ),
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


def _resolve_video_mime_type(upload: UploadFile) -> str:
    content_type = upload.content_type or ""
    guessed_type, _ = mimetypes.guess_type(upload.filename or "")
    mime_type = content_type if content_type.startswith("video/") else guessed_type or ""

    if not mime_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail="Only video uploads are supported. Choose a file with a video MIME type.",
        )

    return mime_type


def _env_auth_settings() -> dict[str, str]:
    return {
        "auth_profile": os.getenv("OCI_CONFIG_PROFILE", "DEFAULT").strip() or "DEFAULT",
        "auth_file_location": os.getenv("OCI_CONFIG_FILE", "~/.oci/config").strip()
        or "~/.oci/config",
    }


def _is_env_fallback_configured() -> bool:
    return bool(
        os.getenv("OCI_CONFIG_PROFILE")
        or os.getenv("OCI_CONFIG_FILE")
    )


def _save_successful_settings_to_env(
    *,
    compartment_id: str,
    service_endpoint: str,
    region: str,
    model_id: str,
    auth_profile: str,
    auth_file_location: str,
) -> None:
    RUNTIME_ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_ENV_PATH.touch(exist_ok=True)
    values = {
        "OCI_COMPARTMENT_ID": compartment_id,
        "GENAI_ENDPOINT": service_endpoint,
        "GENAI_REGION": region,
        "DEFAULT_MODEL_ID": model_id,
        "OCI_CONFIG_PROFILE": auth_profile,
        "OCI_CONFIG_FILE": auth_file_location,
    }

    for key, value in values.items():
        clean_value = value.strip()
        if clean_value:
            set_key(str(RUNTIME_ENV_PATH), key, clean_value)
            os.environ[key] = clean_value


async def _save_upload_to_temp_file(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "upload.mp4").suffix or ".mp4"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = Path(temp_file.name)
    total_size = 0

    try:
        with temp_file:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Uploaded video exceeds the {MAX_UPLOAD_MB} MB limit.",
                    )

                temp_file.write(chunk)

        if total_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded video is empty.")

        return temp_path
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


@app.get("/api/health")
def health() -> dict[str, str | list[str]]:
    return {"status": "ok", "supported_models": sorted(get_supported_model_ids())}


@app.get("/api/model-catalog")
def model_catalog() -> dict:
    return build_static_model_catalog()


@app.post("/api/model-catalog/discover")
def refresh_model_catalog(
    compartment_id: Annotated[str, Form()] = "",
    auth_profile: Annotated[str, Form()] = "DEFAULT",
    auth_file_location: Annotated[str, Form()] = "~/.oci/config",
) -> JSONResponse:
    try:
        return JSONResponse(
            content=discover_model_catalog(
                compartment_id=compartment_id,
                auth_profile=auth_profile,
                auth_file_location=auth_file_location,
            )
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except Exception as exc:
        logger.exception(
            "Could not refresh OCI model availability. Returning the static catalog. Error: %s",
            exc,
        )
        return JSONResponse(content=build_static_model_catalog())


@app.post("/api/analyze-video")
async def analyze_video(
    video: Annotated[UploadFile, File()],
    prompt: Annotated[str, Form()],
    model_id: Annotated[str, Form()],
    analysis_mode: Annotated[str, Form()],
    compartment_id: Annotated[str, Form()] = "",
    service_endpoint: Annotated[str, Form()] = "",
    region: Annotated[str, Form()] = "",
    model_ocid: Annotated[str | None, Form()] = None,
    auth_profile: Annotated[str, Form()] = "DEFAULT",
    auth_file_location: Annotated[str, Form()] = "~/.oci/config",
) -> JSONResponse:
    clean_model_ocid = (model_ocid or "").strip()
    selected_auth_profile = auth_profile.strip() or "DEFAULT"
    selected_auth_file_location = auth_file_location.strip() or "~/.oci/config"

    resolved_model_id = clean_model_ocid or model_id.strip() or os.getenv("DEFAULT_MODEL_ID", "")
    resolved_compartment_id = compartment_id.strip() or os.getenv("OCI_COMPARTMENT_ID", "")
    resolved_service_endpoint = service_endpoint.strip() or os.getenv("GENAI_ENDPOINT", "")
    resolved_region = region.strip() or os.getenv("GENAI_REGION", "")

    if not clean_model_ocid and not is_supported_public_model_id(resolved_model_id):
        return JSONResponse(
            status_code=400,
            content={
                "error": (
                    f"Unsupported model_id '{resolved_model_id}'. "
                    f"Supported model IDs: {', '.join(sorted(get_supported_model_ids()))}."
                )
            },
        )

    if not resolved_region:
        return JSONResponse(status_code=400, content={"error": "Region is required."})

    mime_type = _resolve_video_mime_type(video)
    temp_path: Path | None = None

    try:
        temp_path = await _save_upload_to_temp_file(video)
        used_auth_profile = selected_auth_profile
        used_auth_file_location = selected_auth_file_location
        try:
            result = analyze_video_with_oci_gemini(
                video_path=temp_path,
                prompt=prompt,
                model_id=resolved_model_id,
                mime_type=mime_type,
                compartment_id=resolved_compartment_id,
                service_endpoint=resolved_service_endpoint,
                auth_profile=selected_auth_profile,
                auth_file_location=selected_auth_file_location,
            )
        except RuntimeError as selected_auth_error:
            if not _is_env_fallback_configured():
                raise

            env_auth = _env_auth_settings()
            used_auth_profile = env_auth["auth_profile"]
            used_auth_file_location = env_auth["auth_file_location"]
            try:
                result = analyze_video_with_oci_gemini(
                    video_path=temp_path,
                    prompt=prompt,
                    model_id=resolved_model_id,
                    mime_type=mime_type,
                    compartment_id=resolved_compartment_id,
                    service_endpoint=resolved_service_endpoint,
                    auth_profile=env_auth["auth_profile"],
                    auth_file_location=env_auth["auth_file_location"],
                )
            except RuntimeError as env_auth_error:
                raise RuntimeError(
                    "OCI GenAI authentication failed with the selected UI settings and "
                    "also failed with the server .env fallback. Check the selected "
                    "authentication method, OCI config profile/path if applicable, and "
                    "server fallback auth variables."
                ) from env_auth_error
        try:
            _save_successful_settings_to_env(
                compartment_id=resolved_compartment_id,
                service_endpoint=resolved_service_endpoint,
                region=resolved_region,
                model_id=resolved_model_id,
                auth_profile=used_auth_profile,
                auth_file_location=used_auth_file_location,
            )
        except Exception:
            pass
        return JSONResponse(
            content={
                "output": result.output,
                "model_id": resolved_model_id,
                "analysis_mode": analysis_mode,
                "api_metadata": result.metadata,
            }
        )
    except VideoAnalysisConfigurationError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except HTTPException:
        raise
    except RuntimeError as exc:
        return JSONResponse(status_code=502, content={"error": str(exc)})
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "error": (
                    "Unexpected backend error while processing the video. "
                    "Check the FastAPI terminal logs for details."
                )
            },
        )
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
