# Build the manager binary.
ARG GO_VERSION=1.26.0
FROM golang:${GO_VERSION} AS builder

WORKDIR /workspace

COPY go.mod go.sum ./
RUN go mod download

COPY . .

ARG TARGETOS=linux
ARG TARGETARCH=amd64
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} go build -trimpath -ldflags="-s -w" -o manager ./cmd

# Run as a non-root user in a minimal image.
FROM gcr.io/distroless/static-debian12:nonroot

WORKDIR /
COPY --from=builder /workspace/manager /manager

USER 65532:65532
ENTRYPOINT ["/manager"]
