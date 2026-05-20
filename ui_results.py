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
            x=vals, y=depth, mode="lines", name=label,
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
# SUB-TAB: 3-D Field
# ─────────────────────────────────────────────────────────────────────────────

def render_3d(T_history, model, n_bhes, nsup, nground, slices,
              depth, n_mesh, m_mesh, n_steps, D0):
    st.subheader("3-D field visualisation")
    st.caption("All BHEs shown. Selected BHE shows ground slice when 'T_ground' is chosen.")

    col1, col2, col3 = st.columns(3)
    step_3d   = col1.slider("Timestep", 1, n_steps, n_steps // 2, key="3d_step")
    focus_bhe = col2.selectbox("Focus BHE", list(range(n_bhes)), key="3d_bhe")
    quantity  = col3.selectbox("Quantity", ["T_shell", "T_ground"])

    N_cyl  = 36
    theta  = np.linspace(0, 2 * np.pi, N_cyl)
    r_bore = D0 / 2.0

    # global colour range
    if quantity == "T_shell":
        T_ref = np.array([T_history[step_3d, b, slices["shell"]] for b in range(n_bhes)])
        cmin, cmax = float(T_ref.min()), float(T_ref.max())
    else:
        T_ref = T_history[step_3d, focus_bhe, nsup: nsup + nground]
        cmin, cmax = float(T_ref.min()), float(T_ref.max())

    # BHE positions
    if hasattr(model, "field") and model.field is not None:
        bhe_x = [model.field.boreholes[i].x for i in range(n_bhes)]
        bhe_y = [model.field.boreholes[i].y for i in range(n_bhes)]
    else:
        bhe_x = [0.0]
        bhe_y = [0.0]

    fig = go.Figure()

    for b in range(n_bhes):
        bx, by     = bhe_x[b], bhe_y[b]
        is_focus   = (b == focus_bhe)
        T_bhe      = T_history[step_3d, b, slices["shell"]]

        # cylinder: z goes from 0 (surface) to depth[-1] (bottom) — depth array is negative
        Z_cyl = np.outer(depth,    np.ones(N_cyl))
        X_cyl = bx + r_bore * np.outer(np.ones(m_mesh), np.cos(theta))
        Y_cyl = by + r_bore * np.outer(np.ones(m_mesh), np.sin(theta))
        C_cyl = np.outer(T_bhe,   np.ones(N_cyl))

        fig.add_trace(go.Surface(
            x=X_cyl, y=Y_cyl, z=Z_cyl,
            surfacecolor=C_cyl,
            colorscale="RdYlGn_r",
            cmin=cmin, cmax=cmax,
            showscale=(b == 0),
            colorbar=dict(title="T [°C]", thickness=15, x=1.02) if b == 0 else None,
            opacity=1.0 if is_focus else 0.5,
            name=f"BHE {b}",
            hovertemplate=f"BHE {b}<br>z = %{{z:.2f}} m<br>T = %{{customdata:.3f}} °C<extra></extra>",
            customdata=C_cyl,
        ))

    # ground slice for focus BHE
    if quantity == "T_ground":
        r0_f   = model.ground[0].r0
        rn_f   = model.ground[focus_bhe].rn
        radius = np.linspace(r0_f, rn_f, n_mesh)
        bx, by = bhe_x[focus_bhe], bhe_y[focus_bhe]

        T_gs   = T_history[step_3d, focus_bhe, nsup: nsup + nground].reshape(m_mesh, n_mesh)
        Z_g    = np.outer(depth, np.ones(n_mesh))
        X_g    = bx + np.outer(np.ones(m_mesh), radius)
        Y_g    = by * np.ones_like(X_g)

        fig.add_trace(go.Surface(
            x=X_g, y=Y_g, z=Z_g,
            surfacecolor=T_gs,
            colorscale="RdYlGn_r",
            cmin=cmin, cmax=cmax,
            showscale=False,
            opacity=0.85,
            name=f"Ground BHE {focus_bhe}",
            hovertemplate="r = %{x:.2f} m<br>z = %{z:.2f} m<br>T = %{customdata:.3f} °C<extra></extra>",
            customdata=T_gs,
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title="x [m]",
            yaxis_title="y [m]",
            zaxis=dict(
                title="Depth [m]",
                range=[float(depth[-1]), 0],  # 0 at top, negative bottom
            ),
            aspectmode="manual",
            aspectratio=dict(x=1, y=1, z=3),
        ),
        margin=dict(t=40, b=10, l=10, r=10),
        height=720,
    )
    st.plotly_chart(fig, use_container_width=True)