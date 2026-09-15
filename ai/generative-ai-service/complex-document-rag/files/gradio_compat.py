"""Compatibility shim for gradio 4.44.0 / gradio_client 1.3.0.

gradio_client.utils._json_schema_to_python_type crashes with
"TypeError: argument of type 'bool' is not iterable" when a component's JSON
schema contains a boolean ``additionalProperties`` (valid JSON Schema, e.g.
``additionalProperties: true``). Because get_api_info() runs on every page load,
this makes ``ui.launch()`` fail and then surface the misleading
"localhost is not accessible" error.

Importing this module patches the recursive converter to treat a non-dict
(bool) schema as ``Any``, which is what newer gradio_client releases do.
Remove once the pinned gradio version is upgraded past the fix.
"""
import gradio_client.utils as _gcu

if not getattr(_gcu, "_bool_schema_patch_applied", False):
    _original = _gcu._json_schema_to_python_type

    def _json_schema_to_python_type(schema, defs=None):
        if isinstance(schema, bool):
            return "Any"
        return _original(schema, defs)

    _gcu._json_schema_to_python_type = _json_schema_to_python_type
    _gcu._bool_schema_patch_applied = True
