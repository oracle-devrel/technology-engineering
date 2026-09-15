import io
import json
import os

from fdk import response


def handler(ctx, data: io.BytesIO = None):
    greeting = os.getenv("GREETING", "hello from oke functions operator")
    payload = {}

    if data is not None:
        raw_body = data.getvalue()
        if raw_body:
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError as exc:
                return response.Response(
                    ctx,
                    response_data=json.dumps({
                        "ok": False,
                        "error": "request body must be valid JSON",
                        "details": str(exc),
                    }),
                    headers={"Content-Type": "application/json"},
                    status_code=400,
                )

    return response.Response(
        ctx,
        response_data=json.dumps({
            "ok": True,
            "greeting": greeting,
            "input": payload,
        }),
        headers={"Content-Type": "application/json"},
    )
