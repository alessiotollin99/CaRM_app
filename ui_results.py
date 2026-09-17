# -*- coding: utf-8 -*-
"""
Results rendering: tables and interactive Plotly plots for CaRM App.
"""

import io

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Shared Plotly theme
# ─────────────────────────────────────────────────────────────────────────────

LAYOUT = dict(
    template="plotly_white",
    font=dict(family="sans-serif", size=12),
    margin=dict(t=40, b=60, l=60, r=20),
)


def _depth_yaxis(z_bottom: float) -> dict:
    """Y-axis with 0 at top and z_bottom (negative) at bottom."""
    return dict(range=[z_bottom, 0], title="Depth [m]")


# ─────────────────────────────────────────────────────────────────────────────
# Download helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=True).encode()


def _to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=True)
    return buf.getvalue()


def _download_row(df: pd.DataFrame, label: str, fname: str):
    c1, c2 = st.columns(2)
    c1.download_button(
        f"⬇ {label} — CSV", _to_csv(df), f"{fname}.csv",
        mime="text/csv", key=f"csv_{fname}",
    )
    c2.download_button(
        f"⬇ {label} — Excel", _to_excel_bytes(df), f"{fname}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"xlsx_{fname}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Index helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_slices(nsup, nground, props_b, m_mesh):
    n_eq = props_b.n_equations
    slices = {}
    # shell (first node of each borehole block)
    slices["shell"] = [nsup + nground + j * n_eq for j in range(m_mesh)]
    # fluid down / up (last two nodes)
    slices["fluid_down"] = [nsup + nground + j * n_eq + (n_eq - 2) for j in range(m_mesh)]
    slices["fluid_up"]   = [nsup + nground + j * n_eq + (n_eq - 1) for j in range(m_mesh)]
    # core: second node (index 1) if n_eq > 3, else same as shell
    if n_eq > 3:
        slices["core"] = [nsup + nground + j * n_eq + 1 for j in range(m_mesh)]
    else:
        slices["core"] = slices["shell"]
    return slices


def _quantity_labels(pipe_type: str, supply_and_return: str = "1_2") -> dict:
    """
    Return display name → slice key mapping for borehole quantities,
    adapted per pipe type and flow direction.
    """
    if pipe_type == "SingleUtube":
        return {
            "Shell (borehole wall)": "shell",
            "Core (grout)":          "core",
            "Fluid down":            "fluid_down",
            "Fluid up":              "fluid_up",
        }
    elif pipe_type == "DoubleUtube":
        return {
            "Shell (borehole wall)": "shell",
            "Core (grout)":          "core",
            "Fluid 1 down":          "fluid_down",
            "Fluid 1 up":            "fluid_up",
        }
    elif pipe_type == "Coaxial":
        if supply_and_return == "1_2":
            return {
                "Shell (borehole wall)": "shell",
                "Core (grout)":          "core",
                "Fluid — inner (supply)": "fluid_down",
                "Fluid — annulus (return)": "fluid_up",
            }
        else:
            return {
                "Shell (borehole wall)": "shell",
                "Core (grout)":          "core",
                "Fluid — annulus (supply)": "fluid_down",
                "Fluid — inner (return)":   "fluid_up",
            }
    elif pipe_type == "Helical":
        if supply_and_return == "1_2":
            return {
                "Shell (borehole wall)": "shell",
                "Core (grout)":          "core",
                "Fluid — straight (supply)": "fluid_down",
                "Fluid — helical (return)":  "fluid_up",
            }
        else:
            return {
                "Shell (borehole wall)": "shell",
                "Core (grout)":          "core",
                "Fluid — helical (supply)":  "fluid_down",
                "Fluid — straight (return)": "fluid_up",
            }
    return {"Shell": "shell", "Fluid down": "fluid_down", "Fluid up": "fluid_up"}


# ─────────────────────────────────────────────────────────────────────────────
# SUB-TAB: Ground — Surface
# ─────────────────────────────────────────────────────────────────────────────

def render_ground_surface(T_history, n_bhes, nsup, dt, n_steps, L_sup):
    st.subheader("Surface ground layer [°C]")
    all_steps = list(range(1, n_steps + 1))
    defaults  = sorted({1, n_steps//4, n_steps//2, 3*n_steps//4, n_steps})
    sel_steps = st.multiselect("Timesteps", all_steps,
                               default=[s for s in defaults if s <= n_steps],
                               key="sup_steps")
    bhe_sup = st.selectbox("BHE", list(range(n_bhes)), key="sup_bhe") if n_bhes > 1 else 0

    if not sel_steps:
        return

    sup_depths = np.linspace(0, -L_sup, nsup)
    df = pd.DataFrame(
        {f"step {s} ({s*dt/3600:.0f} h)": T_history[s, bhe_sup, :nsup]
         for s in sel_steps},
        index=[f"{d:.3f}" for d in sup_depths],
    )
    df.index.name = "depth [m]"

    fig = go.Figure()
    for s in sel_steps:
        fig.add_trace(go.Scatter(
            x=T_history[s, bhe_sup, :nsup], y=sup_depths,
            mode="lines+markers", name=f"step {s} ({s*dt/3600:.0f} h)",
            hovertemplate="T = %{x:.3f} °C<br>z = %{y:.3f} m<extra></extra>",
        ))
    fig.update_layout(**LAYOUT, xaxis_title="Temperature [°C]",
                      yaxis=_depth_yaxis(-L_sup), height=420,
                      legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True)
    _download_row(df, "Ground Surface", f"ground_surface_bhe{bhe_sup}")


# ─────────────────────────────────────────────────────────────────────────────
# SUB-TAB: Ground — Middle
# ─────────────────────────────────────────────────────────────────────────────

def render_ground_middle(T_history, n_bhes, nsup, nground, dt, n_steps,
                         depth, n_mesh, m_mesh, model, D0):
    st.subheader("Middle ground layer [°C]")
    st.caption("Smooth contour map — depth vs radius. vmin/vmax fixed across all timesteps.")

    col1, col2 = st.columns([3, 1])
    step_mid = col1.slider("Timestep", 1, n_steps, n_steps // 2, key="mid_step")
    bhe_mid  = col2.selectbox("BHE", list(range(n_bhes)), key="mid_bhe") if n_bhes > 1 else 0

    # global colour range: all timesteps, this BHE
    T_all = T_history[1:, bhe_mid, nsup: nsup + nground].reshape(n_steps, m_mesh, n_mesh)
    vmin  = float(T_all.min())
    vmax  = float(T_all.max())

    r0_val = model.ground[0].r0        # = D0 / 2
    rn_val = model.ground[bhe_mid].rn
    radius = np.linspace(r0_val, rn_val, n_mesh)

    T_mid = T_history[step_mid, bhe_mid, nsup: nsup + nground].reshape(m_mesh, n_mesh)

    # depth domain: from -L_sup to -L_sup-Lbore (depth array already correct)
    z_top    = float(depth[0])   # e.g. -L_sup
    z_bottom = float(depth[-1])  # e.g. -L_sup - Lbore

    fig = go.Figure(go.Contour(
        z=T_mid, x=np.round(radius, 4), y=np.round(depth, 4),
        colorscale="RdYlGn_r",
        zmin=vmin, zmax=vmax,
        contours=dict(
            coloring="heatmap",
            showlabels=True,
            labelfont=dict(size=9, color="black"),
        ),
        colorbar=dict(title="T [°C]", thickness=15),
        hovertemplate="r = %{x:.4f} m<br>z = %{y:.3f} m<br>T = %{z:.3f} °C<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT,
        xaxis=dict(title="Radius [m]", range=[float(radius[0]), float(radius[-1])]),
        yaxis=dict(title="Depth [m]",  range=[z_bottom, z_top]),
        height=700,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Colour scale fixed: vmin = {vmin:.2f} °C, vmax = {vmax:.2f} °C")

    df = pd.DataFrame(
        T_mid,
        index=[f"{d:.3f}" for d in depth],
        columns=[f"{r:.4f}" for r in radius],
    )
    df.index.name = "depth [m]"
    df.columns.name = "radius [m]"
    st.dataframe(df, use_container_width=True)
    _download_row(df, "Ground Middle", f"ground_middle_bhe{bhe_mid}_step{step_mid}")


# ─────────────────────────────────────────────────────────────────────────────
# SUB-TAB: Ground — Bottom
# ─────────────────────────────────────────────────────────────────────────────

def render_ground_bottom(T_history, n_bhes, nsup, nground, dt, n_steps,
                         depth, m_mesh, m_mesh_inf, dz, props_b):
    st.subheader("Bottom ground layer [°C]")
    all_steps = list(range(1, n_steps + 1))
    defaults  = sorted({1, n_steps//4, n_steps//2, 3*n_steps//4, n_steps})
    sel_steps = st.multiselect("Timesteps", all_steps,
                               default=[s for s in defaults if s <= n_steps],
                               key="bot_steps")
    bhe_bot = st.selectbox("BHE", list(range(n_bhes)), key="bot_bhe") if n_bhes > 1 else 0

    if not sel_steps:
        return

    bot_start  = nsup + nground + m_mesh * props_b.n_equations
    bot_depths = np.linspace(depth[-1] - dz, depth[-1] - dz * m_mesh_inf, m_mesh_inf)

    df = pd.DataFrame(
        {f"step {s} ({s*dt/3600:.0f} h)":
         T_history[s, bhe_bot, bot_start: bot_start + m_mesh_inf]
         for s in sel_steps},
        index=[f"{d:.3f}" for d in bot_depths],
    )
    df.index.name = "depth [m]"

    fig = go.Figure()
    for s in sel_steps:
        fig.add_trace(go.Scatter(
            x=T_history[s, bhe_bot, bot_start: bot_start + m_mesh_inf],
            y=bot_depths,
            mode="lines+markers", name=f"step {s} ({s*dt/3600:.0f} h)",
            hovertemplate="T = %{x:.3f} °C<br>z = %{y:.3f} m<extra></extra>",
        ))
    fig.update_layout(**LAYOUT, xaxis_title="Temperature [°C]",
                      yaxis=_depth_yaxis(bot_depths[-1]), height=420,
                      legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True)
    _download_row(df, "Ground Bottom", f"ground_bottom_bhe{bhe_bot}")


# ─────────────────────────────────────────────────────────────────────────────
# SUB-TAB: Borehole
# ─────────────────────────────────────────────────────────────────────────────

def render_borehole(T_history, n_bhes, slices, depth, n_steps, dt,
                    pipe_type, supply_and_return, m_mesh):
    st.subheader("Borehole temperatures [°C]")
    st.caption("Select which quantities to overlay. Y-axis adapts automatically.")

    col1, col2 = st.columns(2)
    step_bore = col1.slider("Timestep", 1, n_steps, n_steps // 2, key="bore_step")
    bhe_bore  = col2.selectbox("BHE", list(range(n_bhes)), key="bore_bhe") if n_bhes > 1 else 0

    qty_map  = _quantity_labels(pipe_type, supply_and_return)
    selected = st.multiselect(
        "Quantities to plot",
        list(qty_map.keys()),
        default=list(qty_map.keys()),
        key="bore_qty",
    )

    if not selected:
        st.info("Select at least one quantity.")
        return

    fig = go.Figure()
    df_data = {}
    for label in selected:
        sl_key = qty_map[label]
        vals   = T_history[step_bore, bhe_bore, slices[sl_key]]
        fig.add_trace(go.Scatter(
            x=vals, y=depth, mode="lines+markers", name=label,
            marker=dict(size=5),
            hovertemplate=f"{label} = %{{x:.3f}} °C<br>z = %{{y:.3f}} m<extra></extra>",
        ))
        df_data[f"{label} [°C]"] = vals

    # auto y-range: full domain, 0 at top
    fig.update_layout(
        **LAYOUT,
        xaxis_title="Temperature [°C]",
        yaxis=_depth_yaxis(depth[-1]),
        height=540,
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig, use_container_width=True)

    df = pd.DataFrame(df_data, index=[f"{d:.3f}" for d in depth])
    df.index.name = "depth [m]"
    st.dataframe(df, use_container_width=True)
    _download_row(df, "Borehole", f"borehole_bhe{bhe_bore}_step{step_bore}")


# ─────────────────────────────────────────────────────────────────────────────
# SUB-TAB: Time series
# ─────────────────────────────────────────────────────────────────────────────

def render_timeseries(T_history, simulation, n_bhes, nsup, nground,
                      slices, props_b, Tf1_arr, mw_arr, cp_w, time_h, n_steps, dt):
    st.subheader("Time series")
    bhe_ts = st.selectbox("BHE", list(range(n_bhes)), key="ts_bhe") if n_bhes > 1 else 0

    Tfout = T_history[1:, bhe_ts, nsup + nground + (props_b.n_equations - 1)]
    Tfin  = Tf1_arr[bhe_ts if Tf1_arr.shape[0] > bhe_ts else 0, :]
    mw_ts = mw_arr[bhe_ts if mw_arr.shape[0] > bhe_ts else 0, :]
    q_ts  = np.where(mw_ts != 0, mw_ts * cp_w * (Tfin - Tfout), 0.0)

    T_shell_mean = T_history[1:, bhe_ts, slices["shell"]].mean(axis=1)
    T_bc_mean    = simulation.T_bc[:, bhe_ts, :].mean(axis=1)

    # temperatures
    fig_T = go.Figure()
    for label, arr, dash in [
        ("Tf_in",         Tfin,         "solid"),
        ("Tf_out",        Tfout,        "solid"),
        ("T_shell_mean",  T_shell_mean, "dot"),
        ("T_bc_mean",     T_bc_mean,    "dash"),
    ]:
        fig_T.add_trace(go.Scatter(
            x=time_h, y=arr, mode="lines", name=label,
            line=dict(dash=dash),
            hovertemplate=f"{label} = %{{y:.3f}} °C  t = %{{x:.1f}} h<extra></extra>",
        ))
    fig_T.update_layout(**LAYOUT, xaxis_title="Time [h]",
                        yaxis_title="Temperature [°C]", height=360,
                        legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig_T, use_container_width=True)

    # heat flux
    fig_q = go.Figure(go.Scatter(
        x=time_h, y=q_ts, mode="lines", name="q [W]",
        line=dict(color="tomato"),
        hovertemplate="q = %{y:.1f} W  t = %{x:.1f} h<extra></extra>",
    ))
    fig_q.update_layout(**LAYOUT, xaxis_title="Time [h]",
                        yaxis_title="Heat extracted [W]", height=300)
    st.plotly_chart(fig_q, use_container_width=True)

    df = pd.DataFrame({
        "Tf_in [°C]":        Tfin,
        "Tf_out [°C]":       Tfout,
        "q [W]":             q_ts,
        "T_shell_mean [°C]": T_shell_mean,
        "T_bc_mean [°C]":    T_bc_mean,
    }, index=time_h)
    df.index.name = "time [h]"
    st.dataframe(df, use_container_width=True)
    _download_row(df, "Time series", f"timeseries_bhe{bhe_ts}")


# ─────────────────────────────────────────────────────────────────────────────
# SUB-TAB: Ground Energy
# ─────────────────────────────────────────────────────────────────────────────

def render_ground_energy_balance(simulation, sim_start, dt, n_steps, heat_flux: bool):
    """
    Monthly ground energy balance, for both simulation modes.

    heat_flux mode: the ground-side load already accounts for the heat pump
    (COP/EER) via ``simulation.Q_ground`` [W] — steps where the building load
    was zero leave it at NaN, treated here as zero exchange.

    Standard mode: no such quantity exists, so it is derived the same way
    the solver itself derives it internally — m·cp·(Tf1 − Tfout_prev), i.e.
    ``simulation.q_nbhes`` [W] summed over all boreholes.

    Convention: positive = heat extracted from the ground (heating);
    negative = heat injected into the ground (cooling).
    """
    st.subheader("Monthly ground energy balance")
    st.caption(
        "Energy exchanged with the ground, aggregated by month. Positive = "
        "extracted from the ground (heating); negative = injected into the "
        "ground (cooling)."
    )

    if heat_flux:
        q_ground_w = np.nan_to_num(simulation.Q_ground, nan=0.0)
    else:
        q_ground_w = simulation.q_nbhes.sum(axis=1)

    extraction_w = -q_ground_w  # flip sign to the "extraction positive" convention
    energy_kwh = extraction_w * dt / 3.6e6

    if sim_start is None:
        st.info("No simulation start date available — showing energy per step instead of per month.")
        df = pd.DataFrame({"energy [kWh]": energy_kwh})
        df.index.name = "step"
    else:
        dates = pd.Timestamp(sim_start) + pd.to_timedelta(np.arange(n_steps) * dt, unit="s")
        df = pd.DataFrame({"energy [kWh]": energy_kwh}, index=dates)
        df = df.resample("MS").sum()
        df.index.name = "month"

    colors = ["seagreen" if v >= 0 else "indianred" for v in df["energy [kWh]"]]
    fig = go.Figure(go.Bar(x=df.index, y=df["energy [kWh]"], marker_color=colors))
    fig.update_layout(**LAYOUT, xaxis_title="Month" if sim_start is not None else "Step",
                      yaxis_title="Energy [kWh]", height=380)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    c1.metric("Total extracted [kWh]", f"{df['energy [kWh]'].clip(lower=0).sum():,.0f}")
    c2.metric("Total injected [kWh]", f"{-df['energy [kWh]'].clip(upper=0).sum():,.0f}")

    st.dataframe(df, use_container_width=True)
    _download_row(df, "Monthly ground energy", "monthly_ground_energy")


# ─────────────────────────────────────────────────────────────────────────────
# SUB-TAB: Grout Properties
# ─────────────────────────────────────────────────────────────────────────────

def _irrigation_windows(active_mask: np.ndarray) -> list:
    """Contiguous (start_idx, end_idx) runs where active_mask is True."""
    windows = []
    start = None
    for i, active in enumerate(active_mask):
        if active and start is None:
            start = i
        elif not active and start is not None:
            windows.append((start, i - 1))
            start = None
    if start is not None:
        windows.append((start, len(active_mask) - 1))
    return windows


def _shade_windows(fig: go.Figure, time_h: np.ndarray, windows: list) -> None:
    for i0, i1 in windows:
        fig.add_vrect(
            x0=time_h[i0], x1=time_h[i1],
            fillcolor="lightblue", opacity=0.15, layer="below", line_width=0,
        )


def render_grout_properties(simulation, time_h, D0, Lbore):
    st.subheader("Variable grout properties — soil moisture")
    st.caption(
        "Grout thermal conductivity, heat capacity, and density evolve with "
        "the soil moisture content, driven by irrigation (shaded bands) and "
        "gravity drainage/evaporation."
    )

    varprops = simulation.bh_p_varprops
    V     = np.pi * (D0 ** 2) / 4.0 * Lbore
    theta = simulation.wc_history_borehole / V
    water_input = np.asarray(varprops.water_input)[: len(time_h)]

    windows = _irrigation_windows(water_input > 0)

    # k / cp / rho evolution
    col1, col2, col3 = st.columns(3)
    specs = [
        (col1, "Thermal conductivity k", simulation.k_borehole_history, "W/(m K)", "royalblue"),
        (col2, "Heat capacity cp",       simulation.cp_borehole_history, "J/(kg K)", "seagreen"),
        (col3, "Density ρ",              simulation.rho_borehole_history, "kg/m³", "darkorange"),
    ]
    for col, label, arr, unit, color in specs:
        fig = go.Figure(go.Scatter(
            x=time_h, y=arr, mode="lines", line=dict(color=color),
            hovertemplate=f"{label} = %{{y:.4g}} {unit}<br>t = %{{x:.1f}} h<extra></extra>",
        ))
        _shade_windows(fig, time_h, windows)
        fig.update_layout(**LAYOUT, xaxis_title="Time [h]",
                          yaxis_title=f"{label} [{unit}]", height=320)
        col.plotly_chart(fig, use_container_width=True)

    # volumetric water content, with residual/saturated bounds
    st.markdown("**Volumetric water content**")
    fig_theta = go.Figure()
    fig_theta.add_trace(go.Scatter(
        x=time_h, y=theta, mode="lines", name="θ", line=dict(color="teal"),
        hovertemplate="θ = %{y:.4f}<br>t = %{x:.1f} h<extra></extra>",
    ))
    fig_theta.add_hline(y=varprops.theta_r_loc, line_dash="dash", line_color="gray",
                        annotation_text="θr (residual)", annotation_position="bottom right")
    fig_theta.add_hline(y=varprops.theta_s_loc, line_dash="dash", line_color="gray",
                        annotation_text="θs (saturated)", annotation_position="top right")
    _shade_windows(fig_theta, time_h, windows)
    fig_theta.update_layout(**LAYOUT, xaxis_title="Time [h]", yaxis_title="θ [-]", height=340)
    st.plotly_chart(fig_theta, use_container_width=True)

    # irrigation input
    st.markdown("**Irrigation input**")
    fig_irr = go.Figure(go.Scatter(
        x=time_h, y=water_input, mode="lines", fill="tozeroy",
        line=dict(color="dodgerblue"),
        hovertemplate="water_input = %{y:.3e} m/s<br>t = %{x:.1f} h<extra></extra>",
    ))
    _shade_windows(fig_irr, time_h, windows)
    fig_irr.update_layout(**LAYOUT, xaxis_title="Time [h]",
                          yaxis_title="water_input [m/s]", height=260)
    st.plotly_chart(fig_irr, use_container_width=True)

    df = pd.DataFrame({
        "k [W/(m K)]":       simulation.k_borehole_history,
        "cp [J/(kg K)]":     simulation.cp_borehole_history,
        "rho [kg/m3]":       simulation.rho_borehole_history,
        "theta [-]":         theta,
        "water_input [m/s]": water_input,
    }, index=time_h)
    df.index.name = "time [h]"
    st.dataframe(df, use_container_width=True)
    _download_row(df, "Grout properties", "grout_properties")