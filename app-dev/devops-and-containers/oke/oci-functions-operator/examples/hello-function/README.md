# Hello Function Runtime Image

Minimal OCI Functions-compatible Python function for the managed Function demo.
This builds the function runtime image that OCI Functions runs. It is not the
operator/controller image that runs in OKE.

The layout follows the Fn Project Python FDK contract: `func.yaml` declares
`runtime: python` and the image starts the handler through
`/python/bin/fdk /function/func.py handler`.

The function accepts JSON input and returns JSON output:

```json
{
  "ok": true,
  "greeting": "hello from oke functions operator",
  "input": {
    "name": "Ron",
    "index": 0
  }
}
```

The `greeting` value comes from the `GREETING` function config/environment variable.

## Preferred: Build With Fn CLI

Use the Fn CLI so the image is built and tagged as an OCI Functions/Fn image.
The image must be pushed to same-region OCIR. For the Jeddah demo, use:

```text
jed.ocir.io/<TENANCY_NAMESPACE>/hello-function:<tag>
```

Do not use GHCR for the function runtime image. GHCR may be fine for the
operator image, but OCI Functions should pull this runtime image from OCIR in
the same region as the Functions application.

The default tag is the `version` in `func.yaml` (`0.0.1`). Change that value
before building if you want a different tag.

Log in to Jeddah OCIR with the container engine used by Fn CLI:

```sh
docker login jed.ocir.io
# or:
podman login jed.ocir.io
```

Build and push:

```sh
cd examples/hello-function
fn build
fn push --registry jed.ocir.io/<TENANCY_NAMESPACE>
```

The pushed image reference is:

```text
jed.ocir.io/<TENANCY_NAMESPACE>/hello-function:0.0.1
```

Alternatively, deploy through Fn CLI if your Fn context is configured for OCI
Functions in `me-jeddah-1`:

```sh
cd examples/hello-function
fn deploy --app <OCI_FUNCTIONS_APPLICATION_NAME> --registry jed.ocir.io/<TENANCY_NAMESPACE> --no-bump
```

## Manual: Build With Podman

Only use the manual path with this Dockerfile or an equivalent Fn Python FDK
layout. OCI Functions cannot invoke an arbitrary container image; it must use
the Fn runtime layout and FDK entrypoint.

For an application shape of `GENERIC_X86`, build the image for `linux/amd64`.
This matters on Apple Silicon, where the host architecture is usually ARM64:

```sh
export TENANCY_NAMESPACE="<TENANCY_NAMESPACE>"
export TAG="0.0.1"

podman build --platform linux/amd64 \
  --format docker \
  -t "jed.ocir.io/${TENANCY_NAMESPACE}/hello-function:${TAG}" \
  examples/hello-function
```

`--format docker` uses the Docker v2 schema 2 manifest format, which is the
most compatible choice when testing OCI Functions image pulls.

Push the image:

```sh
podman push "jed.ocir.io/${TENANCY_NAMESPACE}/hello-function:${TAG}"
```

Use this image as `<FUNCTION_IMAGE>` in `config/samples/functions_v1alpha1_function_managed.yaml`.

If you configure the OCI Functions application for an ARM shape, build and tag
an ARM64-compatible function image instead. The application shape and image
architecture must match.
