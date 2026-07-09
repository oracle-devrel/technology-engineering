import hashlib
import json
import mimetypes
import os
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import faiss
import numpy as np
import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference import models


ROOT = Path(__file__).resolve().parent
KB_PATH = ROOT / "knowledge_base.json"

DEFAULT_EMBED_MODEL_ID = "cohere.embed-v4.0"
DEFAULT_RERANK_MODEL_ID = "cohere.rerank-v4.0-fast"
DEFAULT_REGION = "me-riyadh-1"
DEFAULT_TOP_K = 5

VECTOR_STORE_CACHE = {}


def get_env(name, default=None):
    value = os.getenv(name)
    return value if value not in (None, "") else default


def make_serving_mode(endpoint_env, model_env, default_model):
    endpoint_id = get_env(endpoint_env)
    model_id = get_env(model_env, default_model)

    if endpoint_id:
        return {
            "mode": models.DedicatedServingMode(endpoint_id=endpoint_id),
            "label": endpoint_id,
            "serving_mode_label": "DEDICATED",
        }

    return {
        "mode": models.OnDemandServingMode(model_id=model_id),
        "label": model_id,
        "serving_mode_label": "ON_DEMAND",
    }


def load_oci_settings():
    profile = get_env("OCI_CONFIG_PROFILE", "DEFAULT")
    config_path = get_env("OCI_CONFIG_FILE", "~/.oci/config")
    config = oci.config.from_file(config_path, profile)

    region = get_env("OCI_REGION", DEFAULT_REGION)
    config["region"] = region
    configured_compartment = config.get("compartment_id")
    compartment_id = get_env("OCI_COMPARTMENT_ID", configured_compartment)
    if not compartment_id:
        raise ValueError("Set OCI_COMPARTMENT_ID or include compartment_id in your OCI config.")

    service_endpoint = get_env(
        "OCI_GENAI_ENDPOINT",
        f"https://inference.generativeai.{region}.oci.oraclecloud.com",
    )
    client_kwargs = {}
    if service_endpoint:
        client_kwargs["service_endpoint"] = service_endpoint

    embed = make_serving_mode(
        "OCI_EMBED_ENDPOINT_ID",
        "OCI_EMBED_MODEL_ID",
        DEFAULT_EMBED_MODEL_ID,
    )
    rerank = make_serving_mode(
        "OCI_RERANK_ENDPOINT_ID",
        "OCI_RERANK_MODEL_ID",
        DEFAULT_RERANK_MODEL_ID,
    )

    return {
        "client": GenerativeAiInferenceClient(config, **client_kwargs),
        "compartment_id": compartment_id,
        "profile": profile,
        "region": region,
        "service_endpoint": service_endpoint,
        "embed_serving_mode": embed["mode"],
        "embed_serving_mode_label": embed["serving_mode_label"],
        "embed_model_label": embed["label"],
        "rerank_serving_mode": rerank["mode"],
        "rerank_serving_mode_label": rerank["serving_mode_label"],
        "rerank_model_label": rerank["label"],
        "compartment_source": (
            "OCI_COMPARTMENT_ID"
            if os.getenv("OCI_COMPARTMENT_ID")
            else "config compartment_id"
        ),
    }


def load_knowledge_base():
    with KB_PATH.open("r", encoding="utf-8") as file:
        docs = json.load(file)

    if not isinstance(docs, list) or not docs:
        raise ValueError("knowledge_base.json must contain at least one document.")
    return docs


def extract_document_text(document):
    if isinstance(document, str):
        return document

    title = document.get("title", "")
    text = document.get("text", "")
    tags = ", ".join(document.get("tags", []))
    source = document.get("source", "")
    return f"Title: {title}\nSource: {source}\nTags: {tags}\nText: {text}".strip()


def public_document(document):
    return {
        "id": document.get("id"),
        "title": document.get("title"),
        "source": document.get("source"),
        "text": document.get("text"),
        "tags": document.get("tags", []),
        "answer": document.get("answer", ""),
    }


def normalize_rank_index(index, total):
    if isinstance(index, int) and 0 <= index < total:
        return index
    if isinstance(index, int) and 1 <= index <= total:
        return index - 1
    return None


def normalize_matrix(vectors):
    matrix = np.asarray(vectors, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        raise ValueError("Embedding response did not contain a 2D vector array.")
    faiss.normalize_L2(matrix)
    return matrix


def extract_embeddings(data):
    if getattr(data, "embeddings", None):
        return data.embeddings

    by_type = getattr(data, "embeddings_by_type", None)
    if isinstance(by_type, dict):
        for key in ("float", "FLOAT", models.EmbedTextDetails.EMBEDDING_TYPES_FLOAT):
            if key in by_type:
                return by_type[key]

    raise ValueError("OCI embedding response did not include float embeddings.")


def embed_texts(settings, texts, input_type):
    if not texts:
        return [], None, None

    batch_size = int(get_env("OCI_EMBED_BATCH_SIZE", "96"))
    embeddings = []
    model_id = None
    model_version = None

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        details = models.EmbedTextDetails(
            inputs=batch,
            compartment_id=settings["compartment_id"],
            serving_mode=settings["embed_serving_mode"],
            truncate=models.EmbedTextDetails.TRUNCATE_END,
            input_type=input_type,
            embedding_types=[models.EmbedTextDetails.EMBEDDING_TYPES_FLOAT],
        )
        response = settings["client"].embed_text(details)
        embeddings.extend(extract_embeddings(response.data))
        model_id = response.data.model_id or model_id
        model_version = response.data.model_version or model_version

    return embeddings, model_id, model_version


def vector_store_fingerprint(docs, settings):
    payload = {
        "docs": docs,
        "embed_model": settings["embed_model_label"],
        "region": settings["region"],
        "endpoint": settings["service_endpoint"],
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_vector_store(settings):
    docs = load_knowledge_base()
    fingerprint = vector_store_fingerprint(docs, settings)
    cached = VECTOR_STORE_CACHE.get("store")
    if cached and cached["fingerprint"] == fingerprint:
        return cached

    document_texts = [extract_document_text(doc) for doc in docs]
    embeddings, model_id, model_version = embed_texts(
        settings,
        document_texts,
        models.EmbedTextDetails.INPUT_TYPE_SEARCH_DOCUMENT,
    )
    vectors = normalize_matrix(embeddings)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    store = {
        "fingerprint": fingerprint,
        "docs": docs,
        "index": index,
        "dimension": int(vectors.shape[1]),
        "embedding_model": model_id or settings["embed_model_label"],
        "embedding_model_version": model_version,
        "metric": "cosine similarity",
        "engine": "FAISS IndexFlatIP",
    }
    VECTOR_STORE_CACHE["store"] = store
    return store


def vector_search(settings, query, top_k):
    store = get_vector_store(settings)
    query_embeddings, model_id, model_version = embed_texts(
        settings,
        [query],
        models.EmbedTextDetails.INPUT_TYPE_SEARCH_QUERY,
    )
    query_vector = normalize_matrix(query_embeddings)
    limit = min(top_k, len(store["docs"]))
    scores, indexes = store["index"].search(query_vector, limit)

    results = []
    for rank, (score, index) in enumerate(zip(scores[0], indexes[0]), start=1):
        if index < 0:
            continue
        doc = public_document(store["docs"][int(index)])
        doc["vectorRank"] = rank
        doc["vectorScore"] = float(score)
        results.append(doc)

    vector_meta = {
        "engine": store["engine"],
        "metric": store["metric"],
        "embeddingModel": model_id or store["embedding_model"],
        "embeddingModelVersion": model_version or store["embedding_model_version"],
        "dimension": store["dimension"],
        "topK": limit,
    }
    return results, vector_meta


def rerank_results(settings, query, vector_results):
    documents = [extract_document_text(doc) for doc in vector_results]
    details = models.RerankTextDetails(
        input=query,
        compartment_id=settings["compartment_id"],
        serving_mode=settings["rerank_serving_mode"],
        documents=documents,
        top_n=len(documents),
        is_echo=False,
    )
    response = settings["client"].rerank_text(details)

    ranked = []
    used = set()
    for rank in response.data.document_ranks:
        normalized_index = normalize_rank_index(rank.index, len(vector_results))
        if normalized_index is None or normalized_index in used:
            continue
        used.add(normalized_index)
        doc = dict(vector_results[normalized_index])
        doc["rerankScore"] = float(rank.relevance_score)
        ranked.append(doc)

    for index, doc in enumerate(vector_results):
        if index in used:
            continue
        doc = dict(doc)
        doc["rerankScore"] = None
        ranked.append(doc)

    for index, doc in enumerate(ranked, start=1):
        doc["rerankRank"] = index

    return ranked, {
        "provider": "OCI Generative AI RerankText",
        "model": response.data.model_id or settings["rerank_model_label"],
        "modelVersion": response.data.model_version,
        "servingMode": settings["rerank_serving_mode_label"],
        "scoreName": "relevance score",
    }


def make_error_payload(error):
    if isinstance(error, oci.exceptions.ServiceError):
        return {
            "error": "ServiceError",
            "status": error.status,
            "code": error.code,
            "message": error.message,
            "opcRequestId": error.request_id,
        }

    return {
        "error": error.__class__.__name__,
        "message": str(error),
    }


class Handler(SimpleHTTPRequestHandler):
    server_version = "OCIRerankerDemo/2.0"

    def translate_path(self, path):
        parsed = urlparse(path)
        requested = parsed.path.lstrip("/") or "index.html"
        safe_parts = [part for part in requested.split("/") if part not in ("", ".", "..")]
        return str(ROOT.joinpath(*safe_parts))

    def log_message(self, format, *args):
        return

    def send_json(self, status, payload):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            try:
                settings = load_oci_settings()
                self.send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "profile": settings["profile"],
                        "region": settings["region"],
                        "endpoint": settings["service_endpoint"],
                        "vectorStore": "OCI embeddings + FAISS",
                        "embeddingModel": settings["embed_model_label"],
                        "rerankModel": settings["rerank_model_label"],
                        "embeddingServingMode": settings["embed_serving_mode_label"],
                        "rerankServingMode": settings["rerank_serving_mode_label"],
                        "compartmentSource": settings["compartment_source"],
                    },
                )
            except Exception as error:
                self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, **make_error_payload(error)})
            return

        path = Path(self.translate_path(self.path))
        if path.is_dir():
            path = path / "index.html"
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in ("/api/search", "/api/rerank"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            query = payload.get("query", "").strip()
            top_k = int(payload.get("topK") or payload.get("topN") or DEFAULT_TOP_K)
            use_reranker = bool(payload.get("useReranker", parsed.path == "/api/rerank"))

            if not query:
                self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "BadRequest", "message": "query is required"})
                return

            top_k = max(1, min(top_k, 20))
            started = time.perf_counter()
            settings = load_oci_settings()
            vector_results, vector_meta = vector_search(settings, query, top_k)
            vector_finished = time.perf_counter()

            reranked_results = []
            reranker_meta = {
                "enabled": False,
                "model": settings["rerank_model_label"],
                "servingMode": settings["rerank_serving_mode_label"],
                "scoreName": "relevance score",
            }
            if use_reranker:
                reranked_results, reranker_meta = rerank_results(settings, query, vector_results)
                reranker_meta["enabled"] = True

            active_results = reranked_results if use_reranker and reranked_results else vector_results
            answer_doc = active_results[0] if active_results else {}
            finished = time.perf_counter()

            self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "query": query,
                    "answer": answer_doc.get("answer", ""),
                    "answerSourceId": answer_doc.get("id"),
                    "answerMode": "reranker" if use_reranker else "vector",
                    "vector": vector_meta,
                    "reranker": reranker_meta,
                    "vectorResults": vector_results,
                    "rerankedResults": reranked_results,
                    "timingsMs": {
                        "vector": round((vector_finished - started) * 1000),
                        "reranker": round((finished - vector_finished) * 1000),
                        "total": round((finished - started) * 1000),
                    },
                },
            )
        except Exception as error:
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, **make_error_payload(error)})


def main():
    host = get_env("HOST", "127.0.0.1")
    port = int(get_env("PORT", "4173"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"OCI Reranker demo running at http://{host}:{port}")
    print("Using OCI config from", get_env("OCI_CONFIG_FILE", "~/.oci/config"))
    print("Using OCI region", get_env("OCI_REGION", DEFAULT_REGION))
    print("Using OCI embedding model", get_env("OCI_EMBED_MODEL_ID", DEFAULT_EMBED_MODEL_ID))
    print("Using OCI reranker model", get_env("OCI_RERANK_MODEL_ID", DEFAULT_RERANK_MODEL_ID))
    server.serve_forever()


if __name__ == "__main__":
    main()
