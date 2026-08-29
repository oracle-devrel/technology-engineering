"""Run synchronous analyze_document calls for many chunks in parallel.

The synchronous API is stateless, so independent chunks can be analyzed
concurrently with a thread pool. The OCI SDK's default retry strategy
handles 429 throttling and transient 5xx errors with exponential backoff,
which keeps the pipeline polite against the per-tenancy rate limit.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import oci
import oci.ai_document.models as ai_document_models
from oci.util import to_dict

SUPPORTED_FEATURES = {
    "table": lambda: ai_document_models.DocumentTableExtractionFeature(
        feature_type="TABLE_EXTRACTION"
    ),
    "text": lambda: ai_document_models.DocumentTextExtractionFeature(
        feature_type="TEXT_EXTRACTION"
    ),
    "key_value": lambda: ai_document_models.DocumentKeyValueExtractionFeature(
        feature_type="KEY_VALUE_EXTRACTION"
    ),
}

DEFAULT_WORKERS = 4


class ParallelDocumentAnalyzer:
    def __init__(self, settings):
        oci_config = oci.config.from_file(settings.config_file, settings.profile)
        self.client = oci.ai_document.AIServiceDocumentClient(
            config=oci_config,
            retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
        )
        self.compartment_id = settings.compartment_id

    def _analyze_chunk(self, chunk, features, language, document_type):
        kwargs = {}
        if language:
            kwargs["language"] = language
        if document_type:
            kwargs["document_type"] = document_type

        started = time.perf_counter()
        response = self.client.analyze_document(
            analyze_document_details=ai_document_models.AnalyzeDocumentDetails(
                features=[SUPPORTED_FEATURES[name]() for name in features],
                document=ai_document_models.InlineDocumentDetails(
                    source="INLINE", data=chunk.data
                ),
                compartment_id=self.compartment_id,
                **kwargs,
            )
        )
        elapsed = time.perf_counter() - started
        return to_dict(response.data), elapsed

    def analyze(
        self,
        chunks,
        features=("table", "text"),
        language=None,
        document_type=None,
        max_workers=DEFAULT_WORKERS,
        on_chunk_done=None,
    ):
        """Analyze all chunks and return (results, timings), both in chunk order.

        results[i] pairs chunks[i] with its analyze_document response as a dict;
        timings[i] is that chunk's request wall time in seconds. Use
        max_workers=1 for a sequential baseline. on_chunk_done, if given, is
        called as chunks finish (out of order) for progress reporting.
        """
        unknown = set(features) - set(SUPPORTED_FEATURES)
        if unknown:
            raise ValueError(
                f"Unsupported features: {sorted(unknown)}. "
                f"Choose from {sorted(SUPPORTED_FEATURES)}."
            )

        results = [None] * len(chunks)
        timings = [0.0] * len(chunks)
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(
                    self._analyze_chunk, chunk, features, language, document_type
                ): chunk
                for chunk in chunks
            }
            for future in as_completed(futures):
                chunk = futures[future]
                result, elapsed = future.result()
                results[chunk.index] = (chunk, result)
                timings[chunk.index] = elapsed
                if on_chunk_done:
                    on_chunk_done(chunk, elapsed)
        return results, timings
