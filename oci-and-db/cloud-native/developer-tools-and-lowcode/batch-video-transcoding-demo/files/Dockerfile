
FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y ffmpeg curl python3 python3-pip unzip && \
    pip3 install oci-cli && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /video && chmod 777 /video

WORKDIR /video

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
