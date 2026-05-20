# -*- coding: utf-8 -*-
"""
UI components: input tabs for CaRM App.
"""

import numpy as np
import streamlit as st
from CoolProp.CoolProp import PropsSI

from defaults import (
    SURFACE_MATERIALS,
    SINGLE_UTUBE_DEFAULTS,
    DOUBLE_UTUBE_DEFAULTS,
    COAXIAL_DEFAULTS,
    HELICAL_DEFAULTS,
    BOREHOLE_DEFAULTS,
)


# =============================================================================
# Tab: Ground
# =============================================================================

def render_ground_tab():
    st.subheader("Ground geometry & mesh")
    col1, col2 = st.columns(2)
    with col1:
        Tg         = st.number_input("Undisturbed ground temperature Tg [°C]", value=13.0)
        L          = st.number_input("Borehole active length L [m]", value=100.0)
        L_sup      = st.number_input("Surface layer thickness L_sup [m]", value=1.0)
        L_inf      = st.number_input("Bottom layer thickness L_inf [m]", value=10.0)
        rn         = st.number_input("Far-field radius rn [m]", value=10.0,
                                     help="Leave at 0 to auto-compute for multi-BHE fields",
                                     min_value=0.0)
    with col2:
        n_mesh     = st.number_input("Radial mesh cells n_mesh [-]",        value=20, min_value=1)
        m_mesh     = st.number_input("Axial mesh cells m_mesh [-]",         value=40, min_value=1)
        m_mesh_sup = st.number_input("Axial cells surface layer [-]",       value=4,  min_value=1)
        m_mesh_inf = st.number_input("Axial cells bottom layer [-]",        value=40, min_value=1)

    st.subheader("Ground stratification")
    st.caption("Each row: thermal conductivity, specific heat, density, layer thickness")
    n_layers = st.number_input("Number of layers", value=1, min_value=1, max_value=10)
    stratification = []
    for i in range(int(n_layers)):
        c1, c2, c3, c4 = st.columns(4)
        k_s   = c1.number_input(f"k [W/m·K] — layer {i+1}",    value=1.83,   key=f"k_{i}")
        cp_s  = c2.number_input(f"cp [J/kg·K] — layer {i+1}",  value=947.0,  key=f"cp_{i}")
        rho_s = c3.number_input(f"ρ [kg/m³] — layer {i+1}",    value=1900.0, key=f"rho_{i}")
        th_s  = c4.number_input(f"thick [m] — layer {i+1}",    value=111.0,  key=f"th_{i}")
        stratification.append((k_s, cp_s, rho_s, th_s))

    return dict(
        Tg=Tg, L=L, L_sup=L_sup, L_inf=L_inf, rn=rn,
        n_mesh=int(n_mesh), m_mesh=int(m_mesh),
        m_mesh_sup=int(m_mesh_sup), m_mesh_inf=int(m_mesh_inf),
        stratification=stratification,
    )


# =============================================================================
# Tab: Borehole
# =============================================================================

def render_borehole_tab(pipe_type: str):
    d = BOREHOLE_DEFAULTS
    st.subheader("Borehole geometry & grouting material")
    col1, col2 = st.columns(2)
    with col1:
        Lbore = st.number_input("Borehole length Lbore [m]",          value=d["Lbore"])
        D0    = st.number_input("Borehole diameter D0 [m]",           value=d["D0"])
    with col2:
        cp_0  = st.number_input("Grout specific heat cp_0 [J/kg·K]", value=d["cp_0"])
        rho_0 = st.number_input("Grout density ρ_0 [kg/m³]",         value=d["rho_0"])
        k0    = st.number_input("Grout conductivity k0 [W/m·K]",     value=d["k0"])

    st.subheader(f"Pipe parameters — {pipe_type}")
    pipe_params = {}

    if pipe_type == "SingleUtube":
        p = SINGLE_UTUBE_DEFAULTS
        col1, col2 = st.columns(2)
        with col1:
            pipe_params["Dpi"]          = st.number_input("Inside pipe diameter Dpi [m]",       value=p["Dpi"])
            pipe_params["pipe_thick"]   = st.number_input("Pipe wall thickness [m]",            value=p["pipe_thick"])
            pipe_params["pipe_spacing"] = st.number_input("Shank spacing [m]",                  value=p["pipe_spacing"])
        with col2:
            pipe_params["Rp0"]          = st.number_input("Pipe–wall resistance Rp0 [m·K/W]",   value=p["Rp0"])
            pipe_params["RppB"]         = st.number_input("Pipe–pipe resistance RppB [m·K/W]",  value=p["RppB"])
            pipe_params["n_pipes"]      = int(st.number_input("Number of pipes [-]",            value=p["n_pipes"], min_value=2))

    elif pipe_type == "DoubleUtube":
        p = DOUBLE_UTUBE_DEFAULTS
        col1, col2 = st.columns(2)
        with col1:
            pipe_params["Dpi"]          = st.number_input("Inside pipe diameter Dpi [m]",              value=p["Dpi"])
            pipe_params["pipe_thick"]   = st.number_input("Pipe wall thickness [m]",                   value=p["pipe_thick"])
            pipe_params["pipe_spacing"] = st.number_input("Shank spacing [m]",                         value=p["pipe_spacing"])
        with col2:
            pipe_params["Rp0"]          = st.number_input("Pipe–wall resistance Rp0 [m·K/W]",          value=p["Rp0"])
            pipe_params["RppB"]         = st.number_input("Pipe–pipe resistance (opposite) RppB [m·K/W]", value=p["RppB"])
            pipe_params["RppA"]         = st.number_input("Pipe–pipe resistance (adjacent) RppA [m·K/W]", value=p["RppA"])
            pipe_params["n_pipes"]      = int(st.number_input("Number of pipes [-]",                   value=p["n_pipes"], min_value=4))
            pipe_params["connection"]   = st.selectbox("Connection (P = parallel, S = series)", ["P", "S"])

    elif pipe_type == "Coaxial":
        p = COAXIAL_DEFAULTS
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Inner pipe (1)**")
            pipe_params["Dp1i"]        = st.number_input("Inside diameter Dp1i [m]",     value=p["Dp1i"])
            pipe_params["pipe1_thick"] = st.number_input("Wall thickness [m]",           value=p["pipe1_thick"], key="p1t")
            pipe_params["k_pipe1"]     = st.number_input("Conductivity k1 [W/m·K]",     value=p["k_pipe1"])
        with col2:
            st.markdown("**Outer pipe (2)**")
            pipe_params["Dp2i"]        = st.number_input("Inside diameter Dp2i [m]",     value=p["Dp2i"])
            pipe_params["pipe2_thick"] = st.number_input("Wall thickness [m]",           value=p["pipe2_thick"], key="p2t")
            pipe_params["k_pipe2"]     = st.number_input("Conductivity k2 [W/m·K]",     value=p["k_pipe2"])
        pipe_params["supply_and_return"] = st.selectbox(
            "Inlet pipe (1→2: supply in inner / 2→1: supply in annulus)",
            ["1_2", "2_1"],
        )

    elif pipe_type == "Helical":
        p = HELICAL_DEFAULTS
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Inner pipe (1) — straight**")
            pipe_params["Dpi1"]        = st.number_input("Inside diameter Dpi1 [m]", value=p["Dpi1"])
            pipe_params["pipe1_thick"] = st.number_input("Wall thickness [m]",       value=p["pipe1_thick"], key="hp1t")
            st.markdown("**Helical pipe (2)**")
            pipe_params["Dpi2"]        = st.number_input("Inside diameter Dpi2 [m]", value=p["Dpi2"])
            pipe_params["pipe2_thick"] = st.number_input("Wall thickness [m]",       value=p["pipe2_thick"], key="hp2t")
            pipe_params["k_pipe"]      = st.number_input("Pipe conductivity [W/m·K]",value=p["k_pipe"])
        with col2:
            pipe_params["rih"]         = st.number_input("Inner helix radius rih [m]", value=p["rih"],
                                                          help="= (outer helix diameter / 2) − pipe outside radius")
            pipe_params["P_hel"]       = st.number_input("Pitch P [m]",               value=p["P_hel"])
            pipe_params["supply_and_return"] = st.selectbox(
                "Inlet pipe (1→2 / 2→1)", ["1_2", "2_1"],
            )
            # auto-computed — displayed as disabled inputs
            Lbore_cur = Lbore  # captured from outer scope
            N_hel   = max(1, int(Lbore_cur / pipe_params["P_hel"])) if pipe_params["P_hel"] > 0 else 1
            Lp2tot  = float(N_hel) * np.sqrt(pipe_params["P_hel"]**2 + (2 * np.pi * pipe_params["rih"])**2)
            st.number_input("N turns (auto) [-]",       value=N_hel,  disabled=True, key="N_auto")
            st.number_input("Lp2tot (auto) [m]",        value=round(Lp2tot, 4), disabled=True, key="Lp2_auto")
            pipe_params["N_hel"]   = N_hel
            pipe_params["Lp2tot"]  = Lp2tot

    # --- cross-section diagram ---
    _svg_map = {
        "SingleUtube": "single_utube.svg",
        "DoubleUtube": "double_utube.svg",
    }
    _svg_file = _svg_map.get(pipe_type)
    if _svg_file:
        import pathlib as _pl
        _svg_path = _pl.Path(__file__).parent / _svg_file
        if _svg_path.exists():
            st.divider()
            st.caption("Pipe configuration — cross section")
            col_img, _ = st.columns([1, 1])
            with col_img:
                st.image(str(_svg_path))

    return dict(Lbore=Lbore, D0=D0, cp_0=cp_0, rho_0=rho_0, k0=k0, **pipe_params)


# =============================================================================
# Tab: Fluid
# =============================================================================

def _coolprop_string(fluid_name: str, concentration: float) -> str:
    if fluid_name == "Water":
        return "Water"
    elif fluid_name == "Ethylene glycol":
        return f"INCOMP::MEG[{concentration / 100:.2f}]"
    else:
        return f"INCOMP::MPG[{concentration / 100:.2f}]"


def render_fluid_tab():
    st.subheader("Heat carrier fluid")
    col1, col2 = st.columns(2)
    with col1:
        fluid_name    = st.selectbox("Fluid", ["Water", "Ethylene glycol", "Propylene glycol"])
        T_ref         = st.number_input("Reference temperature [°C]", value=10.0,
                                        help="Typically mean fluid temperature during operation")
    with col2:
        concentration = 0.0
        if fluid_name != "Water":
            concentration = float(st.slider("Glycol concentration [%]",
                                            min_value=0, max_value=60, value=25, step=1))

    fluid_str = _coolprop_string(fluid_name, concentration)
    try:
        T_K   = T_ref + 273.15
        P_atm = 101325.0
        k_w   = PropsSI("L", "T", T_K, "P", P_atm, fluid_str)
        rho_w = PropsSI("D", "T", T_K, "P", P_atm, fluid_str)
        cp_w  = PropsSI("C", "T", T_K, "P", P_atm, fluid_str)
        mu_w  = PropsSI("V", "T", T_K, "P", P_atm, fluid_str)
        ni_w  = mu_w / rho_w
    except Exception as e:
        st.error(f"CoolProp error: {e}")
        st.stop()

    st.subheader("Computed properties")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("k_w [W/m·K]",   f"{k_w:.4f}")
    c2.metric("ρ_w [kg/m³]",   f"{rho_w:.2f}")
    c3.metric("cp_w [J/kg·K]", f"{cp_w:.1f}")
    c4.metric("ν_w [m²/s]",    f"{ni_w:.3e}")

    st.caption("Override computed values if needed:")
    col1, col2 = st.columns(2)
    with col1:
        k_w   = st.number_input("k_w [W/m·K]",   value=float(f"{k_w:.6f}"))
        rho_w = st.number_input("ρ_w [kg/m³]",   value=float(f"{rho_w:.4f}"))
    with col2:
        cp_w  = st.number_input("cp_w [J/kg·K]", value=float(f"{cp_w:.4f}"))
        ni_w  = st.number_input("ν_w [m²/s]",    value=ni_w, format="%.3e")

    return dict(k_w=k_w, rho_w=rho_w, cp_w=cp_w, ni_w=ni_w)


# =============================================================================
# Tab: Environment
# =============================================================================

def render_env_tab():
    st.subheader("Surface material")
    material = st.selectbox("Surface type", list(SURFACE_MATERIALS.keys()))
    preset   = SURFACE_MATERIALS[material]

    col1, col2 = st.columns(2)
    with col1:
        absorptance = st.number_input(
            "Surface absorptance [-]",
            value=preset[0] if preset[0] is not None else 0.70,
            min_value=0.0, max_value=1.0,
            disabled=(material != "Manual"),
        )
    with col2:
        eps = st.number_input(
            "Surface emittance [-]",
            value=preset[1] if preset[1] is not None else 0.95,
            min_value=0.0, max_value=1.0,
            disabled=(material != "Manual"),
        )

    st.subheader("Environmental properties")
    import datetime as _dt_env

    def _doy_seconds(date: _dt_env.date) -> float:
        return float((date - _dt_env.date(date.year, 1, 1)).days * 86400)

    col1, col2 = st.columns(2)
    with col1:
        Tm    = st.number_input("Mean annual air temperature Tm [°C]", value=13.0)
        R_ext = st.number_input("External thermal resistance R_ext [m²·K/W]", value=0.04)
        At    = st.number_input("Annual temperature amplitude At [K]", value=10.0)
        tau_y = st.number_input("Year duration tau_y [s]", value=365 * 24 * 3600)
    with col2:
        st.markdown("**Simulation start date (τ)**")
        st.caption("Seconds from Jan 1 to the simulation start — used as τ in EnvironmentalProperties.")
        tau_date = st.date_input(
            "Simulation start",
            value=_dt_env.date(2024, 1, 1),
            key="env_tau_date",
        )
        tau = _doy_seconds(tau_date)
        st.metric("τ [s]", f"{tau:,.0f}")

        st.markdown("**Date of minimum surface temperature (τ_shift)**")
        st.caption("Typically mid-February — day when surface temperature reaches its annual minimum.")
        shift_date = st.date_input(
            "Date of minimum T",
            value=_dt_env.date(2024, 2, 14),
            key="env_tau_shift_date",
        )
        tau_shift = _doy_seconds(shift_date)
        st.metric("τ_shift [s]", f"{tau_shift:,.0f}")

    return dict(
        Tm=Tm, R_ext=R_ext, absorptance=absorptance, eps=eps,
        At=At, tau_y=tau_y, tau=tau, tau_shift=tau_shift,
        sim_start=tau_date,
    )


# =============================================================================
# Tab: Simulation
# =============================================================================

def render_sim_tab():
    st.subheader("Simulation parameters")
    col1, col2 = st.columns(2)
    with col1:
        dt      = st.number_input("Time step dt [s]",  value=3600)
        n_steps = st.number_input("Number of steps [-]", value=276, min_value=1)
    return dict(dt=int(dt), n_steps=int(n_steps))


# =============================================================================
# Tab: Field Layout  (shown only for multi-BHE modes)
# =============================================================================

def render_field_tab(mode: str):
    """Render field layout. For Series, groups are defined dynamically."""
    if mode == "Single BHE":
        st.info("Field layout is not applicable for Single BHE configuration.")
        return {}

    st.subheader("Field layout")
    n_bhes = int(st.number_input("Total number of BHEs", value=9, min_value=1))
    layout = st.selectbox("Layout type", ["regular", "irregular"])

    if layout == "regular" and mode == "Multi BHE — Series":
        st.warning(
            "For series configuration the FLS model requires **irregular** layout "
            "with explicit borehole coordinates."
        )

    col1, col2 = st.columns(2)
    with col1:
        x_min = st.number_input("Field x_min [m]", value=-2.5)
        y_min = st.number_input("Field y_min [m]", value=-2.5)
    with col2:
        x_max = st.number_input("Field x_max [m]", value=12.5)
        y_max = st.number_input("Field y_max [m]", value=12.5)

    out = dict(
        n_bhes=n_bhes, layout=layout,
        x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max,
    )

    if mode == "Multi BHE — Series":
        st.subheader("Series groups")
        st.caption(
            "Add groups with the button below. Each group is a chain of boreholes "
            "in series. BHE IDs are 0-indexed and comma-separated."
        )

        # session state for groups list
        if "series_groups" not in st.session_state:
            st.session_state["series_groups"] = [
                {"ids": "0, 1, 2"},
                {"ids": "3, 4, 5"},
                {"ids": "6, 7, 8"},
            ]

        to_del = []
        for g, grp in enumerate(st.session_state["series_groups"]):
            c1, c2 = st.columns([5, 1])
            new_ids = c1.text_input(
                f"Group {g} — BHE IDs",
                value=grp["ids"],
                key=f"grp_ids_{g}",
            )
            st.session_state["series_groups"][g]["ids"] = new_ids
            if c2.button("✕", key=f"del_grp_{g}"):
                to_del.append(g)

        for g in reversed(to_del):
            st.session_state["series_groups"].pop(g)

        if st.button("＋ Add group"):
            n_existing = len(st.session_state["series_groups"])
            st.session_state["series_groups"].append({"ids": str(n_existing * 3)})

        # build groups dict
        groups = {}
        for g, grp in enumerate(st.session_state["series_groups"]):
            try:
                ids = [int(x.strip()) for x in grp["ids"].split(",") if x.strip()]
            except ValueError:
                ids = []
            groups[f"group_{g}"] = ids

        n_groups = len(groups)
        out["n_groups"] = n_groups
        out["groups"]   = groups
        st.caption(f"{n_groups} group(s) defined, {sum(len(v) for v in groups.values())} BHEs assigned.")

    return out


# =============================================================================
# Tab: Plant Schedule
# =============================================================================

import datetime as _dt


def _date_to_tau(date: _dt.date) -> float:
    jan1 = _dt.date(date.year, 1, 1)
    return float((date - jan1).days * 86400)


def _build_mw_tf1_from_schedule(
    n_steps: int, dt_s: int,
    sim_start: _dt.date,
    circuits: list,
) -> tuple:
    """
    Build Tf1_arr and mw_arr from per-circuit schedule.

    Each circuit dict:
        Tf1_val : float
        mw_val  : float
        periods : list of (start_date, end_date, hour_on, hour_off)
                  Within each period, pump is on from hour_on to hour_off every day.
                  Outside all periods: mw = 0.
    """
    n_inlets     = len(circuits)
    Tf1_arr      = np.zeros((n_inlets, n_steps), dtype=np.float64)
    mw_arr       = np.zeros((n_inlets, n_steps), dtype=np.float64)
    sim_start_dt = _dt.datetime(sim_start.year, sim_start.month, sim_start.day, 0)

    for i, circ in enumerate(circuits):
        Tf1_arr[i, :] = circ["Tf1_val"]
        for (pd_start, pd_end, h_on, h_off) in circ["periods"]:
            # iterate day by day within the period
            day = pd_start
            while day <= pd_end:
                for h in range(h_on, h_off):
                    t = _dt.datetime(day.year, day.month, day.day, h)
                    delta_s = (t - sim_start_dt).total_seconds()
                    if 0 <= delta_s < n_steps * dt_s:
                        step = int(delta_s / dt_s)
                        mw_arr[i, step] = circ["mw_val"]
                day += _dt.timedelta(days=1)

    return Tf1_arr, mw_arr


def render_plant_schedule_tab(mode: str, n_steps: int, dt_s: int,
                              field_p: dict, sim_start):
    """
    Plant Schedule tab.
    sim_start comes from env_p["sim_start"] (set in Environment tab).
    Returns dict with keys:
        schedule_mode : "calendar" | "file"
        circuits      : list of circuit dicts  (calendar only)
        bc_file_path, col_tf1, col_mw, same_profile  (file only)
    """
    # --- input mode ---
    schedule_mode = st.radio(
        "Inlet profile mode",
        ["Calendar schedule", "From file (Excel)"],
        horizontal=True,
        key="schedule_mode",
    )

    # ── From file ──────────────────────────────────────────────────────────
    if schedule_mode == "From file (Excel)":
        st.caption(
            "Upload an Excel file with columns `Tin_C` and `mw_kgs` "
            "(one row per timestep). All circuits share the same profile."
        )
        bc_file = st.file_uploader("Inlet profile (.xlsx)", type=["xlsx"], key="bc_file")
        if bc_file is None:
            st.info("Upload a file to continue.")
            return dict(schedule_mode="file", bc_file_path=None)

        import tempfile as _tmp, pandas as _pd
        with _tmp.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(bc_file.read())
            tmp_path = tmp.name

        xl     = _pd.ExcelFile(tmp_path)
        sheets = xl.sheet_names
        st.caption(f"Sheets: {', '.join(sheets)}")
        col_tf1 = st.selectbox("Column — Tf1 [°C]",
                               ["Tin_C", "Tin_C_clean"] + sheets, key="bc_col_tf1")
        col_mw  = st.selectbox("Column — mw [kg/s]",
                               ["mw_kgs", "mw_kgs_series_norm"] + sheets, key="bc_col_mw")
        same    = st.checkbox("All circuits share the same profile", value=True)

        return dict(schedule_mode="file",
                    bc_file_path=tmp_path, col_tf1=col_tf1, col_mw=col_mw,
                    same_profile=same)

    # ── Calendar schedule ──────────────────────────────────────────────────
    if mode == "Single BHE":
        n_circuits     = 1
        circuit_labels = ["Circuit 0"]
    elif mode == "Multi BHE — Parallel":
        n_circuits     = field_p.get("n_bhes", 1)
        circuit_labels = [f"BHE {i}" for i in range(n_circuits)]
    else:
        n_circuits     = field_p.get("n_groups", 1)
        circuit_labels = [f"Group {i}" for i in range(n_circuits)]

    st.subheader("Operating schedule per circuit")
    st.caption(
        "For each circuit: set Tf1 and mw, then define one or more operating periods. "
        "Each period has a **date range** (from → to) and a **daily schedule** (hour on → hour off). "
        "Outside all periods the pump is off (mw = 0)."
    )

    # init session state
    key_p = "plant_periods"
    if key_p not in st.session_state:
        st.session_state[key_p] = {}
    for i in range(n_circuits):
        if i not in st.session_state[key_p]:
            st.session_state[key_p][i] = []

    circuits_out = []

    for i, label in enumerate(circuit_labels):
        with st.expander(f"**{label}**", expanded=(i == 0)):
            col1, col2 = st.columns(2)
            with col1:
                tf1_v = st.number_input("Tf1 [°C]",  value=2.0,    key=f"tf1_{i}")
            with col2:
                mw_v  = st.number_input("mw [kg/s]", value=0.1657, key=f"mw_{i}")

            st.markdown("**Operating periods**")
            periods_i = st.session_state[key_p][i]
            to_delete = []

            for j, (pd_start, pd_end, h_on, h_off) in enumerate(periods_i):
                st.markdown(f"*Period {j+1}*")
                c1, c2 = st.columns(2)
                pd_start_new = c1.date_input("From date", value=pd_start,
                                              key=f"pds_{i}_{j}")
                pd_end_new   = c2.date_input("To date",   value=pd_end,
                                              key=f"pde_{i}_{j}")
                c3, c4, c5 = st.columns([2, 2, 1])
                h_on_new  = int(c3.number_input("Daily start [h]", value=h_on,
                                                 min_value=0, max_value=23,
                                                 key=f"hon_{i}_{j}"))
                h_off_new = int(c4.number_input("Daily end [h]",   value=h_off,
                                                 min_value=1, max_value=24,
                                                 key=f"hoff_{i}_{j}"))
                if c5.button("✕", key=f"del_{i}_{j}"):
                    to_delete.append(j)
                else:
                    periods_i[j] = (pd_start_new, pd_end_new, h_on_new, h_off_new)

                st.caption(
                    f"{pd_start_new.strftime('%d %b %Y')} → "
                    f"{pd_end_new.strftime('%d %b %Y')}  |  "
                    f"daily {h_on_new:02d}:00–{h_off_new:02d}:00"
                )
                st.divider()

            for j in reversed(to_delete):
                periods_i.pop(j)

            if st.button("＋ Add period", key=f"add_{i}"):
                default_end = sim_start + _dt.timedelta(days=90)
                periods_i.append((sim_start, default_end, 0, 24))

            st.session_state[key_p][i] = periods_i

            if not periods_i:
                st.caption("No periods defined — circuit always off.")

            circuits_out.append(dict(
                Tf1_val=tf1_v,
                mw_val=mw_v,
                periods=list(periods_i),
            ))

    return dict(
        schedule_mode="calendar",
        circuits=circuits_out,
    )