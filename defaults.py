# -*- coding: utf-8 -*-
"""
Default values and lookup tables for CaRM App.
"""

import datetime as dt

# =============================================================================
# Surface material presets  (absorptance, emissivity)
# =============================================================================

SURFACE_MATERIALS = {
    "Manual":                  (None,  None),
    "Asphalt":                 (0.93,  0.95),
    "Concrete":                (0.60,  0.88),
    "Grass — high and dry":    (0.68,  0.90),
    "Grass — green after rain":(0.67,  0.98),
    "Snow — fresh":            (0.13,  0.82),
    "Sand — white powdered":   (0.45,  0.84),
    "Sand — wet":              (0.91,  0.95),
    "Sand — dry":              (0.82,  0.90),
}

# =============================================================================
# Pipe configuration defaults
# All lengths in [m], resistances in [m·K/W], conductivities in [W/m·K]
# =============================================================================

SINGLE_UTUBE_DEFAULTS = dict(
    Dpi          = 0.034,    # inside diameter [m]
    pipe_thick   = 0.003,    # wall thickness [m]  → De = 0.040 m
    pipe_spacing = 0.0826,   # shank spacing [m]
    Rp0          = 0.16,     # pipe-wall resistance [m·K/W]
    RppB         = 0.52,     # pipe-pipe resistance [m·K/W]
    n_pipes      = 2,
)

DOUBLE_UTUBE_DEFAULTS = dict(
    Dpi          = 0.026,    # inside diameter [m]
    pipe_thick   = 0.003,    # wall thickness [m]  → De = 0.032 m
    pipe_spacing = 0.0826,   # shank spacing [m]
    Rp0          = 0.25,     # pipe-wall resistance [m·K/W]
    RppB         = 0.72,     # pipe-pipe resistance between opposite pipes [m·K/W]
    RppA         = 0.55,     # pipe-pipe resistance between adjacent pipes [m·K/W]
    n_pipes      = 4,
    connection   = "P",
)

COAXIAL_DEFAULTS = dict(
    Dp1i         = 0.0408,   # inner pipe inside diameter [m]
    pipe1_thick  = 0.0046,   # inner pipe wall thickness [m]  → De1 = 0.050 m
    Dp2i         = 0.140,    # outer pipe inside diameter [m]
    pipe2_thick  = 0.005,    # outer pipe wall thickness [m]  → De2 = 0.150 m
    k_pipe1      = 0.40,     # inner pipe conductivity [W/m·K]
    k_pipe2      = 16.0,     # outer pipe conductivity [W/m·K] (steel)
    supply_and_return = "1_2",
)

HELICAL_DEFAULTS = dict(
    Dpi1         = 0.026,    # inner pipe 1 inside diameter [m]
    pipe1_thick  = 0.003,    # pipe 1 wall thickness [m]
    Dpi2         = 0.026,    # inner pipe 2 inside diameter [m]
    pipe2_thick  = 0.003,    # pipe 2 wall thickness [m]
    k_pipe       = 0.40,     # pipe conductivity [W/m·K]
    rih          = 0.190,    # inner helix radius [m]  (= outside helix diam/2 - pipe De)
    P_hel        = 0.100,    # pitch [m]
    supply_and_return = "1_2",
)

BOREHOLE_DEFAULTS = dict(
    Lbore  = 100.0,
    D0     = 0.15,
    cp_0   = 1460.0,
    rho_0  = 1655.0,
    k0     = 1.83,
)

# Borehole diameter D0 needs more room than BOREHOLE_DEFAULTS["D0"] for some
# pipe types — keyed by pipe_type, looked up in render_borehole_tab.
D0_PIPE_TYPE_OVERRIDES = {
    # Helical coils need more room than the generic default: with
    # HELICAL_DEFAULTS (rih=0.19), D0 must be > 2*(rih+Dpi2+2*pipe_thick)
    # ~ 0.44 m, matching the D0=0.5 used in CaRM's own Helical examples.
    "Helical": 0.5,
}

# =============================================================================
# Variable grout properties (soil moisture / irrigation) defaults
# Only meaningful for Helical BHEs — see carm.properties.BoreholeGeometry.
# =============================================================================

IRRIGATION_DEFAULTS = dict(
    enabled       = False,
    soil_type     = "sand",   # "sand" | "loam" | "clay"
    D_irrigation  = 0.030,    # irrigation pipe diameter [m]
    perf_fraction = 0.5,      # irrigation pipe perforation fraction [-]
    water_rate    = 5.0e-5,   # default constant irrigation rate for a new period [m/s]
)

# =============================================================================
# Heat flux mode defaults (building load driven, instead of Tf1 driven)
# =============================================================================

HEATFLUX_DEFAULTS = dict(
    mw_value   = 0.1657,   # pump mass flow rate while a load period is active [kg/s]
    Q_load     = 5000.0,   # default load for a new period, + = extraction/heating [W]
    T_supply   = 45.0,     # default supply temperature for a new period [°C]
)

# =============================================================================
# Ground tab defaults
# =============================================================================

GROUND_DEFAULTS = dict(
    Tg         = 13.0,   # undisturbed ground temperature [°C]
    L          = 100.0,  # borehole active length [m]
    L_sup      = 1.0,    # surface layer thickness [m]
    L_inf      = 10.0,   # bottom layer thickness [m]
    rn         = 10.0,   # far-field radius [m]
    n_mesh     = 20,      # radial mesh cells [-]
    m_mesh     = 40,      # axial mesh cells [-]
    m_mesh_sup = 4,       # axial cells, surface layer [-]
    m_mesh_inf = 40,      # axial cells, bottom layer [-]
    n_layers   = 1,       # number of stratification layers [-]
)

# Default values for a newly added ground-stratification layer row.
GROUND_LAYER_DEFAULTS = dict(
    k   = 1.83,    # thermal conductivity [W/m·K]
    cp  = 947.0,   # specific heat [J/kg·K]
    rho = 1900.0,  # density [kg/m³]
    th  = 111.0,   # thickness [m]
)

# =============================================================================
# Fluid tab defaults
# =============================================================================

FLUID_DEFAULTS = dict(
    T_ref         = 10.0,  # reference temperature [°C]
    concentration = 25,    # glycol concentration [%], only shown for non-water fluids
)

# =============================================================================
# Environment tab defaults
# =============================================================================

ENV_DEFAULTS = dict(
    # Fallbacks used when surface material is "Manual" (no preset in
    # SURFACE_MATERIALS to draw absorptance/emittance from).
    absorptance_manual = 0.70,
    eps_manual          = 0.95,
    Tm             = 13.0,               # mean annual air temperature [°C]
    R_ext          = 0.04,               # external thermal resistance [m²·K/W]
    At             = 10.0,               # annual temperature amplitude [K]
    tau_y          = 365 * 24 * 3600,    # year duration [s]
    tau_date       = dt.date(2024, 1, 1),   # simulation start date
    tau_shift_date = dt.date(2024, 2, 14),  # date of minimum surface temperature
)

# =============================================================================
# Simulation tab defaults
# =============================================================================

SIM_DEFAULTS = dict(
    dt      = 3600,  # time step [s]
    n_steps = 276,    # number of steps [-]
)

# =============================================================================
# Field layout tab defaults (multi-BHE modes only)
# =============================================================================

FIELD_DEFAULTS = dict(
    n_bhes = 9,
    x_min  = -2.5,  # field x_min [m]
    y_min  = -2.5,  # field y_min [m]
    x_max  = 12.5,  # field x_max [m]
    y_max  = 12.5,  # field y_max [m]
)

# =============================================================================
# Plant schedule tab defaults (calendar-schedule mode)
# =============================================================================

PLANT_DEFAULTS = dict(
    heat_flux_enabled = False,
    same_profile       = True,   # "from file" mode: all circuits share one profile
    # Same pump flow rate assumption as heat-flux mode's own default.
    mw                 = HEATFLUX_DEFAULTS["mw_value"],
    tf1_new_period     = 2.0,    # fallback Tf1 [°C] for a circuit's first-ever added period
)
