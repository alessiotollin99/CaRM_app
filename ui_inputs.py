# -*- coding: utf-8 -*-
"""
UI components: input tabs for CaRM App.
"""

import datetime as dt

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
    D0_PIPE_TYPE_OVERRIDES,
    IRRIGATION_DEFAULTS,
    HEATFLUX_DEFAULTS,
    GROUND_DEFAULTS,
    GROUND_LAYER_DEFAULTS,
    FLUID_DEFAULTS,
    ENV_DEFAULTS,
    SIM_DEFAULTS,
    FIELD_DEFAULTS,
    PLANT_DEFAULTS,
)


# =============================================================================
# Tab: Ground
# =============================================================================

def render_ground_tab():
    d = GROUND_DEFAULTS
    st.subheader("Ground geometry & mesh")
    col1, col2 = st.columns(2)
    with col1:
        Tg         = st.number_input("Undisturbed ground temperature Tg [°C]", value=d["Tg"], key="cfg_Tg")
        L          = st.number_input("Borehole active length L [m]", value=d["L"], key="cfg_L")
        L_sup      = st.number_input("Surface layer thickness L_sup [m]", value=d["L_sup"], key="cfg_L_sup")
        L_inf      = st.number_input("Bottom layer thickness L_inf [m]", value=d["L_inf"], key="cfg_L_inf")
        rn         = st.number_input("Far-field radius rn [m]", value=d["rn"],
                                     help="Leave at 0 to auto-compute for multi-BHE fields",
                                     min_value=0.0, key="cfg_rn")
    with col2:
        n_mesh     = st.number_input("Radial mesh cells n_mesh [-]",        value=d["n_mesh"], min_value=1, key="cfg_n_mesh")
        m_mesh     = st.number_input("Axial mesh cells m_mesh [-]",         value=d["m_mesh"], min_value=1, key="cfg_m_mesh")
        m_mesh_sup = st.number_input("Axial cells surface layer [-]",       value=d["m_mesh_sup"],  min_value=1, key="cfg_m_mesh_sup")
        m_mesh_inf = st.number_input("Axial cells bottom layer [-]",        value=d["m_mesh_inf"], min_value=1, key="cfg_m_mesh_inf")

    st.subheader("Ground stratification")
    st.caption("Each row: thermal conductivity, specific heat, density, layer thickness")
    n_layers = st.number_input("Number of layers", value=d["n_layers"], min_value=1, max_value=10, key="cfg_n_layers")
    dl = GROUND_LAYER_DEFAULTS
    stratification = []
    for i in range(int(n_layers)):
        c1, c2, c3, c4 = st.columns(4)
        k_s   = c1.number_input(f"k [W/m·K] — layer {i+1}",    value=dl["k"],   key=f"k_{i}")
        cp_s  = c2.number_input(f"cp [J/kg·K] — layer {i+1}",  value=dl["cp"],  key=f"cp_{i}")
        rho_s = c3.number_input(f"ρ [kg/m³] — layer {i+1}",    value=dl["rho"], key=f"rho_{i}")
        th_s  = c4.number_input(f"thick [m] — layer {i+1}",    value=dl["th"],  key=f"th_{i}")
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
    d0_default = D0_PIPE_TYPE_OVERRIDES.get(pipe_type, d["D0"])

    st.subheader("Borehole geometry & grouting material")
    col1, col2 = st.columns(2)
    with col1:
        Lbore = st.number_input("Borehole length Lbore [m]",          value=d["Lbore"], key="cfg_Lbore")
        D0    = st.number_input("Borehole diameter D0 [m]",           value=d0_default, key="cfg_D0")
    with col2:
        cp_0  = st.number_input("Grout specific heat cp_0 [J/kg·K]", value=d["cp_0"], key="cfg_cp_0")
        rho_0 = st.number_input("Grout density ρ_0 [kg/m³]",         value=d["rho_0"], key="cfg_rho_0")
        k0    = st.number_input("Grout conductivity k0 [W/m·K]",     value=d["k0"], key="cfg_k0")

    st.subheader(f"Pipe parameters — {pipe_type}")
    pipe_params = {}

    if pipe_type == "SingleUtube":
        p = SINGLE_UTUBE_DEFAULTS
        col1, col2 = st.columns(2)
        with col1:
            pipe_params["Dpi"]          = st.number_input("Inside pipe diameter Dpi [m]",       value=p["Dpi"], key="cfg_su_Dpi")
            pipe_params["pipe_thick"]   = st.number_input("Pipe wall thickness [m]",            value=p["pipe_thick"], key="cfg_su_pipe_thick")
            pipe_params["pipe_spacing"] = st.number_input("Shank spacing [m]",                  value=p["pipe_spacing"], key="cfg_su_pipe_spacing")
        with col2:
            pipe_params["Rp0"]          = st.number_input("Pipe–wall resistance Rp0 [m·K/W]",   value=p["Rp0"], key="cfg_su_Rp0")
            pipe_params["RppB"]         = st.number_input("Pipe–pipe resistance RppB [m·K/W]",  value=p["RppB"], key="cfg_su_RppB")
            pipe_params["n_pipes"]      = int(st.number_input("Number of pipes [-]",            value=p["n_pipes"], min_value=2, key="cfg_su_n_pipes"))

    elif pipe_type == "DoubleUtube":
        p = DOUBLE_UTUBE_DEFAULTS
        col1, col2 = st.columns(2)
        with col1:
            pipe_params["Dpi"]          = st.number_input("Inside pipe diameter Dpi [m]",              value=p["Dpi"], key="cfg_du_Dpi")
            pipe_params["pipe_thick"]   = st.number_input("Pipe wall thickness [m]",                   value=p["pipe_thick"], key="cfg_du_pipe_thick")
            pipe_params["pipe_spacing"] = st.number_input("Shank spacing [m]",                         value=p["pipe_spacing"], key="cfg_du_pipe_spacing")
        with col2:
            pipe_params["Rp0"]          = st.number_input("Pipe–wall resistance Rp0 [m·K/W]",          value=p["Rp0"], key="cfg_du_Rp0")
            pipe_params["RppB"]         = st.number_input("Pipe–pipe resistance (opposite) RppB [m·K/W]", value=p["RppB"], key="cfg_du_RppB")
            pipe_params["RppA"]         = st.number_input("Pipe–pipe resistance (adjacent) RppA [m·K/W]", value=p["RppA"], key="cfg_du_RppA")
            pipe_params["n_pipes"]      = int(st.number_input("Number of pipes [-]",                   value=p["n_pipes"], min_value=4, key="cfg_du_n_pipes"))
            pipe_params["connection"]   = st.selectbox("Connection (P = parallel, S = series)", ["P", "S"], key="cfg_du_connection")

    elif pipe_type == "Coaxial":
        p = COAXIAL_DEFAULTS
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Inner pipe (1)**")
            pipe_params["Dp1i"]        = st.number_input("Inside diameter Dp1i [m]",     value=p["Dp1i"], key="cfg_cx_Dp1i")
            pipe_params["pipe1_thick"] = st.number_input("Wall thickness [m]",           value=p["pipe1_thick"], key="p1t")
            pipe_params["k_pipe1"]     = st.number_input("Conductivity k1 [W/m·K]",     value=p["k_pipe1"], key="cfg_cx_k_pipe1")
        with col2:
            st.markdown("**Outer pipe (2)**")
            pipe_params["Dp2i"]        = st.number_input("Inside diameter Dp2i [m]",     value=p["Dp2i"], key="cfg_cx_Dp2i")
            pipe_params["pipe2_thick"] = st.number_input("Wall thickness [m]",           value=p["pipe2_thick"], key="p2t")
            pipe_params["k_pipe2"]     = st.number_input("Conductivity k2 [W/m·K]",     value=p["k_pipe2"], key="cfg_cx_k_pipe2")
        pipe_params["supply_and_return"] = st.selectbox(
            "Inlet pipe (1→2: supply in inner / 2→1: supply in annulus)",
            ["1_2", "2_1"], key="cfg_cx_supply_and_return",
        )

    elif pipe_type == "Helical":
        p = HELICAL_DEFAULTS
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Inner pipe (1) — straight**")
            pipe_params["Dpi1"]        = st.number_input("Inside diameter Dpi1 [m]", value=p["Dpi1"], key="cfg_he_Dpi1")
            pipe_params["pipe1_thick"] = st.number_input("Wall thickness [m]",       value=p["pipe1_thick"], key="hp1t")
            st.markdown("**Helical pipe (2)**")
            pipe_params["Dpi2"]        = st.number_input("Inside diameter Dpi2 [m]", value=p["Dpi2"], key="cfg_he_Dpi2")
            pipe_params["pipe2_thick"] = st.number_input("Wall thickness [m]",       value=p["pipe2_thick"], key="hp2t")
            pipe_params["k_pipe"]      = st.number_input("Pipe conductivity [W/m·K]",value=p["k_pipe"], key="cfg_he_k_pipe")
        with col2:
            pipe_params["rih"]         = st.number_input("Inner helix radius rih [m]", value=p["rih"],
                                                          help="= (outer helix diameter / 2) − pipe outside radius",
                                                          key="cfg_he_rih")
            pipe_params["P_hel"]       = st.number_input("Pitch P [m]",               value=p["P_hel"], key="cfg_he_P_hel")
            pipe_params["supply_and_return"] = st.selectbox(
                "Inlet pipe (1→2 / 2→1)", ["1_2", "2_1"], key="cfg_he_supply_and_return",
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

    variable_props = render_variable_props_section(pipe_type, D0)

    return dict(Lbore=Lbore, D0=D0, cp_0=cp_0, rho_0=rho_0, k0=k0,
               variable_props=variable_props, **pipe_params)


# =============================================================================
# Variable grout properties (soil moisture / irrigation) — Helical only
# =============================================================================

def render_variable_props_section(pipe_type: str, D0: float) -> dict:
    """
    Render the soil-moisture / irrigation controls, shown only for Helical
    BHEs (see carm.properties.BoreholeGeometry — irrigation is only feasible
    with shallow helical heat exchangers).

    Returns a dict with keys: enabled, soil_type, D_irrigation, perf_fraction,
    periods (list of (start_date, end_date, rate) tuples).
    """
    variable_props = dict(
        enabled=False, soil_type=None, D_irrigation=None,
        perf_fraction=None, periods=[],
    )

    st.divider()

    if pipe_type != "Helical":
        st.caption(
            "💧 Variable grout properties (soil moisture / irrigation) are "
            "only available with the **Helical** pipe configuration."
        )
        return variable_props

    st.subheader("Variable grout properties (soil moisture / irrigation)")
    vp_enabled = st.checkbox(
        "Enable variable grout properties",
        value=IRRIGATION_DEFAULTS["enabled"],
        help=(
            "Models grout thermal conductivity, heat capacity, and density as "
            "a function of soil moisture content, driven by irrigation and "
            "gravity drainage/evaporation (Brooks-Corey model)."
        ),
        key="cfg_vp_enabled",
    )
    variable_props["enabled"] = vp_enabled

    if not vp_enabled:
        return variable_props

    st.caption(
        "ρ_0 above is now interpreted as the **dry** grout density — soil "
        "moisture adds the water's own contribution on top of it."
    )

    d = IRRIGATION_DEFAULTS
    soil_types = ["sand", "loam", "clay"]
    col1, col2, col3 = st.columns(3)
    with col1:
        soil_type = st.selectbox("Soil type", soil_types,
                                 index=soil_types.index(d["soil_type"]), key="cfg_vp_soil_type")
    with col2:
        D_irrigation = st.number_input(
            "Irrigation pipe diameter D_irrigation [m]",
            value=d["D_irrigation"], min_value=0.0001, max_value=D0,
            format="%.4f", key="cfg_vp_D_irrigation",
        )
    with col3:
        perf_fraction = st.number_input(
            "Perforation fraction [-]",
            value=d["perf_fraction"], min_value=0.0, max_value=0.999,
            key="cfg_vp_perf_fraction",
        )
    variable_props.update(
        soil_type=soil_type, D_irrigation=D_irrigation, perf_fraction=perf_fraction,
    )

    st.markdown("**Irrigation schedule**")
    st.caption(
        "Add one or more periods (date range + constant rate). Outside all "
        "periods, irrigation is off."
    )

    key_p = "irrigation_periods"
    if key_p not in st.session_state:
        st.session_state[key_p] = []
    periods = st.session_state[key_p]

    to_delete = []
    for j, (pd_start, pd_end, rate) in enumerate(periods):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        pd_start_new = c1.date_input("From", value=pd_start, key=f"irr_from_{j}")
        pd_end_new   = c2.date_input("To",   value=pd_end,   key=f"irr_to_{j}")
        rate_new = float(c3.number_input(
            "Rate [m/s]", value=rate, key=f"irr_rate_{j}", format="%.2e",
        ))
        if c4.button("✕", key=f"irr_del_{j}"):
            to_delete.append(j)
        else:
            periods[j] = (pd_start_new, pd_end_new, rate_new)

    for j in reversed(to_delete):
        periods.pop(j)

    if st.button("＋ Add irrigation period"):
        # Anchor the default period to the Environment tab's simulation start
        # (already in session_state after the first render), so a freshly
        # added period actually overlaps the simulated window by default.
        anchor = st.session_state.get("env_tau_date", dt.date(2024, 1, 1))
        periods.append((anchor, anchor + dt.timedelta(days=14), d["water_rate"]))

    st.session_state[key_p] = periods
    if not periods:
        st.caption("No irrigation periods defined — water_input stays at zero.")

    variable_props["periods"] = list(periods)
    return variable_props


def build_water_input_from_schedule(
    n_steps: int, dt_s: int, sim_start, periods: list,
) -> np.ndarray:
    """
    Build a water_input time series [m/s] from a list of
    (start_date, end_date, rate) periods. Outside all periods, water_input
    is zero. Mirrors _build_mw_tf1_from_schedule's date-to-step conversion.
    """
    water_input = np.zeros(n_steps, dtype=np.float64)
    if sim_start is None:
        return water_input

    sim_start_dt = dt.datetime(sim_start.year, sim_start.month, sim_start.day, 0)
    for (pd_start, pd_end, rate) in periods:
        start_dt = dt.datetime(pd_start.year, pd_start.month, pd_start.day, 0)
        end_dt   = dt.datetime(pd_end.year, pd_end.month, pd_end.day, 23, 59, 59)
        step_start = max(0, int((start_dt - sim_start_dt).total_seconds() // dt_s))
        step_end   = min(n_steps, int((end_dt - sim_start_dt).total_seconds() // dt_s) + 1)
        if step_end > step_start:
            water_input[step_start:step_end] = rate

    return water_input


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
        fluid_name    = st.selectbox("Fluid", ["Water", "Ethylene glycol", "Propylene glycol"], key="cfg_fluid_name")
        T_ref         = st.number_input("Reference temperature [°C]", value=FLUID_DEFAULTS["T_ref"],
                                        help="Typically mean fluid temperature during operation",
                                        key="cfg_T_ref")
    with col2:
        concentration = 0.0
        if fluid_name != "Water":
            concentration = float(st.slider("Glycol concentration [%]",
                                            min_value=0, max_value=60, value=FLUID_DEFAULTS["concentration"], step=1,
                                            key="cfg_concentration"))

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
        k_w   = st.number_input("k_w [W/m·K]",   value=float(f"{k_w:.6f}"), key="cfg_kw_override")
        rho_w = st.number_input("ρ_w [kg/m³]",   value=float(f"{rho_w:.4f}"), key="cfg_rhow_override")
    with col2:
        cp_w  = st.number_input("cp_w [J/kg·K]", value=float(f"{cp_w:.4f}"), key="cfg_cpw_override")
        ni_w  = st.number_input("ν_w [m²/s]",    value=ni_w, format="%.3e", key="cfg_niw_override")

    return dict(k_w=k_w, rho_w=rho_w, cp_w=cp_w, ni_w=ni_w)


# =============================================================================
# Tab: Environment
# =============================================================================

def render_env_tab():
    st.subheader("Surface material")
    material = st.selectbox("Surface type", list(SURFACE_MATERIALS.keys()), key="cfg_material")
    preset   = SURFACE_MATERIALS[material]

    col1, col2 = st.columns(2)
    with col1:
        absorptance = st.number_input(
            "Surface absorptance [-]",
            value=preset[0] if preset[0] is not None else ENV_DEFAULTS["absorptance_manual"],
            min_value=0.0, max_value=1.0,
            disabled=(material != "Manual"),
            key="cfg_absorptance",
        )
    with col2:
        eps = st.number_input(
            "Surface emittance [-]",
            value=preset[1] if preset[1] is not None else ENV_DEFAULTS["eps_manual"],
            min_value=0.0, max_value=1.0,
            disabled=(material != "Manual"),
            key="cfg_eps",
        )

    st.subheader("Environmental properties")
    import datetime as _dt_env

    def _doy_seconds(date: _dt_env.date) -> float:
        return float((date - _dt_env.date(date.year, 1, 1)).days * 86400)

    col1, col2 = st.columns(2)
    with col1:
        Tm    = st.number_input("Mean annual air temperature Tm [°C]", value=ENV_DEFAULTS["Tm"], key="cfg_Tm")
        R_ext = st.number_input("External thermal resistance R_ext [m²·K/W]", value=ENV_DEFAULTS["R_ext"], key="cfg_R_ext")
        At    = st.number_input("Annual temperature amplitude At [K]", value=ENV_DEFAULTS["At"], key="cfg_At")
        tau_y = st.number_input("Year duration tau_y [s]", value=ENV_DEFAULTS["tau_y"], key="cfg_tau_y")
    with col2:
        st.markdown("**Simulation start date (τ)**")
        st.caption("Seconds from Jan 1 to the simulation start — used as τ in EnvironmentalProperties.")
        tau_date = st.date_input(
            "Simulation start",
            value=ENV_DEFAULTS["tau_date"],
            key="env_tau_date",
        )
        tau = _doy_seconds(tau_date)
        st.metric("τ [s]", f"{tau:,.0f}")

        st.markdown("**Date of minimum surface temperature (τ_shift)**")
        st.caption("Typically mid-February — day when surface temperature reaches its annual minimum.")
        shift_date = st.date_input(
            "Date of minimum T",
            value=ENV_DEFAULTS["tau_shift_date"],
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
        dt      = st.number_input("Time step dt [s]",  value=SIM_DEFAULTS["dt"], key="cfg_dt")
        n_steps = st.number_input("Number of steps [-]", value=SIM_DEFAULTS["n_steps"], min_value=1, key="cfg_n_steps")
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
    d = FIELD_DEFAULTS
    n_bhes = int(st.number_input("Total number of BHEs", value=d["n_bhes"], min_value=1, key="cfg_field_n_bhes"))
    layout = st.selectbox("Layout type", ["regular", "irregular"], key="cfg_field_layout")

    if layout == "regular" and mode == "Multi BHE — Series":
        st.warning(
            "For series configuration the FLS model requires **irregular** layout "
            "with explicit borehole coordinates."
        )

    col1, col2 = st.columns(2)
    with col1:
        x_min = st.number_input("Field x_min [m]", value=d["x_min"], key="cfg_field_x_min")
        y_min = st.number_input("Field y_min [m]", value=d["y_min"], key="cfg_field_y_min")
    with col2:
        x_max = st.number_input("Field x_max [m]", value=d["x_max"], key="cfg_field_x_max")
        y_max = st.number_input("Field y_max [m]", value=d["y_max"], key="cfg_field_y_max")

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
        for (pd_start, pd_end, h_on, h_off, tf1_period) in circ["periods"]:
            # iterate day by day within the period
            day = pd_start
            while day <= pd_end:
                for h in range(h_on, h_off):
                    t = _dt.datetime(day.year, day.month, day.day, h)
                    delta_s = (t - sim_start_dt).total_seconds()
                    if 0 <= delta_s < n_steps * dt_s:
                        step = int(delta_s / dt_s)
                        mw_arr[i, step]  = circ["mw_val"]
                        Tf1_arr[i, step] = tf1_period
                day += _dt.timedelta(days=1)

    return Tf1_arr, mw_arr


def render_heat_flux_tab(n_steps: int, dt_s: int, sim_start) -> dict:
    """
    Heat flux mode schedule: the plant is driven by a building load
    (Q_buildings) and a supply temperature (T_supply) instead of a fixed
    inlet temperature. Pump flow (mw) switches on automatically whenever
    the load is non-zero — see ``carm.simulation.solver.Simulation``
    (``heat_flux=True`` requires ``Tf1=None``).

    Returns dict with keys: schedule_mode="heat_flux", heat_flux=True,
    Q_buildings, T_supply (arrays, shape (n_steps,)), mw_value (float).
    """
    d = HEATFLUX_DEFAULTS
    st.subheader("Building load schedule")
    st.caption(
        "Add one or more load periods. Positive Q_load = heat extracted "
        "from the ground (heating); negative = heat injected into the "
        "ground (cooling). Outside all periods the plant is off (mw = 0)."
    )

    mw_value = st.number_input(
        "Pump mass flow rate while a period is active, mw [kg/s]",
        value=d["mw_value"], min_value=0.0,
        help="Applied to every circuit whenever Q_buildings != 0; 0 otherwise.",
        key="cfg_hf_mw_value",
    )

    key_p = "heat_flux_periods"
    if key_p not in st.session_state:
        st.session_state[key_p] = []
    periods = st.session_state[key_p]

    to_delete = []
    for j, (pd_start, pd_end, q_load, t_supply) in enumerate(periods):
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
        pd_start_new = c1.date_input("From", value=pd_start, key=f"hf_from_{j}")
        pd_end_new   = c2.date_input("To",   value=pd_end,   key=f"hf_to_{j}")
        q_load_new = float(c3.number_input(
            "Q_load [W]", value=q_load, key=f"hf_q_{j}",
        ))
        t_supply_new = float(c4.number_input(
            "T_supply [°C]", value=t_supply, key=f"hf_ts_{j}",
        ))
        if c5.button("✕", key=f"hf_del_{j}"):
            to_delete.append(j)
        else:
            periods[j] = (pd_start_new, pd_end_new, q_load_new, t_supply_new)
        st.caption(
            f"{pd_start_new.strftime('%d %b %Y')} → {pd_end_new.strftime('%d %b %Y')}  |  "
            f"Q_load = {q_load_new:.0f} W  |  T_supply = {t_supply_new:.1f} °C"
        )
        st.divider()

    for j in reversed(to_delete):
        periods.pop(j)

    if st.button("＋ Add load period"):
        anchor = periods[-1][1] if periods else (sim_start or dt.date(2024, 1, 1))
        periods.append(
            (anchor, anchor + dt.timedelta(days=90), d["Q_load"], d["T_supply"])
        )

    st.session_state[key_p] = periods
    if not periods:
        st.caption("No periods defined — plant always off.")

    Q_buildings, T_supply = _build_heat_flux_arrays(n_steps, dt_s, sim_start, periods)

    return dict(
        schedule_mode="heat_flux",
        heat_flux=True,
        Q_buildings=Q_buildings,
        T_supply=T_supply,
        mw_value=mw_value,
    )


def _build_heat_flux_arrays(
    n_steps: int, dt_s: int, sim_start, periods: list,
) -> tuple:
    """
    Build Q_buildings and T_supply time series [W], [°C] from a list of
    (start_date, end_date, Q_load, T_supply) periods. Outside all periods,
    Q_buildings is zero (plant off) and T_supply is left at 0.
    """
    Q_buildings = np.zeros(n_steps, dtype=np.float64)
    T_supply    = np.zeros(n_steps, dtype=np.float64)
    if sim_start is None:
        return Q_buildings, T_supply

    sim_start_dt = dt.datetime(sim_start.year, sim_start.month, sim_start.day, 0)
    for (pd_start, pd_end, q_load, t_supply) in periods:
        start_dt = dt.datetime(pd_start.year, pd_start.month, pd_start.day, 0)
        end_dt   = dt.datetime(pd_end.year, pd_end.month, pd_end.day, 23, 59, 59)
        step_start = max(0, int((start_dt - sim_start_dt).total_seconds() // dt_s))
        step_end   = min(n_steps, int((end_dt - sim_start_dt).total_seconds() // dt_s) + 1)
        if step_end > step_start:
            Q_buildings[step_start:step_end] = q_load
            T_supply[step_start:step_end] = t_supply

    return Q_buildings, T_supply


def render_plant_schedule_tab(mode: str, n_steps: int, dt_s: int,
                              field_p: dict, sim_start):
    """
    Plant Schedule tab.
    sim_start comes from env_p["sim_start"] (set in Environment tab).
    Returns dict with keys:
        schedule_mode : "calendar" | "file" | "heat_flux"
        circuits      : list of circuit dicts  (calendar only)
        bc_file_path, col_tf1, col_mw, same_profile  (file only)
        heat_flux, Q_buildings, T_supply, mw_value  (heat_flux only)
    """
    st.subheader("Simulation type")
    heat_flux_enabled = st.checkbox(
        "Enable heat flux mode (drive the plant with a building load "
        "instead of a fixed inlet temperature)",
        value=PLANT_DEFAULTS["heat_flux_enabled"], key="heat_flux_enabled",
        help=(
            "When enabled, CaRM derives the inlet fluid temperature "
            "internally from a building heating/cooling load (Q_buildings) "
            "and a supply temperature (T_supply), via a COP/EER heat pump "
            "model. When disabled (default), Tf1 is set directly as below."
        ),
    )
    if heat_flux_enabled:
        return render_heat_flux_tab(n_steps=n_steps, dt_s=dt_s, sim_start=sim_start)

    st.divider()

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
        same    = st.checkbox("All circuits share the same profile", value=PLANT_DEFAULTS["same_profile"], key="cfg_bc_same_profile")

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
            mw_v = st.number_input("mw [kg/s]", value=PLANT_DEFAULTS["mw"], key=f"mw_{i}")

            st.markdown("**Operating periods**")
            periods_i = st.session_state[key_p][i]
            to_delete = []

            for j, (pd_start, pd_end, h_on, h_off, tf1_p) in enumerate(periods_i):
                st.markdown(f"*Period {j+1}*")
                c1, c2, c3 = st.columns(3)
                pd_start_new = c1.date_input("From date", value=pd_start,
                                              key=f"pds_{i}_{j}")
                pd_end_new   = c2.date_input("To date",   value=pd_end,
                                              key=f"pde_{i}_{j}")
                tf1_p_new = float(c3.number_input("Tf1 [°C]", value=tf1_p,
                                                   key=f"tf1p_{i}_{j}"))
                c4, c5, c6 = st.columns([2, 2, 1])
                h_on_new  = int(c4.number_input("Daily start [h]", value=h_on,
                                                 min_value=0, max_value=23,
                                                 key=f"hon_{i}_{j}"))
                h_off_new = int(c5.number_input("Daily end [h]",   value=h_off,
                                                 min_value=1, max_value=24,
                                                 key=f"hoff_{i}_{j}"))
                if c6.button("✕", key=f"del_{i}_{j}"):
                    to_delete.append(j)
                else:
                    periods_i[j] = (pd_start_new, pd_end_new, h_on_new, h_off_new, tf1_p_new)

                st.caption(
                    f"{pd_start_new.strftime('%d %b %Y')} → "
                    f"{pd_end_new.strftime('%d %b %Y')}  |  "
                    f"daily {h_on_new:02d}:00–{h_off_new:02d}:00  |  "
                    f"Tf1 = {tf1_p_new:.1f} °C"
                )
                st.divider()

            for j in reversed(to_delete):
                periods_i.pop(j)

            if st.button("＋ Add period", key=f"add_{i}"):
                default_end = sim_start + _dt.timedelta(days=90)
                default_tf1 = circuits_out[-1]["periods"][-1][4] if circuits_out and circuits_out[-1]["periods"] else PLANT_DEFAULTS["tf1_new_period"]
                periods_i.append((sim_start, default_end, 0, 24, default_tf1))

            st.session_state[key_p][i] = periods_i

            if not periods_i:
                st.caption("No periods defined — circuit always off.")

            circuits_out.append(dict(
                mw_val=mw_v,
                periods=list(periods_i),
            ))

    return dict(
        schedule_mode="calendar",
        circuits=circuits_out,
    )