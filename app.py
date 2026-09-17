# -*- coding: utf-8 -*-
"""
CaRM App — main entry point.

Run with:
    streamlit run app.py
"""

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from ui_inputs import (
    render_ground_tab,
    render_borehole_tab,
    render_fluid_tab,
    render_env_tab,
    render_sim_tab,
    render_field_tab,
    render_plant_schedule_tab,
    _build_mw_tf1_from_schedule,
    build_water_input_from_schedule,
)
from ui_results import (
    render_ground_surface,
    render_ground_middle,
    render_ground_bottom,
    render_borehole,
    render_timeseries,
    render_grout_properties,
    render_ground_energy_balance,
    _build_slices,
)

from carm import (
    BoreholeGeometry, BoreholeMesh, BoreholeThermalProperties,
    Coaxial, DoubleUtube, Helical, SingleUtube,
)
from carm import EnvironmentalProperties, EnvironmentalTimeSeries
from carm import FieldInput, Fluid, GroundGeometry, GroundMesh
from carm import PhysicalModel, Simulation

from config_io import serialize_config, apply_config

# =============================================================================
# Page config
# =============================================================================

st.set_page_config(page_title="CaRM", page_icon="🌡️", layout="wide")
st.title("CaRM — Borehole Heat Exchanger Simulation")

# =============================================================================
# Sidebar
# =============================================================================

def _preview_excel(file, required_cols: list, label: str):
    """
    Read an uploaded Excel file, show a small preview, and validate that the
    required columns are present. Returns the parsed DataFrame, or None if
    the file could not be read or is missing a required column.
    """
    try:
        df = pd.read_excel(file)
    except Exception as e:
        st.sidebar.error(f"{label}: could not read file — {e}")
        return None

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.sidebar.error(
            f"{label}: missing column(s) {missing}. Found: {list(df.columns)}"
        )
        return None

    with st.sidebar.expander(f"{label} — preview ({len(df)} rows)"):
        st.dataframe(df.head(5), use_container_width=True)

    file.seek(0)  # rewind so it can be re-read at run time
    return df


st.sidebar.header("Session configuration")
st.sidebar.caption(
    "Save every input parameter to a file, or load a previously saved one. "
    "Uploaded data files (environmental data, field layout) are not included "
    "and must be re-uploaded by hand."
)
config_upload = st.sidebar.file_uploader(
    "📂 Load configuration (.json)", type=["json"],
    key=f"_config_upload_widget_{st.session_state.get('_config_upload_nonce', 0)}",
)
if config_upload is not None:
    apply_config(st.session_state, config_upload.read().decode("utf-8"))
    st.session_state["_config_upload_nonce"] = st.session_state.get("_config_upload_nonce", 0) + 1
    st.sidebar.success("Configuration loaded.")
    st.rerun()

st.sidebar.download_button(
    "💾 Save configuration",
    data=serialize_config(st.session_state),
    file_name="carm_config.json",
    mime="application/json",
    use_container_width=True,
)

st.sidebar.divider()
st.sidebar.header("Simulation mode")
mode = st.sidebar.radio(
    "Configuration",
    ["Single BHE", "Multi BHE — Parallel", "Multi BHE — Series"],
    key="cfg_mode",
)
pipe_type = st.sidebar.selectbox(
    "Pipe configuration",
    ["SingleUtube", "DoubleUtube", "Coaxial", "Helical"],
    key="cfg_pipe_type",
)

st.sidebar.divider()
st.sidebar.header("Input files")

env_file = st.sidebar.file_uploader(
    "Environmental data (.xlsx)", type=["xlsx"],
    help="Required columns: T_ext [°C], SolarRad [W/m²].",
)
if env_file is not None:
    _preview_excel(env_file, ["T_ext", "SolarRad"], "Environmental data")

spacing_file = None
if mode in ["Multi BHE — Parallel", "Multi BHE — Series"]:
    spacing_file = st.sidebar.file_uploader(
        "Field layout (.xlsx)", type=["xlsx"],
        help="Required columns: x [m], y [m] — one row per borehole.",
    )
    if spacing_file is not None:
        _preview_excel(spacing_file, ["x", "y"], "Field layout")

# =============================================================================
# Input tabs  — Field Layout shown conditionally
# =============================================================================

if mode == "Single BHE":
    tab_ground, tab_bore, tab_fluid, tab_env, tab_sim, tab_bc = st.tabs(
        ["Ground", "Borehole", "Fluid", "Environment", "Simulation", "Plant Schedule"]
    )
    tab_field = None
else:
    tab_ground, tab_bore, tab_fluid, tab_env, tab_sim, tab_field, tab_bc = st.tabs(
        ["Ground", "Borehole", "Fluid", "Environment", "Simulation",
         "Field Layout", "Plant Schedule"]
    )

with tab_ground:
    ground_p = render_ground_tab()

with tab_bore:
    bore_p = render_borehole_tab(pipe_type)

with tab_fluid:
    fluid_p = render_fluid_tab()

with tab_env:
    env_p = render_env_tab()

with tab_sim:
    sim_p = render_sim_tab()

field_p = {}
if tab_field is not None:
    with tab_field:
        field_p = render_field_tab(mode)

# n_inlets depends on mode and groups — compute a best-effort value for BC tab
_n_inlets_est = 1
if mode == "Multi BHE — Parallel":
    _n_inlets_est = field_p.get("n_bhes", 1)
elif mode == "Multi BHE — Series":
    _n_inlets_est = field_p.get("n_groups", 1)

with tab_bc:
    bc_p = render_plant_schedule_tab(
        mode=mode,
        n_steps=sim_p["n_steps"],
        dt_s=sim_p["dt"],
        field_p=field_p,
        sim_start=env_p.get("sim_start"),
    )

# =============================================================================
# Run
# =============================================================================

st.divider()
save_results = st.checkbox(
    "Save results to disk (results/ folder, .npz archive)",
    value=False,
    help="Passed through as save_results to Simulation.run().",
    key="cfg_save_results",
)
run = st.button("▶ Run simulation", type="primary", use_container_width=True)

if run:
    if env_file is None:
        st.error("Please upload the environmental data file.")
        st.stop()
    if mode in ["Multi BHE — Parallel", "Multi BHE — Series"] and spacing_file is None:
        st.error("Please upload the field layout file.")
        st.stop()
    if bc_p.get("schedule_mode") == "file" and bc_p.get("bc_file_path") is None:
        st.error("Please upload the boundary conditions file.")
        st.stop()

    with st.spinner("Running CaRM simulation…"):

        # --- CaRM objects ---
        vp = bore_p["variable_props"]
        fluid     = Fluid(**fluid_p)
        bore_geom = BoreholeGeometry(
            Lbore=bore_p["Lbore"], D0=bore_p["D0"],
            D_irrigation=vp["D_irrigation"] if vp["enabled"] else None,
            perf_fraction=vp["perf_fraction"] if vp["enabled"] else None,
        )
        bore_mesh     = BoreholeMesh(m_mesh=ground_p["m_mesh"])
        bore_th_props = BoreholeThermalProperties(
            cp_0=bore_p["cp_0"], rho_0=bore_p["rho_0"], k0=bore_p["k0"],
            soil_type=vp["soil_type"] if vp["enabled"] else None,
        )

        if pipe_type == "SingleUtube":
            props_b = SingleUtube(
                geom=bore_geom, mesh=bore_mesh, thermalprops=bore_th_props, fluid=fluid,
                Rp0=bore_p["Rp0"], RppB=bore_p["RppB"],
                pipe_spacing=bore_p["pipe_spacing"], pipe_thick=bore_p["pipe_thick"],
                Dpi=bore_p["Dpi"], n_pipes=bore_p["n_pipes"],
            )
        elif pipe_type == "DoubleUtube":
            props_b = DoubleUtube(
                geom=bore_geom, mesh=bore_mesh, thermalprops=bore_th_props, fluid=fluid,
                Rp0=bore_p["Rp0"], RppB=bore_p["RppB"], RppA=bore_p["RppA"],
                pipe_spacing=bore_p["pipe_spacing"], pipe_thick=bore_p["pipe_thick"],
                Dpi=bore_p["Dpi"], n_pipes=bore_p["n_pipes"],
                connection=bore_p["connection"],
            )
        elif pipe_type == "Coaxial":
            props_b = Coaxial(
                geom=bore_geom, mesh=bore_mesh, thermalprops=bore_th_props, fluid=fluid,
                supply_and_return=bore_p["supply_and_return"],
                Dp1i=bore_p["Dp1i"], Dp2i=bore_p["Dp2i"],
                pipe1_thick=bore_p["pipe1_thick"], pipe2_thick=bore_p["pipe2_thick"],
                k_pipe1=bore_p["k_pipe1"], k_pipe2=bore_p["k_pipe2"],
            )
        elif pipe_type == "Helical":
            props_b = Helical(
                geom=bore_geom, mesh=bore_mesh, thermalprops=bore_th_props, fluid=fluid,
                Dpi1=bore_p["Dpi1"], Dpi2=bore_p["Dpi2"],
                P=bore_p["P_hel"], Lp2tot=bore_p["Lp2tot"],
                supply_and_return=bore_p["supply_and_return"],
                rih=bore_p["rih"], pipe_thick=bore_p["pipe1_thick"],
                N=bore_p["N_hel"], k_pipe=bore_p["k_pipe"],
            )

        rn_val      = ground_p["rn"] if (mode == "Single BHE" and ground_p["rn"] > 0) else None
        ground_geom = GroundGeometry(
            rn=rn_val, D0=bore_p["D0"], L=ground_p["L"],
            L_sup=ground_p["L_sup"], L_inf=ground_p["L_inf"],
        )
        ground_mesh = GroundMesh(
            n_mesh=ground_p["n_mesh"], m_mesh=ground_p["m_mesh"],
            m_mesh_sup=ground_p["m_mesh_sup"], m_mesh_inf=ground_p["m_mesh_inf"],
        )

        env_df = pd.read_excel(env_file)
        env_input = EnvironmentalTimeSeries.from_array(
            Tm=env_p["Tm"],
            T_ext=env_df["T_ext"].to_numpy(),
            SolarRad=env_df["SolarRad"].to_numpy(),
        )
        if vp["enabled"]:
            env_input.water_input = build_water_input_from_schedule(
                n_steps=sim_p["n_steps"], dt_s=sim_p["dt"],
                sim_start=env_p.get("sim_start"), periods=vp["periods"],
            )
        env_props = EnvironmentalProperties(
            R_ext=env_p["R_ext"], absorptance=env_p["absorptance"], eps=env_p["eps"],
            At=env_p["At"], tau=env_p["tau"], tau_y=env_p["tau_y"], tau_shift=env_p["tau_shift"],
        )

        # --- field ---
        myfield = None
        if mode in ["Multi BHE — Parallel", "Multi BHE — Series"]:
            field_df = pd.read_excel(spacing_file)
            myfield = FieldInput(
                n_bhes=field_p["n_bhes"],
                xmin=field_p["x_min"], ymin=field_p["y_min"],
                xmax=field_p["x_max"], ymax=field_p["y_max"],
                rb=bore_p["D0"] / 2.0,
                layout=field_p["layout"],
            )
            myfield.from_array(field_df["x"].to_numpy(), field_df["y"].to_numpy())

        model_kwargs = dict(
            ground_geom=ground_geom, ground_mesh=ground_mesh,
            borehole=props_b, fluid=fluid,
            Tg=ground_p["Tg"], stratification=ground_p["stratification"],
        )
        if myfield is not None:
            model_kwargs["fieldinput"] = myfield
        model = PhysicalModel(**model_kwargs)

        # --- inlet count ---
        n_steps = sim_p["n_steps"]
        dt      = sim_p["dt"]
        if mode == "Single BHE":
            n_inlets = 1
        elif mode == "Multi BHE — Parallel":
            n_inlets = field_p["n_bhes"]
        else:
            n_inlets = field_p["n_groups"]

        # --- build Tf1_arr / mw_arr, or Q_buildings / T_supply for heat flux mode ---
        heat_flux_mode = bc_p.get("heat_flux", False)
        Q_buildings = T_supply = None
        if heat_flux_mode:
            Q_buildings = bc_p["Q_buildings"]
            T_supply    = bc_p["T_supply"]
            Tf1_arr     = None
            mw_row      = np.where(Q_buildings != 0, bc_p["mw_value"], 0.0)
            mw_arr      = np.tile(mw_row, (n_inlets, 1))
        elif bc_p["schedule_mode"] == "calendar":
            Tf1_arr, mw_arr = _build_mw_tf1_from_schedule(
                n_steps=n_steps,
                dt_s=dt,
                sim_start=env_p["sim_start"],
                circuits=bc_p["circuits"],
            )
        else:
            # from file
            df_bc = pd.read_excel(bc_p["bc_file_path"])
            tf1_raw = df_bc[bc_p["col_tf1"]].to_numpy()[:n_steps]
            mw_raw  = df_bc[bc_p["col_mw"]].to_numpy()[:n_steps]
            Tf1_arr = np.tile(tf1_raw, (n_inlets, 1))
            mw_arr  = np.tile(mw_raw,  (n_inlets, 1))

        # --- simulation ---
        sim_kwargs = dict(
            model=model, envinput=env_input, timesteps=dt, n_steps=n_steps,
            envprops=env_props, mw_tot=mw_arr,
        )
        if heat_flux_mode:
            sim_kwargs.update(
                heat_flux=True, Q_buildings=Q_buildings, T_supply=T_supply, Tf1=None,
            )
        else:
            sim_kwargs["Tf1"] = Tf1_arr
        if mode == "Multi BHE — Series":
            sim_kwargs["groups"] = field_p["groups"]

        simulation = Simulation(**sim_kwargs)

        if mode == "Multi BHE — Parallel":
            T_history = simulation.run(parallel=True, save_results=save_results)
        elif mode == "Multi BHE — Series":
            T_history = simulation.run(series=True, save_results=save_results)
        else:
            T_history = simulation.run(save_results=save_results)

        if heat_flux_mode and mode != "Multi BHE — Series":
            # Tf1 is computed internally step-by-step in heat flux mode —
            # pull it back for display now that the run has populated it.
            Tf1_arr = simulation.Tf1

    st.success("Simulation complete!")

    supply_and_return = bore_p.get("supply_and_return", "1_2")
    st.session_state.update({
        "T_history":         T_history,
        "simulation":        simulation,
        "model":             model,
        "props_b":           props_b,
        "Tf1_arr":           Tf1_arr,
        "mw_arr":            mw_arr,
        "pipe_type":         pipe_type,
        "supply_and_return": supply_and_return,
        "params": dict(
            n_steps=n_steps, dt=dt,
            m_mesh=ground_p["m_mesh"], n_mesh=ground_p["n_mesh"],
            m_mesh_sup=ground_p["m_mesh_sup"], m_mesh_inf=ground_p["m_mesh_inf"],
            L_sup=ground_p["L_sup"], L_inf=ground_p["L_inf"],
            D0=bore_p["D0"], cp_w=fluid_p["cp_w"], Lbore=bore_p["Lbore"],
            heat_flux=heat_flux_mode, sim_start=env_p.get("sim_start"),
        ),
    })

# =============================================================================
# Results
# =============================================================================

if "T_history" not in st.session_state:
    st.stop()

T_history         = st.session_state["T_history"]
simulation        = st.session_state["simulation"]
model             = st.session_state["model"]
props_b           = st.session_state["props_b"]
Tf1_arr           = st.session_state["Tf1_arr"]
mw_arr            = st.session_state["mw_arr"]
pipe_type_r       = st.session_state["pipe_type"]
supply_and_return = st.session_state["supply_and_return"]
p                 = st.session_state["params"]

n_steps    = p["n_steps"];    dt         = p["dt"]
m_mesh     = p["m_mesh"];     n_mesh     = p["n_mesh"]
m_mesh_sup = p["m_mesh_sup"]; m_mesh_inf = p["m_mesh_inf"]
L_sup      = p["L_sup"];      L_inf      = p["L_inf"]
D0         = p["D0"];         cp_w       = p["cp_w"]

n_bhes  = T_history.shape[1]
nsup    = m_mesh_sup + 1
nground = n_mesh * m_mesh
dz      = model.ground[0].dz
depth   = np.arange(-L_sup, -L_sup - dz * m_mesh, -dz)
time_h  = np.arange(1, n_steps + 1) * dt / 3600

slices = _build_slices(nsup, nground, props_b, m_mesh)

st.divider()
st.header("Results")

show_grout_tab = hasattr(simulation, "bh_p_varprops")

tab_labels = [
    "Ground — Surface",
    "Ground — Middle",
    "Ground — Bottom",
    "Borehole",
    "Time series",
    "Ground Energy",
]
if show_grout_tab:
    tab_labels.append("Grout Properties")

result_tabs = st.tabs(tab_labels)
(res_sup, res_mid, res_bot, res_bore, res_ts, res_energy) = result_tabs[:6]
res_grout = result_tabs[6] if show_grout_tab else None

with res_sup:
    render_ground_surface(T_history, n_bhes, nsup, dt, n_steps, L_sup)

with res_mid:
    render_ground_middle(T_history, n_bhes, nsup, nground, dt, n_steps,
                         depth, n_mesh, m_mesh, model, D0)

with res_bot:
    render_ground_bottom(T_history, n_bhes, nsup, nground, dt, n_steps,
                         depth, m_mesh, m_mesh_inf, dz, props_b)

with res_bore:
    render_borehole(T_history, n_bhes, slices, depth, n_steps, dt,
                    pipe_type_r, supply_and_return, m_mesh)

with res_ts:
    render_timeseries(T_history, simulation, n_bhes, nsup, nground,
                      slices, props_b, Tf1_arr, mw_arr, cp_w, time_h, n_steps, dt)

with res_energy:
    render_ground_energy_balance(
        simulation, p["sim_start"], dt, n_steps, p["heat_flux"],
    )

if show_grout_tab:
    with res_grout:
        render_grout_properties(simulation, time_h, D0, p["Lbore"])

# raw download
st.divider()
buf = io.BytesIO()
np.save(buf, T_history)
st.download_button(
    label="⬇ Download full T_history (.npy)",
    data=buf.getvalue(),
    file_name="T_history.npy",
    mime="application/octet-stream",
)