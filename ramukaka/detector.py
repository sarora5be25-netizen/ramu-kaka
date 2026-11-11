"""Learns what normal looks like for one machine and flags what is not normal.

One model per machine and per state (running or idle), trained on healthy
windows only. The output is "check this machine". It never gives a failure date.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def machine_state(current_mean, idle_below=0.5):
    """Idle if the clamp sees almost no current, otherwise running."""
    return "idle" if current_mean < idle_below else "running"


class Baseline:
    def __init__(self, contamination=0.01, seed=0):
        self.models = {}
        self.contamination = contamination
        self.seed = seed

    def fit(self, X, min_windows=50):
        X = np.asarray(X, dtype=float)
        states = np.array([machine_state(r[0]) for r in X])
        for s in ("running", "idle"):
            part = X[states == s]
            if len(part) < min_windows:
                continue
            scaler = StandardScaler().fit(part)
            forest = IsolationForest(
                n_estimators=200, contamination=self.contamination,
                random_state=self.seed).fit(scaler.transform(part))
            self.models[s] = (scaler, forest)
        return self

    def is_odd(self, x):
        """True if this one window looks unlike the machine's normal."""
        s = machine_state(x[0])
        if s not in self.models:
            return False  # not enough normal data for this state yet
        scaler, forest = self.models[s]
        return forest.predict(scaler.transform([x]))[0] == -1


class Watcher:
    """Raises the flag only when several recent windows look odd.

    This cuts false alarms from one noisy reading.
    """
    def __init__(self, baseline, window=6, need=4):
        self.baseline, self.window, self.need = baseline, window, need
        self.recent = []

    def push(self, x):
        self.recent = (self.recent + [self.baseline.is_odd(x)])[-self.window:]
        return sum(self.recent) >= self.need
