# -*- coding: utf-8 -*-
"""
Round-trip tests for config_io.serialize_config / apply_config.

config_io talks to session_state purely through dict-like access
(.items(), __getitem__, __setitem__), so a plain dict stands in for
st.session_state here — no Streamlit runtime needed.
"""

import datetime as dt

import numpy as np
import pytest

from config_io import serialize_config, apply_config


def test_round_trip_preserves_plain_values():
    state = {"cfg_Tg": 13.0, "cfg_mode": "Single BHE", "cfg_n_steps": 276}

    loaded = {}
    apply_config(loaded, serialize_config(state))

    assert loaded == state


def test_round_trip_preserves_dates():
    state = {"env_tau_date": dt.date(2024, 1, 1)}

    loaded = {}
    apply_config(loaded, serialize_config(state))

    assert loaded["env_tau_date"] == dt.date(2024, 1, 1)
    assert isinstance(loaded["env_tau_date"], dt.date)


def test_serialize_skips_underscore_prefixed_keys():
    state = {"_config_upload_nonce": 3, "cfg_Tg": 13.0}

    loaded = {}
    apply_config(loaded, serialize_config(state))

    assert "_config_upload_nonce" not in loaded
    assert loaded == {"cfg_Tg": 13.0}


def test_serialize_skips_button_keys():
    state = {"add_0": True, "del_1_2": True, "del_grp_0": True, "cfg_Tg": 13.0}

    loaded = {}
    apply_config(loaded, serialize_config(state))

    assert loaded == {"cfg_Tg": 13.0}


def test_serialize_skips_non_json_serialisable_values():
    state = {"T_history": np.zeros(3), "cfg_Tg": 13.0}

    loaded = {}
    apply_config(loaded, serialize_config(state))

    assert loaded == {"cfg_Tg": 13.0}


def test_plant_periods_keys_round_trip_as_ints():
    state = {"plant_periods": {0: [], 1: [("a", "b")]}}

    loaded = {}
    apply_config(loaded, serialize_config(state))

    assert set(loaded["plant_periods"].keys()) == {0, 1}
    assert all(isinstance(k, int) for k in loaded["plant_periods"].keys())


def test_apply_config_skips_keys_that_refuse_assignment():
    class PickySessionState(dict):
        def __setitem__(self, key, value):
            if key == "readonly_widget":
                raise Exception("Streamlit forbids setting this widget's state")
            super().__setitem__(key, value)

    saved = serialize_config({"readonly_widget": True, "cfg_Tg": 13.0})

    state = PickySessionState()
    apply_config(state, saved)  # must not raise despite the bad key

    assert dict(state) == {"cfg_Tg": 13.0}
