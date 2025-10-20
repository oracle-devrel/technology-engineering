from typing import Any, Callable, Optional, TypeVar
import inspect
import json
import logging

from streamlit.delta_generator import DeltaGenerator
from streamlit.external.langchain.streamlit_callback_handler import StreamlitCallbackHandler
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from langchain_core.callbacks.base import BaseCallbackHandler


def _from_json(data):
    if isinstance(data, str):
        try:
            return json.loads(data)
        except Exception as e:
            # logging.warning(e)
            return data
    elif isinstance(data, list):
        return [_from_json(e) for e in data]
    elif isinstance(data, dict):
        return {k: _from_json(v) for k, v in data.items()}
    return data


def attempt_to_write_json(container, data):
    new_data = _from_json(data)
    if isinstance(new_data, str):
        container.markdown(new_data)
    else:
        container.container().json(new_data)


class CustomCallbackHandler(StreamlitCallbackHandler):
    def on_tool_end(
        self,
        output: Any,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        thought = self._require_current_thought()
        attempt_to_write_json(thought.container, output.content)
        self._complete_current_thought()


def get_streamlit_cb(parent_container: DeltaGenerator) -> BaseCallbackHandler:
    fn_return_type = TypeVar('fn_return_type')

    def add_streamlit_context(fn: Callable[..., fn_return_type]) -> Callable[..., fn_return_type]:
        ctx = get_script_run_ctx()

        def wrapper(*args, **kwargs) -> fn_return_type:
            add_script_run_ctx(ctx=ctx)
            return fn(*args, **kwargs)

        return wrapper

    st_cb = CustomCallbackHandler(
        parent_container,
        collapse_completed_thoughts=True,
        expand_new_thoughts=True,
    )

    for method_name, method_func in inspect.getmembers(st_cb, predicate=inspect.ismethod):
        if method_name.startswith('on_'):
            setattr(st_cb, method_name, add_streamlit_context(method_func))
    return st_cb
