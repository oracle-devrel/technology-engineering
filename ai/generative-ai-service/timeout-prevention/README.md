# OCI Generative AI Timeout Prevention Toolkit

This asset provides a practical, production-ready Python implementation demonstrating how to proactively prevent timeouts when interacting with **OCI Generative AI** using the OCI Python SDK.
The repository includes a robust code sample and a supporting presentation that outlines the resilience techniques implemented.

Reviewed: 03.12.2025

# When to use this asset?

This asset should be used by **developers, architects, and platform engineers** who integrate OCI Generative AI into applications and need to:

* Prevent request timeouts before they occur
* Improve reliability of AI-driven workloads
* Implement adaptive retry and backoff strategies
* Apply proactive model routing and fallback patterns
* Enhance observability through structured request logging
* Protect systems with circuit breaker mechanisms

It is particularly valuable in environments with variable latency, heavy concurrency, or strict user-experience requirements.

# How to use this asset?

1. Configure OCI credentials in `~/.oci/config` with access to Generative AI services.
2. Install the OCI Python SDK:

   ```bash
   pip install oci
   ```
3. Open `timeout_safe_client.py` and update the model OCIDs (`FAST_MODEL` and `ROBUST_MODEL`).
4. Run the sample client:

   ```bash
   python timeout_safe_client.py
   ```
5. Integrate the `call_genai()` function into your application to benefit from:

   * Proactive timeout prevention
   * Exponential backoff retry strategy
   * Request-safe retry tokens
   * Connection and read timeout configuration
   * Automatic fallback to more capable models
   * Circuit breaker safety to avoid cascading failures
   * Logging focused on response time and failure insight

The included PDF presentation provides additional context on the concepts and reasoning behind these preventative patterns.

# Useful Links

- [OCI Python SDK Documentation](https://docs.oracle.com/en-us/iaas/tools/python/latest/index.html)

  - Reference for retry behavior, SDK configuration, and Generative AI APIs.
- [OCI Generative AI Service](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
  - Detailed information on OCI Generative AI Service 

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.