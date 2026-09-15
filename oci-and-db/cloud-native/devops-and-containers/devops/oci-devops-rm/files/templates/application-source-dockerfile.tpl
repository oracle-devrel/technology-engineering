FROM container-registry.oracle.com/os/oraclelinux:10-slim

LABEL org.opencontainers.image.title="${component_name}"
LABEL org.opencontainers.image.description="Sample application image for the OKE Helm starter stack"

CMD ["/usr/bin/sleep", "31536000"]
