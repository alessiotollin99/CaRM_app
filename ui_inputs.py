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
    col1, col2 = st.columns(2)
    with col1:
        Tm        = st.number_input("Mean annual air temperature Tm [°C]", value=13.0)
        R_ext     = st.number_input("External thermal resistance R_ext [m²·K/W]", value=0.04)
        At        = st.number_input("Annual temperature amplitude At [K]", value=10.0)
    with col2:
        tau_y     = st.number_input("Year duration tau_y [s]", value=365 * 24 * 3600)
        tau_shift = st.number_input("Phase shift tau_shift [s]", value=210 * 24 * 3600)

    return dict(
        Tm=Tm, R_ext=R_ext, absorptance=absorptance, eps=eps,
        At=At, tau_y=tau_y, tau_shift=tau_shift,
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
    """Render field layout + series groups. Returns dict or None for Single BHE."""
    if mode == "Single BHE":
        st.info("Field layout is not applicable for Single BHE configuration.")
        return {}

    st.subheader("Field layout")
    n_bhes = int(st.number_input("Total number of BHEs", value=9, min_value=1))
    layout = st.selectbox("Layout type", ["regular", "irregular"])

    if layout == "regular" and mode == "Multi BHE — Series":
        st.warning(
            "For series configuration the FLS thermal interaction model "
            "requires **irregular** layout with explicit borehole coordinates. "
            "Switch to irregular or the simulation may produce incorrect results.",
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
        st.caption("Comma-separated borehole IDs (0-indexed) per group")
        n_groups = int(st.number_input("Number of series groups", value=3, min_value=1))
        groups = {}
        for g in range(n_groups):
            raw = st.text_input(
                f"Group {g} borehole IDs",
                value=", ".join(str(x) for x in range(g * 3, g * 3 + 3)),
                key=f"grp_{g}",
            )
            groups[f"group_{g}"] = [int(x.strip()) for x in raw.split(",")]
        out["n_groups"] = n_groups
        out["groups"]   = groups

    return out


# =============================================================================
# Tab: Boundary Conditions  (Tf1 and mw profiles)
# =============================================================================

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _make_schedule(n_steps: int, dt: int, active_months: list,
                   active_hours: tuple, Tf1_val: float, mw_val: float,
                   n_inlets: int) -> tuple:
    """
    Build Tf1_arr and mw_arr from a constant value + monthly/hourly schedule.
    Off-hours: mw = 0, Tf1 = Tf1_val (irrelevant but non-zero).
    """
    Tf1_arr = np.full((n_inlets, n_steps), Tf1_val, dtype=np.float64)
    mw_arr  = np.zeros((n_inlets, n_steps), dtype=np.float64)

    dt_h = dt / 3600.0  # timestep in hours
    # cumulative hours per month
    cum_hours = np.cumsum([0] + [d * 24 for d in MONTH_DAYS])

    for step in range(n_steps):
        t_h = step * dt_h          # hour of simulation
        t_year = t_h % 8760        # hour within the year
        # which month?
        month_idx = next(
            (i for i in range(12) if cum_hours[i] <= t_year < cum_hours[i + 1]),
            11,
        )
        # which hour of day?
        hour_of_day = int(t_year % 24)
        h_start, h_end = active_hours
        if (MONTHS[month_idx] in active_months) and (h_start <= hour_of_day < h_end):
            mw_arr[:, step] = mw_val

    return Tf1_arr, mw_arr


def render_bc_tab(mode: str, n_steps_ref: int, dt_ref: int,
                  n_inlets_ref: int, field_p: dict):
    """
    Boundary conditions: Tf1 and mw profiles.
    n_inlets_ref: 1 for Single, n_bhes for Parallel, n_groups for Series.
    """
    st.subheader("Inlet conditions")

    bc_mode = st.radio(
        "Input mode",
        ["Constant + schedule", "From file (Excel)"],
        horizontal=True,
        key="bc_mode",
    )

    if bc_mode == "Constant + schedule":
        col1, col2 = st.columns(2)
        with col1:
            Tf1_val = st.number_input("Inlet fluid temperature Tf1 [°C]", value=2.0)
            mw_val  = st.number_input("Mass flow rate per circuit mw [kg/s]", value=0.1657)
        with col2:
            h_start = st.slider("Operation start [h of day]", 0, 23, 0)
            h_end   = st.slider("Operation end [h of day]",   1, 24, 24)

        active_months = st.multiselect(
            "Active months",
            MONTHS,
            default=MONTHS,
            key="bc_months",
        )

        if not active_months:
            st.warning("Select at least one active month.")

        st.caption(
            f"On: {', '.join(active_months) if active_months else '—'}  "
            f"| Hours: {h_start:02d}:00 – {h_end:02d}:00  "
            f"| Tf1 = {Tf1_val} °C  | mw = {mw_val} kg/s per circuit"
        )

        return dict(
            bc_mode="schedule",
            Tf1_val=Tf1_val,
            mw_val=mw_val,
            active_months=active_months,
            active_hours=(h_start, h_end),
        )

    else:  # From file
        st.caption(
            "Upload an Excel file with one sheet per circuit (or one sheet with columns "
            "`Tin_C` and `mw_kgs` if all circuits share the same profile). "
            "Rows = timesteps."
        )
        bc_file = st.file_uploader(
            "Boundary conditions file (.xlsx)",
            type=["xlsx"],
            key="bc_file",
        )

        if bc_file is None:
            st.info("Upload a file to continue.")
            return dict(bc_mode="file", bc_file=None)

        # preview
        import tempfile, pandas as pd
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(bc_file.read())
            tmp_path = tmp.name
        bc_file.seek(0)

        xl      = pd.ExcelFile(tmp_path)
        sheets  = xl.sheet_names
        st.caption(f"Sheets found: {', '.join(sheets)}")

        col1_name = st.selectbox("Column for Tf1 [°C]",  ["Tin_C", "Tin_C_clean"] + sheets, key="bc_col_tf1")
        col2_name = st.selectbox("Column for mw [kg/s]", ["mw_kgs", "mw_kgs_series_norm"] + sheets, key="bc_col_mw")

        same_profile = st.checkbox(
            "All circuits share the same profile (tile across inlets)",
            value=True,
        )

        return dict(
            bc_mode="file",
            bc_file_path=tmp_path,
            col_tf1=col1_name,
            col_mw=col2_name,
            same_profile=same_profile,
        )