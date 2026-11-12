"""Made-up sensor data, only for testing the code without a machine.

Every number here is a guess for a small motor. None of it was measured.
Real readings from the box will replace it.
"""
import numpy as np

# The same four numbers the firmware prints for every time window.
FEATURES = ["current_rms", "current_change", "vib_rms", "vib_peak"]

# (current in amps, vibration in g) for a healthy motor that is running or idle
HEALTHY = {"running": (2.0, 0.08), "idle": (0.15, 0.01)}


def window(state="running", fault=None, rng=None):
    rng = rng or np.random.default_rng()
    amps, vib = HEALTHY[state]
    cur = amps * rng.normal(1, 0.03)
    change = abs(rng.normal(0, 0.02 * amps)) + 0.001
    vib_rms = vib * rng.normal(1, 0.06)
    vib_peak = vib_rms * rng.normal(3.0, 0.2)
    if state == "running":
        if fault == "overload":        # extra load pulls more current
            cur *= 1.25
            change *= 1.3
        elif fault == "loose_mount":   # the mount shakes, current barely moves
            vib_rms *= 2.0
            vib_peak *= 2.3
            change *= 1.2
        elif fault == "bearing":       # early wear: a small rise with sharper peaks
            vib_rms *= 1.35
            vib_peak *= 1.8
    return [cur, change, vib_rms, vib_peak]


def make_windows(n, state="running", fault=None, seed=0):
    rng = np.random.default_rng(seed)
    return np.array([window(state, fault, rng) for _ in range(n)])
