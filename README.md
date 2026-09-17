# CaRM App

A [Streamlit](https://streamlit.io) web interface for [pyCaRM](https://github.com/BETALAB-team/pyCaRM) (CApacity Resistance Model), a Python library for simulating the transient thermal response of borehole heat exchanger (BHE) systems.

The app lets you configure a ground/borehole simulation through a set of input tabs, run it, and explore the results interactively — no scripting required.

## Features

- **Single or multi-borehole fields** — parallel or series connection modes
- **Pipe configurations** — single U-tube, double U-tube, coaxial, helical
- **Ground stratification** and time-variable grout properties (soil moisture / irrigation)
- **Two boundary-condition modes**: fixed inlet temperature/flow schedule (calendar-based or from file), or heat-flux mode driven by building load + heat pump performance
- **Environmental input** from an uploaded Excel file (external temperature, solar radiation)
- **Interactive results**: ground temperature (surface/middle/bottom), borehole cross-sections, time series, energy balance, and grout property plots
- **Session persistence** — save/load the full input configuration as JSON

## Installation

The app depends on the [pyCaRM](https://github.com/BETALAB-team/pyCaRM) library, expected as a sibling directory.

```bash
# clone both repos side by side
git clone https://github.com/BETALAB-team/pyCaRM.git ../CaRM
git clone https://github.com/alessiotollin99/CaRM_app.git
cd CaRM_app

# install the app's dependencies
pip install .

# install pyCaRM (editable, so local changes to it are picked up)
pip install -e ../CaRM
```

## Usage

```bash
streamlit run app.py
```

This opens the app in your browser. From there:

1. Choose a simulation mode (single or multi-BHE) and pipe configuration in the sidebar.
2. Upload the required input files (environmental data, and field layout for multi-BHE runs).
3. Fill in the input tabs (Ground, Borehole, Fluid, Environment, Simulation, Field Layout, Plant Schedule).
4. Click **Run simulation** and inspect the results tabs.

## Project structure

| File | Purpose |
|---|---|
| `app.py` | Main entry point — page layout, simulation wiring, and run logic |
| `ui_inputs.py` | Input tab rendering (ground, borehole, fluid, environment, simulation, field, plant schedule) |
| `ui_results.py` | Results tab rendering (plots and tables) |
| `defaults.py` | Default parameter values |
| `config_io.py` | Save/load session configuration as JSON |

## License

[MIT](LICENSE)
