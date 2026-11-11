"""Made-up sensor data for testing the code.

Every number here is an assumption chosen to look like a small motor.
It is NOT measured data. Real readings from the SCT-013 and MPU6050 will
replace this once the box is wired to a motor.
"""
import numpy as np

FEATURES = ["current_mean", "current_std", "vib_rms", "vib_peak"]

# (current amps, vibration g) for a healthy running motor and an idle one
HEALTHY = {"running": (2.0, 0.08), "idle": (0.15, 0.01)}


def window(state="running", fault=None, rng=None):
    """One time window of features for one machine."""
    rng = rng or np.random.default_rng()
    cur, vib = HEALTHY[state]
    cur_m = cur * rng.normal(1, 0.03)
    cur_s = 0.04 * cur * rng.normal(1, 0.1) + 0.002
    vib_r = vib * rng.normal(1, 0.06)
    vib_p = vib_r * rng.normal(3.0, 0.2)
    if state == "running":
        if fault == "overload":       # extra load pulls more current
            cur_m *= 1.25
            cur_s *= 1.3
        elif fault == "loose_mount":  # mount shakes more, current barely moves
            vib_r *= 2.0
            vib_p *= 2.3
            cur_s *= 1.2
        elif fault == "bearing":      # early wear: small rise with sharper peaks
            vib_r *= 1.35
            vib_p *= 1.8
    return [cur_m, cur_s, vib_r, vib_p]


def make_windows(n, state="running", fault=None, seed=0):
    rng = np.random.default_rng(seed)
    return np.array([window(state, fault, rng) for _ in range(n)])
