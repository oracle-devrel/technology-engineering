# Copyright (c) 2025 Oracle and/or its affiliates.
FROM ubuntu:24.04

ENV PATH="/root/.local/bin:$PATH"

RUN apt-get update \
 && apt-get install -y curl pipx \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /appli

COPY pyproject.toml benchplot.py /appli/

RUN pipx install . && pipx ensurepath

CMD ["benchplot"]
