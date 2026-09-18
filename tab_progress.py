# -*- coding: utf-8 -*-
"""
Numbered, checkmark-when-filled progress indicator for CaRM App's input
tabs.

Purely informational: this module only *computes* whether a tab's tracked
values differ from their defaults ("filled in"). No tab is hidden, disabled,
or reordered as a result. Streamlit-free, same shape as config_io.py — it
talks to session_state purely through dict-like ``.get()``/``.items()``
access, so a plain dict stands in for ``st.session_state`` in tests.

"Filled in" is always recomputed fresh from current session_state; it is
never itself stored, so it reacts correctly to both manual widget edits and
a loaded configuration (``config_io.apply_config``) without special-casing
either path.
"""

from defaults import (
    BOREHOLE_DEFAULTS,
    COAXIAL_DEFAULTS,
    D0_PIPE_TYPE_OVERRIDES,
    DOUBLE_UTUBE_DEFAULTS,
    ENV_DEFAULTS,
    FIELD_DEFAULTS,
    FLUID_DEFAULTS,
    GROUND_DEFAULTS,
    GROUND_LAYER_DEFAULTS,
    HELICAL_DEFAULTS,
    PLANT_DEFAULTS,
    SIM_DEFAULTS,
    SINGLE_UTUBE_DEFAULTS,
    SURFACE_MATERIALS,
)

# Input tabs, in their intended fill-in order. "Field Layout" is only shown
# (and only numbered/tracked) in multi-BHE modes — see build_tab_labels().
TAB_NAMES = [
    "Ground",
    "Borehole",
    "Fluid",
    "Environment",
    "Simulation",
    "Field Layout",
    "Plant Schedule",
]

# Session_state key -> centralized default, per pipe type. Mirrors the
# cfg_{su,du,cx,he}_* keys assigned in ui_inputs.py's render_borehole_tab
# (note pipe1_thick/pipe2_thick use bare "p1t"/"p2t"/"hp1t"/"hp2t" keys,
# not a cfg_ prefix).
_PIPE_TYPE_FIELDS = {
    "SingleUtube": (SINGLE_UTUBE_DEFAULTS, {
        "Dpi":          "cfg_su_Dpi",
        "pipe_thick":   "cfg_su_pipe_thick",
        "pipe_spacing": "cfg_su_pipe_spacing",
        "Rp0":          "cfg_su_Rp0",
        "RppB":         "cfg_su_RppB",
        "n_pipes":      "cfg_su_n_pipes",
    }),
    "DoubleUtube": (DOUBLE_UTUBE_DEFAULTS, {
        "Dpi":          "cfg_du_Dpi",
        "pipe_thick":   "cfg_du_pipe_thick",
        "pipe_spacing": "cfg_du_pipe_spacing",
        "Rp0":          "cfg_du_Rp0",
        "RppB":         "cfg_du_RppB",
        "RppA":         "cfg_du_RppA",
        "n_pipes":      "cfg_du_n_pipes",
        "connection":   "cfg_du_connection",
    }),
    "Coaxial": (COAXIAL_DEFAULTS, {
        "Dp1i":              "cfg_cx_Dp1i",
        "pipe1_thick":       "p1t",
        "k_pipe1":           "cfg_cx_k_pipe1",
        "Dp2i":              "cfg_cx_Dp2i",
        "pipe2_thick":       "p2t",
        "k_pipe2":           "cfg_cx_k_pipe2",
        "supply_and_return": "cfg_cx_supply_and_return",
    }),
    "Helical": (HELICAL_DEFAULTS, {
        "Dpi1":              "cfg_he_Dpi1",
        "pipe1_thick":       "hp1t",
        "Dpi2":              "cfg_he_Dpi2",
        "pipe2_thick":       "hp2t",
        "k_pipe":            "cfg_he_k_pipe",
        "rih":               "cfg_he_rih",
        "P_hel":             "cfg_he_P_hel",
        "supply_and_return": "cfg_he_supply_and_return",
    }),
}

# Implicit selectbox defaults: these widgets have no explicit `value=`/
# `index=` literal in ui_inputs.py, so Streamlit itself defaults to the
# first listed option.
_SCHEDULE_MODE_DEFAULT = "Calendar schedule"
_FLUID_NAME_DEFAULT = "Water"
_FIELD_LAYOUT_DEFAULT = "regular"


def _differs(session_state, key, default) -> bool:
    return session_state.get(key, default) != default


def _ground_filled(session_state) -> bool:
    d = GROUND_DEFAULTS
    for field in ("Tg", "L", "L_sup", "L_inf", "rn", "n_mesh",
                  "m_mesh", "m_mesh_sup", "m_mesh_inf", "n_layers"):
        if _differs(session_state, f"cfg_{field}", d[field]):
            return True

    try:
        n_layers = int(session_state.get("cfg_n_layers", d["n_layers"]))
    except (TypeError, ValueError):
        n_layers = d["n_layers"]

    dl = GROUND_LAYER_DEFAULTS
    for i in range(n_layers):
        for field, default in dl.items():
            if _differs(session_state, f"{field}_{i}", default):
                return True
    return False


def _borehole_filled(session_state) -> bool:
    d = BOREHOLE_DEFAULTS
    pipe_type = session_state.get("cfg_pipe_type", "SingleUtube")
    d0_default = D0_PIPE_TYPE_OVERRIDES.get(pipe_type, d["D0"])

    if _differs(session_state, "cfg_Lbore", d["Lbore"]):
        return True
    if _differs(session_state, "cfg_D0", d0_default):
        return True
    if _differs(session_state, "cfg_cp_0", d["cp_0"]):
        return True
    if _differs(session_state, "cfg_rho_0", d["rho_0"]):
        return True
    if _differs(session_state, "cfg_k0", d["k0"]):
        return True

    pipe_defaults, key_map = _PIPE_TYPE_FIELDS.get(pipe_type, (None, None))
    if pipe_defaults is None:
        return False
    for field, default in pipe_defaults.items():
        session_key = key_map.get(field)
        if session_key is not None and _differs(session_state, session_key, default):
            return True
    return False


def _fluid_filled(session_state) -> bool:
    d = FLUID_DEFAULTS
    if _differs(session_state, "cfg_T_ref", d["T_ref"]):
        return True
    # Switching fluid away from the implicit default ("Water", the
    # selectbox's first option) is itself a substantive change — it also
    # gates whether the concentration field is even shown/relevant.
    if session_state.get("cfg_fluid_name", _FLUID_NAME_DEFAULT) != _FLUID_NAME_DEFAULT:
        return True
    return False


def _env_absorptance_default(session_state):
    material = session_state.get("cfg_material", "Manual")
    preset = SURFACE_MATERIALS.get(material, (None, None))
    return preset[0] if preset[0] is not None else ENV_DEFAULTS["absorptance_manual"]


def _env_eps_default(session_state):
    material = session_state.get("cfg_material", "Manual")
    preset = SURFACE_MATERIALS.get(material, (None, None))
    return preset[1] if preset[1] is not None else ENV_DEFAULTS["eps_manual"]


def _env_filled(session_state) -> bool:
    d = ENV_DEFAULTS
    for key, default in (
        ("cfg_Tm", d["Tm"]),
        ("cfg_R_ext", d["R_ext"]),
        ("cfg_At", d["At"]),
        ("cfg_tau_y", d["tau_y"]),
        ("env_tau_date", d["tau_date"]),
        ("env_tau_shift_date", d["tau_shift_date"]),
    ):
        if _differs(session_state, key, default):
            return True

    if _differs(session_state, "cfg_absorptance", _env_absorptance_default(session_state)):
        return True
    if _differs(session_state, "cfg_eps", _env_eps_default(session_state)):
        return True
    return False


def _sim_filled(session_state) -> bool:
    d = SIM_DEFAULTS
    return (
        _differs(session_state, "cfg_dt", d["dt"])
        or _differs(session_state, "cfg_n_steps", d["n_steps"])
    )


def _field_filled(session_state) -> bool:
    d = FIELD_DEFAULTS
    for field in ("n_bhes", "x_min", "y_min", "x_max", "y_max"):
        if _differs(session_state, f"cfg_field_{field}", d[field]):
            return True
    if _differs(session_state, "cfg_field_layout", _FIELD_LAYOUT_DEFAULT):
        return True
    return False


# ui_inputs.py's render_field_tab seeds this many default groups the first
# time Series mode is rendered, before "series_groups" exists in
# session_state.
_DEFAULT_SERIES_GROUP_COUNT = 3


def _circuit_count(session_state, mode: str) -> int:
    """
    Number of Plant Schedule circuits actually rendered for ``mode`` —
    mirrors app.py's own n_circuits derivation, bounding the mw_<i> scan
    below to only the currently relevant circuits (same principle as
    Borehole's active-pipe-type-only check).
    """
    if mode == "Single BHE":
        return 1
    if mode == "Multi BHE — Parallel":
        return int(session_state.get("cfg_field_n_bhes", FIELD_DEFAULTS["n_bhes"]))
    # Multi BHE — Series: one circuit per group.
    groups = session_state.get("series_groups")
    if groups is None:
        return _DEFAULT_SERIES_GROUP_COUNT
    return len(groups)


def _plant_filled(session_state, mode: str) -> bool:
    d = PLANT_DEFAULTS
    if _differs(session_state, "heat_flux_enabled", d["heat_flux_enabled"]):
        return True
    if _differs(session_state, "schedule_mode", _SCHEDULE_MODE_DEFAULT):
        return True

    for i in range(_circuit_count(session_state, mode)):
        if session_state.get(f"mw_{i}", d["mw"]) != d["mw"]:
            return True

    plant_periods = session_state.get("plant_periods", {})
    if isinstance(plant_periods, dict) and any(len(v) > 0 for v in plant_periods.values()):
        return True

    heat_flux_periods = session_state.get("heat_flux_periods", [])
    if len(heat_flux_periods) > 0:
        return True

    return False


_TAB_CHECKS = {
    "Ground":       _ground_filled,
    "Borehole":     _borehole_filled,
    "Fluid":        _fluid_filled,
    "Environment":  _env_filled,
    "Simulation":   _sim_filled,
    "Field Layout": _field_filled,
}


def tab_progress(session_state, mode: str) -> dict:
    """
    Return an ordered ``{tab_name: filled_bool}`` mapping for every input
    tab that is shown for the given mode. "Field Layout" is only included
    when ``mode`` is one of the two multi-BHE options, matching its own
    conditional rendering in app.py.
    """
    progress = {}
    for name in TAB_NAMES:
        if name == "Field Layout" and mode == "Single BHE":
            continue
        if name == "Plant Schedule":
            progress[name] = _plant_filled(session_state, mode)
        else:
            progress[name] = _TAB_CHECKS[name](session_state)
    return progress


def build_tab_labels(session_state, mode: str) -> list:
    """
    Build the numbered, checkmark-when-filled label list (e.g. "1 Ground",
    "2 Borehole ✓", ...) for ``st.tabs([...])``, in fill-in order.
    """
    labels = []
    for i, (name, filled) in enumerate(tab_progress(session_state, mode).items(), start=1):
        label = f"{i} {name}"
        if filled:
            label += " ✓"
        labels.append(label)
    return labels
