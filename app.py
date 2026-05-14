# -*- coding: utf-8 -*-
"""
CaRM App — Streamlit interface for BHE/BTES simulation.
"""

import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from carm import (
    BoreholeGeometry,
    BoreholeMesh,
    BoreholeThermalProperties,
    Coaxial,
    DoubleUtube,
    Helical,
    SingleUtube,
)
from carm import EnvironmentalProperties, EnvironmentalTimeSeries
from carm import FieldInput
from carm import Fluid
from carm import GroundGeometry, GroundMesh
from carm import PhysicalModel
from carm import Simulation

# =============================================================================
# Page config
# =============================================================================

st.set_page_config(page_title="CaRM", page_icon="🌡️", layout="wide")
st.title("CaRM — Borehole Heat Exchanger Simulation")

# =============================================================================
# Sidebar: simulation mode
# =============================================================================

st.sidebar.header("Simulation mode")

mode = st.sidebar.radio(
    "Configuration",
    ["Single BHE", "Multi BHE — Parallel", "Multi BHE — Series"],
)

pipe_type = st.sidebar.selectbox(
    "Pipe configuration",
    ["SingleUtube", "DoubleUtube", "Coaxial", "Helical"],
)

# =============================================================================
# Sidebar: file uploads
# =============================================================================

st.sidebar.header("Input files")

env_file = st.sidebar.file_uploader("Environmental data (input_env.xlsx)", type=["xlsx"])

spacing_file = None
if mode in ["Multi BHE — Parallel", "Multi BHE — Series"]:
    spacing_file = st.sidebar.file_uploader("Field layout (spacing.xlsx)", type=["xlsx"])

# =============================================================================
# Main form: tabs
# =============================================================================

tab_ground, tab_borehole, tab_fluid, tab_env, tab_sim = st.tabs(
    ["Ground", "Borehole", "Fluid", "Environment", "Simulation"]
)

# -----------------------------------------------------------------------------
# Tab: Ground
# -----------------------------------------------------------------------------

with tab_ground:
    st.subheader("Ground geometry & mesh")
    col1, col2 = st.columns(2)
    with col1:
        Tg      = st.number_input("Undisturbed ground temperature Tg [°C]", value=13.0)
        L       = st.number_input("Borehole active length L [m]", value=100.0)
        L_sup   = st.number_input("Surface layer thickness L_sup [m]", value=1.0)
        L_inf   = st.number_input("Bottom layer thickness L_inf [m]", value=10.0)
        rn      = st.number_input("Far-field radius rn [m]", value=10.0,
                                   help="Leave at 0 to auto-compute for multi-BHE fields",
                                   min_value=0.0)
    with col2:
        n_mesh      = st.number_input("Radial mesh cells n_mesh [-]", value=20, min_value=1)
        m_mesh      = st.number_input("Axial mesh cells m_mesh [-]", value=40, min_value=1)
        m_mesh_sup  = st.number_input("Axial cells surface layer m_mesh_sup [-]", value=4, min_value=1)
        m_mesh_inf  = st.number_input("Axial cells bottom layer m_mesh_inf [-]", value=40, min_value=1)

    st.subheader("Ground stratification")
    st.caption("Each row: (k [W/m·K], cp [J/kg·K], rho [kg/m³], thickness [m])")
    n_layers = st.number_input("Number of layers", value=1, min_value=1, max_value=10)
    stratification = []
    for i in range(n_layers):
        c1, c2, c3, c4 = st.columns(4)
        k_s   = c1.number_input(f"k layer {i+1}",   value=1.8,    key=f"k_{i}")
        cp_s  = c2.number_input(f"cp layer {i+1}",  value=947.37, key=f"cp_{i}")
        rho_s = c3.number_input(f"rho layer {i+1}", value=1900.0, key=f"rho_{i}")
        th_s  = c4.number_input(f"thick layer {i+1}", value=111.0, key=f"th_{i}")
        stratification.append((k_s, cp_s, rho_s, th_s))

# -----------------------------------------------------------------------------
# Tab: Borehole
# -----------------------------------------------------------------------------

with tab_borehole:
    st.subheader("Borehole geometry & grout")
    col1, col2 = st.columns(2)
    with col1:
        Lbore   = st.number_input("Borehole length Lbore [m]", value=100.0)
        D0      = st.number_input("Borehole diameter D0 [m]", value=0.15)
        cp_0    = st.number_input("Grout specific heat cp_0 [J/kg·K]", value=1460.0)
        rho_0   = st.number_input("Grout density rho_0 [kg/m³]", value=1655.0)
        k0      = st.number_input("Grout thermal conductivity k0 [W/m·K]", value=1.8)

    st.subheader(f"Pipe parameters — {pipe_type}")

    if pipe_type == "SingleUtube":
        col1, col2 = st.columns(2)
        with col1:
            Dpi         = st.number_input("Inner pipe diameter Dpi [m]", value=0.026)
            pipe_thick  = st.number_input("Pipe wall thickness [m]", value=0.003)
            pipe_spacing= st.number_input("Pipe spacing [m]", value=0.0823)
        with col2:
            Rp0         = st.number_input("Pipe-grout resistance Rp0 [K·m/W]", value=0.25)
            RppB        = st.number_input("Pipe-pipe resistance RppB [K·m/W]", value=0.72)
            n_pipes     = st.number_input("Number of pipes n_pipes", value=2, min_value=2)

    elif pipe_type == "DoubleUtube":
        col1, col2 = st.columns(2)
        with col1:
            Dpi         = st.number_input("Inner pipe diameter Dpi [m]", value=0.026)
            pipe_thick  = st.number_input("Pipe wall thickness [m]", value=0.003)
            pipe_spacing= st.number_input("Pipe spacing [m]", value=0.0823)
        with col2:
            Rp0         = st.number_input("Pipe-grout resistance Rp0 [K·m/W]", value=0.25)
            RppB        = st.number_input("Pipe-pipe resistance RppB [K·m/W]", value=0.72)
            RppA        = st.number_input("Pipe-pipe resistance RppA [K·m/W]", value=0.55)
            n_pipes     = st.number_input("Number of pipes n_pipes", value=4, min_value=4)
            connection  = st.selectbox("Connection", ["P", "S"])

    elif pipe_type == "Coaxial":
        col1, col2 = st.columns(2)
        with col1:
            Dp1i        = st.number_input("Inner pipe inner diameter Dp1i [m]", value=0.032)
            Dp2i        = st.number_input("Outer pipe inner diameter Dp2i [m]", value=0.110)
            pipe1_thick = st.number_input("Inner pipe wall thickness [m]", value=0.003)
            pipe2_thick = st.number_input("Outer pipe wall thickness [m]", value=0.006)
        with col2:
            k_pipe      = st.number_input("Pipe thermal conductivity k_pipe [W/m·K]", value=0.38)
            supply_and_return = st.selectbox("Supply/return", ["1_2", "2_1"],
                                              help="1_2: supply in inner pipe; 2_1: supply in annulus")

    elif pipe_type == "Helical":
        col1, col2 = st.columns(2)
        with col1:
            Dpi1        = st.number_input("Pipe 1 inner diameter Dpi1 [m]", value=0.0204)
            Dpi2        = st.number_input("Pipe 2 inner diameter Dpi2 [m]", value=0.0204)
            pipe_thick  = st.number_input("Pipe wall thickness [m]", value=0.0023)
            k_pipe      = st.number_input("Pipe thermal conductivity k_pipe [W/m·K]", value=0.38)
        with col2:
            rih         = st.number_input("Helix inner radius rih [m]", value=0.045)
            N           = st.number_input("Number of turns N [-]", value=8, min_value=1)
            P           = st.number_input("Helix pitch P [m]", value=1.5)
            Lp2tot      = st.number_input("Total length outer pipe Lp2tot [m]", value=12.0)
            supply_and_return = st.selectbox("Supply/return", ["1_2", "2_1"])

# -----------------------------------------------------------------------------
# Tab: Fluid
# -----------------------------------------------------------------------------

with tab_fluid:
    st.subheader("Fluid thermal properties")
    col1, col2 = st.columns(2)
    with col1:
        k_w   = st.number_input("Thermal conductivity k_w [W/m·K]", value=0.5687)
        rho_w = st.number_input("Density rho_w [kg/m³]", value=1000.14)
    with col2:
        cp_w  = st.number_input("Specific heat cp_w [J/kg·K]", value=4207.4)
        ni_w  = st.number_input("Kinematic viscosity ni_w [m²/s]", value=1.496e-6, format="%.3e")

# -----------------------------------------------------------------------------
# Tab: Environment
# -----------------------------------------------------------------------------

with tab_env:
    st.subheader("Environmental properties")
    col1, col2 = st.columns(2)
    with col1:
        Tm          = st.number_input("Mean annual air temperature Tm [°C]", value=13.0)
        R_ext       = st.number_input("External thermal resistance R_ext [m²·K/W]", value=0.04)
        absorptance = st.number_input("Surface absorptance [-]", value=0.7, min_value=0.0, max_value=1.0)
        eps         = st.number_input("Surface emittance [-]", value=0.95, min_value=0.0, max_value=1.0)
    with col2:
        At          = st.number_input("Annual temperature amplitude At [K]", value=10.0)
        tau_y       = st.number_input("Year duration tau_y [s]", value=365 * 24 * 3600)
        tau_shift   = st.number_input("Temperature phase shift tau_shift [s]", value=210 * 24 * 3600)

# -----------------------------------------------------------------------------
# Tab: Simulation
# -----------------------------------------------------------------------------

with tab_sim:
    st.subheader("Simulation parameters")
    col1, col2 = st.columns(2)
    with col1:
        dt      = st.number_input("Time step dt [s]", value=3600)
        n_steps = st.number_input("Number of steps n_steps [-]", value=276, min_value=1)
        Tf1_val = st.number_input("Inlet fluid temperature Tf1 [°C]", value=2.0)
        mw_val  = st.number_input("Mass flow rate mw_tot [kg/s]", value=0.1657)

    if mode == "Multi BHE — Series":
        st.subheader("Series groups")
        st.caption("Define each group as a comma-separated list of borehole IDs (0-indexed)")
        n_bhes   = st.number_input("Total number of BHEs", value=9, min_value=1)
        n_groups = st.number_input("Number of series groups", value=3, min_value=1)
        groups = {}
        for g in range(n_groups):
            raw = st.text_input(f"Group {g} borehole IDs", value=", ".join(str(x) for x in range(g*3, g*3+3)), key=f"grp_{g}")
            groups[f"group_{g}"] = [int(x.strip()) for x in raw.split(",")]
    elif mode == "Multi BHE — Parallel":
        n_bhes = st.number_input("Total number of BHEs", value=9, min_value=1)
        col1, col2 = st.columns(2)
        with col1:
            x_min = st.number_input("Field x_min [m]", value=-2.5)
            y_min = st.number_input("Field y_min [m]", value=-2.5)
        with col2:
            x_max = st.number_input("Field x_max [m]", value=12.5)
            y_max = st.number_input("Field y_max [m]", value=12.5)

# =============================================================================
# Run button
# =============================================================================

st.divider()
run = st.button("▶ Run simulation", type="primary", use_container_width=True)

if run:

    # --- validate uploads ---
    if env_file is None:
        st.error("Please upload the environmental data file (input_env.xlsx).")
        st.stop()

    if mode in ["Multi BHE — Parallel", "Multi BHE — Series"] and spacing_file is None:
        st.error("Please upload the field layout file (spacing.xlsx).")
        st.stop()

    with st.spinner("Running CaRM simulation..."):

        # --- save uploads to temp files ---
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            f.write(env_file.read())
            env_path = Path(f.name)

        # --- build objects ---
        fluid = Fluid(k_w=k_w, rho_w=rho_w, cp_w=cp_w, ni_w=ni_w)

        bore_geom      = BoreholeGeometry(Lbore=Lbore, D0=D0)
        bore_mesh      = BoreholeMesh(m_mesh=m_mesh)
        bore_th_props  = BoreholeThermalProperties(cp_0=cp_0, rho_0=rho_0, k0=k0)

        if pipe_type == "SingleUtube":
            props_b = SingleUtube(
                geom=bore_geom, mesh=bore_mesh, thermalprops=bore_th_props, fluid=fluid,
                Rp0=Rp0, RppB=RppB, pipe_spacing=pipe_spacing,
                pipe_thick=pipe_thick, Dpi=Dpi, n_pipes=n_pipes,
            )
        elif pipe_type == "DoubleUtube":
            props_b = DoubleUtube(
                geom=bore_geom, mesh=bore_mesh, thermalprops=bore_th_props, fluid=fluid,
                Rp0=Rp0, RppB=RppB, RppA=RppA, pipe_spacing=pipe_spacing,
                pipe_thick=pipe_thick, Dpi=Dpi, n_pipes=n_pipes, connection=connection,
            )
        elif pipe_type == "Coaxial":
            props_b = Coaxial(
                geom=bore_geom, mesh=bore_mesh, thermalprops=bore_th_props, fluid=fluid,
                supply_and_return=supply_and_return,
                Dp1i=Dp1i, Dp2i=Dp2i,
                pipe1_thick=pipe1_thick, pipe2_thick=pipe2_thick,
                k_pipe1=k_pipe, k_pipe2=k_pipe,
            )
        elif pipe_type == "Helical":
            props_b = Helical(
                geom=bore_geom, mesh=bore_mesh, thermalprops=bore_th_props, fluid=fluid,
                Dpi1=Dpi1, Dpi2=Dpi2, P=P, Lp2tot=Lp2tot,
                supply_and_return=supply_and_return,
                rih=rih, pipe_thick=pipe_thick, N=N, k_pipe=k_pipe,
            )

        rn_val = rn if (mode == "Single BHE" and rn > 0) else None
        ground_geom = GroundGeometry(rn=rn_val, D0=D0, L=L, L_sup=L_sup, L_inf=L_inf)
        ground_mesh = GroundMesh(
            n_mesh=n_mesh, m_mesh=m_mesh,
            m_mesh_sup=m_mesh_sup, m_mesh_inf=m_mesh_inf,
        )

        env_input = EnvironmentalTimeSeries.from_excel(Tm=Tm, path=env_path)
        env_props = EnvironmentalProperties(
            R_ext=R_ext, absorptance=absorptance, eps=eps,
            At=At, tau=0, tau_y=tau_y, tau_shift=tau_shift,
        )

        # --- field (multi only) ---
        if mode == "Multi BHE — Parallel":
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
                f.write(spacing_file.read())
                field_path = Path(f.name)
            myfield = FieldInput(n_bhes=n_bhes, xmin=x_min, ymin=y_min, xmax=x_max, ymax=y_max, rb=D0/2)
            myfield.from_excel(field_path)
        elif mode == "Multi BHE — Series":
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
                f.write(spacing_file.read())
                field_path = Path(f.name)
            myfield = FieldInput(n_bhes=n_bhes, xmin=x_min, ymin=y_min, xmax=x_max, ymax=y_max, rb=D0/2, layout="irregular")
            myfield.from_excel(field_path)

        model_kwargs = dict(
            ground_geom=ground_geom, ground_mesh=ground_mesh,
            borehole=props_b, fluid=fluid, Tg=Tg, stratification=stratification,
        )
        if mode != "Single BHE":
            model_kwargs["fieldinput"] = myfield

        model = PhysicalModel(**model_kwargs)

        # --- arrays ---
        if mode == "Single BHE":
            n_inlets = 1
        elif mode == "Multi BHE — Parallel":
            n_inlets = n_bhes
        else:
            n_inlets = n_groups

        Tf1_arr   = np.full((n_inlets, n_steps), Tf1_val, dtype=np.float64)
        mw_arr    = np.full((n_inlets, n_steps), mw_val, dtype=np.float64)

        sim_kwargs = dict(
            model=model, envinput=env_input, timesteps=dt, n_steps=n_steps,
            envprops=env_props, mw_tot=mw_arr, Tf1=Tf1_arr,
        )
        if mode == "Multi BHE — Series":
            sim_kwargs["groups"] = groups

        simulation = Simulation(**sim_kwargs)

        if mode == "Multi BHE — Parallel":
            T_history = simulation.run(parallel=True)
        elif mode == "Multi BHE — Series":
            T_history = simulation.run(series=True)
        else:
            T_history = simulation.run()

    st.success("Simulation complete!")

    # =========================================================================
    # Post-processing & plots
    # =========================================================================

    nsup    = m_mesh_sup + 1
    nground = n_mesh * m_mesh
    ref_bhe = 0

    time  = np.arange(dt, dt * (n_steps + 1), dt, dtype=np.float64)
    dz    = model.ground[0].dz
    depth = np.arange(-L_sup, -L_sup - dz * m_mesh, -dz)

    slice_shell = [nsup + nground + j * props_b.n_equations for j in range(m_mesh)]
    slice_down  = [nsup + nground + j * props_b.n_equations + (props_b.n_equations - 2) for j in range(m_mesh)]
    slice_up    = [nsup + nground + j * props_b.n_equations + (props_b.n_equations - 1) for j in range(m_mesh)]

    Tfout = T_history[1:, ref_bhe, nsup + nground + (props_b.n_equations - 1)]

    # --- Plot 1: outlet fluid temperature ---
    st.subheader("Outlet fluid temperature")
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(time / 3600, Tfout, color="tab:red", label=r"$T_{f,out}$")
    ax.axhline(Tf1_val, color="tab:blue", linestyle="--", label=r"$T_{f,in}$")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel("Temperature [°C]")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # --- Plot 2: shell temperature vertical profile ---
    steps_plot = [max(1, n_steps // 4), n_steps // 2, n_steps]
    steps_plot = sorted(set(min(s, n_steps) for s in steps_plot))

    st.subheader("Shell temperature — vertical profile")
    fig, ax = plt.subplots(figsize=(4, 4))
    for s in steps_plot:
        ax.plot(T_history[s, ref_bhe, slice_shell], depth, label=f"Step {s}")
    ax.set_xlabel("Temperature [°C]")
    ax.set_ylabel("Depth [m]")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # --- Plot 3: ground temperature heatmap ---
    st.subheader("Ground temperature heatmap")
    r0     = model.ground[0].r0
    rn_out = model.ground[0].rn
    radius = np.linspace(D0 / 2, rn_out, n_mesh)
    R, D   = np.meshgrid(radius, depth)

    fig, axes = plt.subplots(1, len(steps_plot), figsize=(5 * len(steps_plot), 4))
    if len(steps_plot) == 1:
        axes = [axes]
    T_all = np.array([
        T_history[s, ref_bhe, nsup: nsup + nground].reshape(m_mesh, n_mesh)
        for s in steps_plot
    ])
    vmin, vmax = T_all.min(), T_all.max()
    for i, (s, ax) in enumerate(zip(steps_plot, axes)):
        pc = ax.pcolormesh(R, D, T_all[i], cmap="RdYlGn_r", shading="gouraud", vmin=vmin, vmax=vmax)
        fig.colorbar(pc, ax=ax, label="Temperature [°C]")
        ax.set_xlabel("Radius [m]")
        ax.set_ylabel("Depth [m]")
        ax.set_title(f"Step {s}")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # --- Raw data download ---
    st.subheader("Download results")
    import io
    buf = io.BytesIO()
    np.save(buf, T_history)
    st.download_button(
        label="Download T_history (.npy)",
        data=buf.getvalue(),
        file_name="T_history.npy",
        mime="application/octet-stream",
    )