# -*- coding: utf-8 -*-
"""
End-to-end smoke test for the default (Single BHE) workflow.

Drives app.py through Streamlit's AppTest harness: uploads the real
example environmental file, runs a short simulation, and checks it
completes without raising. This exercises the actual production code
path (widgets -> session_state -> pyCaRM objects -> Simulation.run()),
so it's the regression guard for pyCaRM API drift and for wiring
changes -- not a mock of it.

Kept to a handful of timesteps purely for test speed; correctness of
the physics is pyCaRM's own responsibility, not this app's.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
APP_PATH = ROOT / "app.py"
ENV_XLSX = ROOT / "input_env.xlsx"

N_STEPS_SMOKE = 5


def _find(elements, label_substring):
    matches = [e for e in elements if label_substring in (e.label or "")]
    assert matches, f"no element with label containing {label_substring!r}"
    return matches[0]


def test_single_bhe_default_run_completes():
    at = AppTest.from_file(str(APP_PATH), default_timeout=120)
    at.run()
    assert not at.exception, f"initial render raised: {at.exception}"

    input_tab_labels = [t.label for t in at.tabs[:6]]
    assert input_tab_labels == [
        "1 Ground", "2 Borehole", "3 Fluid", "4 Environment", "5 Simulation",
        "6 Plant Schedule",
    ], "expected numbered input tab labels with no checkmarks on a fresh load"

    env_uploader = _find(at.file_uploader, "Environmental data")
    env_uploader.set_value((
        "input_env.xlsx",
        ENV_XLSX.read_bytes(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ))
    at.number_input(key="cfg_n_steps").set_value(N_STEPS_SMOKE)
    at.run()
    assert not at.exception, f"render after upload raised: {at.exception}"

    run_button = _find(at.button, "Run simulation")
    run_button.click()
    at.run()

    assert not at.exception, f"simulation run raised: {at.exception}"
    assert any("Simulation complete" in s.value for s in at.success), (
        "expected a 'Simulation complete!' success message"
    )

    # T_history is (n_steps + 1, n_bhes, n_mesh_nodes): +1 for the initial
    # condition, 1 borehole for the default Single BHE mode.
    T_history = at.session_state["T_history"]
    assert T_history.shape[0] == N_STEPS_SMOKE + 1, (
        f"unexpected T_history shape {T_history.shape} for {N_STEPS_SMOKE} steps"
    )
    assert T_history.shape[1] == 1, "expected a single borehole for Single BHE mode"
