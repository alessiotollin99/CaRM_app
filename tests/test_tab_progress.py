# -*- coding: utf-8 -*-
"""
Unit tests for tab_progress.py's "filled in" logic.

Like test_config_io.py, this talks to session_state purely through
dict-like access — a plain dict stands in for st.session_state, no
Streamlit runtime needed.
"""

from defaults import (
    D0_PIPE_TYPE_OVERRIDES,
    FIELD_DEFAULTS,
    GROUND_DEFAULTS,
    PLANT_DEFAULTS,
    SINGLE_UTUBE_DEFAULTS,
)
from tab_progress import TAB_NAMES, build_tab_labels, tab_progress


# =============================================================================
# Fresh state
# =============================================================================

def test_fresh_state_reports_every_tab_not_filled_single_bhe():
    progress = tab_progress({}, mode="Single BHE")

    assert set(progress.keys()) == set(TAB_NAMES) - {"Field Layout"}
    assert all(filled is False for filled in progress.values())


def test_fresh_state_reports_every_tab_not_filled_multi_bhe():
    progress = tab_progress({}, mode="Multi BHE — Parallel")

    assert set(progress.keys()) == set(TAB_NAMES)
    assert all(filled is False for filled in progress.values())


# =============================================================================
# Field Layout: mode-gated inclusion
# =============================================================================

def test_field_layout_excluded_in_single_bhe_mode():
    progress = tab_progress({}, mode="Single BHE")
    assert "Field Layout" not in progress


def test_field_layout_included_in_multi_bhe_modes():
    for mode in ("Multi BHE — Parallel", "Multi BHE — Series"):
        progress = tab_progress({}, mode=mode)
        assert "Field Layout" in progress


def test_field_layout_reacts_to_tracked_key_change():
    state = {"cfg_field_n_bhes": FIELD_DEFAULTS["n_bhes"] + 1}
    progress = tab_progress(state, mode="Multi BHE — Parallel")
    assert progress["Field Layout"] is True


# =============================================================================
# Changing / reverting a tracked value marks only that tab
# =============================================================================

def test_changing_one_tracked_value_marks_only_its_tab():
    state = {"cfg_Tg": GROUND_DEFAULTS["Tg"] + 1.0}
    progress = tab_progress(state, mode="Single BHE")

    assert progress["Ground"] is True
    assert all(filled is False for name, filled in progress.items() if name != "Ground")


def test_reverting_a_value_to_default_unmarks_the_tab():
    changed = {"cfg_Tg": GROUND_DEFAULTS["Tg"] + 1.0}
    reverted = {"cfg_Tg": GROUND_DEFAULTS["Tg"]}

    assert tab_progress(changed, mode="Single BHE")["Ground"] is True
    assert tab_progress(reverted, mode="Single BHE")["Ground"] is False


# =============================================================================
# Borehole: only the active pipe type's keys count
# =============================================================================

def test_borehole_reacts_to_active_pipe_type_keys():
    state = {
        "cfg_pipe_type": "SingleUtube",
        "cfg_su_Dpi": SINGLE_UTUBE_DEFAULTS["Dpi"] + 0.01,
    }
    progress = tab_progress(state, mode="Single BHE")
    assert progress["Borehole"] is True


def test_borehole_ignores_inactive_pipe_type_keys():
    # cfg_su_* left over from a previous pipe-type selection, but the
    # active pipe type is now DoubleUtube -> must not affect the checkmark.
    state = {
        "cfg_pipe_type": "DoubleUtube",
        "cfg_su_Dpi": SINGLE_UTUBE_DEFAULTS["Dpi"] + 0.01,
    }
    progress = tab_progress(state, mode="Single BHE")
    assert progress["Borehole"] is False


def test_borehole_switching_pipe_type_reevaluates_with_new_type_only():
    state = {
        "cfg_pipe_type": "SingleUtube",
        "cfg_su_Dpi": SINGLE_UTUBE_DEFAULTS["Dpi"] + 0.01,
    }
    assert tab_progress(state, mode="Single BHE")["Borehole"] is True

    state["cfg_pipe_type"] = "DoubleUtube"
    assert tab_progress(state, mode="Single BHE")["Borehole"] is False


def test_borehole_d0_default_follows_pipe_type_override():
    # D0's default itself depends on pipe type (Helical needs more room) —
    # leaving D0 unset must not spuriously mark the tab filled for Helical.
    state = {"cfg_pipe_type": "Helical"}
    progress = tab_progress(state, mode="Single BHE")
    assert progress["Borehole"] is False

    state["cfg_D0"] = D0_PIPE_TYPE_OVERRIDES["Helical"] + 0.1
    progress = tab_progress(state, mode="Single BHE")
    assert progress["Borehole"] is True


# =============================================================================
# Fluid: switching fluid type is itself a substantive change
# =============================================================================

def test_fluid_reacts_to_fluid_name_change():
    state = {"cfg_fluid_name": "Ethylene glycol"}
    assert tab_progress(state, mode="Single BHE")["Fluid"] is True


# =============================================================================
# Field Layout: layout-type selection is tracked too
# =============================================================================

def test_field_layout_reacts_to_layout_type_change():
    state = {"cfg_field_layout": "irregular"}
    progress = tab_progress(state, mode="Multi BHE — Series")
    assert progress["Field Layout"] is True


# =============================================================================
# Plant Schedule: shallow, multi-trigger check
# =============================================================================

def test_plant_schedule_reacts_to_heat_flux_toggle():
    state = {"heat_flux_enabled": not PLANT_DEFAULTS["heat_flux_enabled"]}
    assert tab_progress(state, mode="Single BHE")["Plant Schedule"] is True


def test_plant_schedule_reacts_to_inlet_profile_mode_change():
    state = {"schedule_mode": "From file (Excel)"}
    assert tab_progress(state, mode="Single BHE")["Plant Schedule"] is True


def test_plant_schedule_reacts_to_circuit_mw_change():
    state = {"mw_0": PLANT_DEFAULTS["mw"] + 0.05}
    assert tab_progress(state, mode="Single BHE")["Plant Schedule"] is True


def test_plant_schedule_reacts_to_added_operating_period():
    state = {"plant_periods": {0: [], 1: [("2024-01-01", "2024-01-02", 0, 24, 2.0)]}}
    assert tab_progress(state, mode="Single BHE")["Plant Schedule"] is True


def test_plant_schedule_reacts_to_added_heat_flux_period():
    state = {"heat_flux_periods": [("2024-01-01", "2024-04-01", 5000.0, 45.0)]}
    assert tab_progress(state, mode="Single BHE")["Plant Schedule"] is True


def test_plant_schedule_not_filled_with_only_empty_period_lists():
    state = {"plant_periods": {0: [], 1: []}, "heat_flux_periods": []}
    assert tab_progress(state, mode="Single BHE")["Plant Schedule"] is False


def test_plant_schedule_ignores_stale_mw_keys_outside_current_mode():
    # mw_5 is left over from a previous Multi BHE — Parallel session with 9
    # circuits; back in Single BHE mode only mw_0 is relevant.
    state = {"mw_5": PLANT_DEFAULTS["mw"] + 0.5}
    assert tab_progress(state, mode="Single BHE")["Plant Schedule"] is False


def test_plant_schedule_reacts_to_mw_within_current_circuit_count():
    state = {
        "cfg_field_n_bhes": 3,
        "mw_2": PLANT_DEFAULTS["mw"] + 0.5,
    }
    assert tab_progress(state, mode="Multi BHE — Parallel")["Plant Schedule"] is True


def test_plant_schedule_ignores_mw_beyond_current_parallel_circuit_count():
    state = {
        "cfg_field_n_bhes": 2,
        "mw_5": PLANT_DEFAULTS["mw"] + 0.5,
    }
    assert tab_progress(state, mode="Multi BHE — Parallel")["Plant Schedule"] is False


# =============================================================================
# build_tab_labels: numbering + checkmark formatting
# =============================================================================

def test_build_tab_labels_numbers_and_checks_single_bhe():
    state = {"cfg_Tg": GROUND_DEFAULTS["Tg"] + 1.0}
    labels = build_tab_labels(state, mode="Single BHE")

    assert labels[0] == "1 Ground ✓"
    assert labels[1] == "2 Borehole"
    assert "Field Layout" not in " ".join(labels)
    assert labels[-1].startswith("6 Plant Schedule")


def test_build_tab_labels_includes_field_layout_in_multi_bhe_mode():
    labels = build_tab_labels({}, mode="Multi BHE — Parallel")

    assert len(labels) == len(TAB_NAMES)
    assert labels[5] == "6 Field Layout"
    assert labels[6] == "7 Plant Schedule"


def test_build_tab_labels_no_checkmarks_on_fresh_state():
    labels = build_tab_labels({}, mode="Multi BHE — Series")
    assert all("✓" not in label for label in labels)
