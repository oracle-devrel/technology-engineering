# Copyright (c) 2025 Oracle and/or its affiliates.
FROM ubuntu:24.04

ENV PATH="/root/.local/bin:/root/.local/share/pipx/venvs/genai-perf/bin/:$PATH"
ARG GENAI_PERF_VERSION=0.0.12

RUN apt-get update \
 && apt-get install -y curl pipx \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN pipx install genai-perf==${GENAI_PERF_VERSION} && pipx ensurepath
RUN curl -o /root/.local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/refs/heads/master/wait-for-it.sh
RUN chmod +x /root/.local/bin/wait-for-it.sh
