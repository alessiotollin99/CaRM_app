# -*- coding: utf-8 -*-
"""
Default values and lookup tables for CaRM App.
"""

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
