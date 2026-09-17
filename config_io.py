# -*- coding: utf-8 -*-
"""
Save/load the app's input configuration (everything the user typed across
the tabs) as a JSON file, so a session can be closed and resumed later
without re-entering every parameter.

How it works: every input widget that should be restorable has an explicit
``key=`` (see ui_inputs.py). That makes Streamlit mirror its value into
``st.session_state[key]``. Saving just dumps every JSON-serialisable entry
of ``st.session_state``; loading writes those entries back into
``st.session_state`` *before* the widgets are created on the next run, so
each widget picks up the restored value as its own state.

Not covered: the two file_uploader widgets (environmental data, field
layout) — Streamlit does not allow programmatically restoring an uploaded
file's content into a file_uploader widget, so those must be re-uploaded
by hand after loading a configuration.
"""

import datetime as dt
import json
import re

# Streamlit forbids ever pre-setting a button's session_state entry — it
# raises the moment the *widget* is instantiated later in the script, not
# when the value is assigned, so it can't be caught defensively at load
# time. These are every explicit button `key=` pattern used in ui_inputs.py;
# they carry no meaningful state to restore anyway (just "was clicked").
_BUTTON_KEY_PATTERNS = [
    re.compile(r"^irr_del_\d+$"),
    re.compile(r"^hf_del_\d+$"),
    re.compile(r"^del_grp_\d+$"),
    re.compile(r"^add_\d+$"),
    re.compile(r"^del_\d+_\d+$"),
]


def _is_button_key(key: str) -> bool:
    return any(p.match(key) for p in _BUTTON_KEY_PATTERNS)


def _json_default(obj):
    if isinstance(obj, (dt.date, dt.datetime)):
        return {"__date__": obj.isoformat()}
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _json_object_hook(d):
    if "__date__" in d:
        return dt.date.fromisoformat(d["__date__"])
    return d


def serialize_config(session_state) -> str:
    """Dump every JSON-serialisable entry of session_state to a JSON string.

    Keys starting with "_" are treated as internal app bookkeeping (e.g. the
    load-configuration file_uploader's own rotating key) and are skipped —
    Streamlit forbids writing to a file_uploader's session_state key once
    that widget has been instantiated, so re-applying one from a saved
    config would crash on load.
    """
    data = {}
    for key, value in session_state.items():
        if key.startswith("_") or _is_button_key(key):
            continue
        try:
            json.dumps(value, default=_json_default)
        except TypeError:
            continue  # not serialisable (e.g. simulation results, uploaded files) -> skip
        data[key] = value
    return json.dumps(data, default=_json_default, indent=2)


def apply_config(session_state, json_text: str) -> None:
    """Parse a config JSON and write its entries back into session_state."""
    data = json.loads(json_text, object_hook=_json_object_hook)

    # plant_periods is keyed by circuit index (int) in the app, but JSON
    # object keys are always strings -> convert back.
    if isinstance(data.get("plant_periods"), dict):
        data["plant_periods"] = {int(k): v for k, v in data["plant_periods"].items()}

    for key, value in data.items():
        try:
            session_state[key] = value
        except Exception:
            # Some widget types (buttons, file_uploaders) don't allow their
            # session_state entry to be set programmatically. Their saved
            # value is inert bookkeeping anyway (e.g. a button's last-click
            # bool) — skip rather than let one bad key abort the whole load.
            continue
