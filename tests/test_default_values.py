# -*- coding: utf-8 -*-
"""
Pins every input-tab widget's default value against the centralized
defaults structure in defaults.py, driving the real app through
Streamlit's AppTest harness (same approach as test_app_smoke.py).

This is the regression guard for the "centralize per-tab defaults"
prefactor (ticket 01): it fails if a widget's rendered default ever
drifts from the single source of truth in defaults.py, in either
direction.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from defaults import (
    BOREHOLE_DEFAULTS,
    D0_PIPE_TYPE_OVERRIDES,
    ENV_DEFAULTS,
    FIELD_DEFAULTS,
    FLUID_DEFAULTS,
    GROUND_DEFAULTS,
    GROUND_LAYER_DEFAULTS,
    IRRIGATION_DEFAULTS,
    PLANT_DEFAULTS,
    SIM_DEFAULTS,
)

ROOT = Path(__file__).resolve().parent.parent
APP_PATH = ROOT / "app.py"


def _run_default_app() -> AppTest:
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    at.run()
    assert not at.exception, f"default render raised: {at.exception}"
    return at


def test_ground_tab_defaults():
    at = _run_default_app()
    assert at.number_input(key="cfg_Tg").value == GROUND_DEFAULTS["Tg"]
    assert at.number_input(key="cfg_L").value == GROUND_DEFAULTS["L"]
    assert at.number_input(key="cfg_L_sup").value == GROUND_DEFAULTS["L_sup"]
    assert at.number_input(key="cfg_L_inf").value == GROUND_DEFAULTS["L_inf"]
    assert at.number_input(key="cfg_rn").value == GROUND_DEFAULTS["rn"]
    assert at.number_input(key="cfg_n_mesh").value == GROUND_DEFAULTS["n_mesh"]
    assert at.number_input(key="cfg_m_mesh").value == GROUND_DEFAULTS["m_mesh"]
    assert at.number_input(key="cfg_m_mesh_sup").value == GROUND_DEFAULTS["m_mesh_sup"]
    assert at.number_input(key="cfg_m_mesh_inf").value == GROUND_DEFAULTS["m_mesh_inf"]
    assert at.number_input(key="cfg_n_layers").value == GROUND_DEFAULTS["n_layers"]
    assert at.number_input(key="k_0").value == GROUND_LAYER_DEFAULTS["k"]
    assert at.number_input(key="cp_0").value == GROUND_LAYER_DEFAULTS["cp"]
    assert at.number_input(key="rho_0").value == GROUND_LAYER_DEFAULTS["rho"]
    assert at.number_input(key="th_0").value == GROUND_LAYER_DEFAULTS["th"]


def test_borehole_tab_defaults_for_single_utube():
    at = _run_default_app()  # default pipe type is SingleUtube
    assert at.number_input(key="cfg_Lbore").value == BOREHOLE_DEFAULTS["Lbore"]
    assert at.number_input(key="cfg_D0").value == BOREHOLE_DEFAULTS["D0"]
    assert at.number_input(key="cfg_cp_0").value == BOREHOLE_DEFAULTS["cp_0"]
    assert at.number_input(key="cfg_rho_0").value == BOREHOLE_DEFAULTS["rho_0"]
    assert at.number_input(key="cfg_k0").value == BOREHOLE_DEFAULTS["k0"]


def test_borehole_d0_override_for_helical_pipe_type():
    # cfg_D0 renders in every pipe type, so it only picks up a new `value=`
    # on its first-ever render for that session -- pre-seed session_state
    # instead of switching pipe_type after an initial run.
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    at.session_state["cfg_pipe_type"] = "Helical"
    at.run()
    assert not at.exception, f"render with Helical pipe type raised: {at.exception}"
    assert at.number_input(key="cfg_D0").value == D0_PIPE_TYPE_OVERRIDES["Helical"]


def test_variable_props_defaults_for_helical_pipe_type():
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    at.run()
    at.selectbox(key="cfg_pipe_type").set_value("Helical")
    at.run()
    assert at.checkbox(key="cfg_vp_enabled").value == IRRIGATION_DEFAULTS["enabled"]


def test_fluid_tab_defaults():
    at = _run_default_app()
    assert at.number_input(key="cfg_T_ref").value == FLUID_DEFAULTS["T_ref"]


def test_env_tab_defaults():
    at = _run_default_app()
    assert at.number_input(key="cfg_Tm").value == ENV_DEFAULTS["Tm"]
    assert at.number_input(key="cfg_R_ext").value == ENV_DEFAULTS["R_ext"]
    assert at.number_input(key="cfg_At").value == ENV_DEFAULTS["At"]
    assert at.number_input(key="cfg_tau_y").value == ENV_DEFAULTS["tau_y"]
    assert at.date_input(key="env_tau_date").value == ENV_DEFAULTS["tau_date"]
    assert at.date_input(key="env_tau_shift_date").value == ENV_DEFAULTS["tau_shift_date"]
    # "Manual" surface material leaves absorptance/eps at their manual fallback
    assert at.selectbox(key="cfg_material").value == "Manual"
    assert at.number_input(key="cfg_absorptance").value == ENV_DEFAULTS["absorptance_manual"]
    assert at.number_input(key="cfg_eps").value == ENV_DEFAULTS["eps_manual"]


def test_sim_tab_defaults():
    at = _run_default_app()
    assert at.number_input(key="cfg_dt").value == SIM_DEFAULTS["dt"]
    assert at.number_input(key="cfg_n_steps").value == SIM_DEFAULTS["n_steps"]


def test_field_tab_defaults_in_multi_bhe_mode():
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    at.run()
    at.radio(key="cfg_mode").set_value("Multi BHE — Parallel")
    at.run()
    assert not at.exception, f"render after switching mode raised: {at.exception}"
    assert at.number_input(key="cfg_field_n_bhes").value == FIELD_DEFAULTS["n_bhes"]
    assert at.number_input(key="cfg_field_x_min").value == FIELD_DEFAULTS["x_min"]
    assert at.number_input(key="cfg_field_y_min").value == FIELD_DEFAULTS["y_min"]
    assert at.number_input(key="cfg_field_x_max").value == FIELD_DEFAULTS["x_max"]
    assert at.number_input(key="cfg_field_y_max").value == FIELD_DEFAULTS["y_max"]


def test_plant_schedule_tab_defaults():
    at = _run_default_app()
    assert at.checkbox(key="heat_flux_enabled").value == PLANT_DEFAULTS["heat_flux_enabled"]
    assert at.number_input(key="mw_0").value == PLANT_DEFAULTS["mw"]
