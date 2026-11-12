"""Learns what normal looks like for one machine and flags what is different.

There is one model for each machine and each state (running or idle), learned
from healthy windows only. It never sees a fault while learning. The result is
"check this machine", never a failure date.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

IDLE_BELOW = 0.5  # amps. Under this the clamp sees almost nothing, so the machine is idle.
Z_LIMIT = 4.0     # any one number this many spreads away from normal counts as odd


def machine_state(current_rms, idle_below=IDLE_BELOW):
    return "idle" if current_rms < idle_below else "running"


class Baseline:
    def __init__(self, contamination=0.01, seed=0):
        self.models = {}
        self.contamination = contamination
        self.seed = seed

    def fit(self, X, min_windows=50):
        X = np.asarray(X, dtype=float)
        states = np.array([machine_state(row[0]) for row in X])
        for s in ("running", "idle"):
            part = X[states == s]
            if len(part) < min_windows:
                continue  # not enough normal data for this state yet
            scaler = StandardScaler().fit(part)
            forest = IsolationForest(n_estimators=200,
                                     contamination=self.contamination,
                                     random_state=self.seed)
            forest.fit(scaler.transform(part))
            self.models[s] = (scaler, forest)
        return self

    def is_odd(self, x):
        """True if this window does not look like the machine's normal.

        Two checks. The forest looks at all four numbers together. The second
        check catches one number that jumped a lot (extra load raises the
        current), which the forest can miss when the other numbers are normal.
        The box runs the second check too, so the two behave alike.
        """
        s = machine_state(x[0])
        if s not in self.models:
            return False
        scaler, forest = self.models[s]
        z = scaler.transform([x])
        return bool(forest.predict(z)[0] == -1 or np.abs(z).max() > Z_LIMIT)


class Watcher:
    """Raises the flag only when several recent windows look odd.

    One noisy reading should not wake the owner.
    """
    def __init__(self, baseline, window=6, need=4):
        self.baseline, self.window, self.need = baseline, window, need
        self.recent = []

    def push(self, x):
        self.recent = (self.recent + [self.baseline.is_odd(x)])[-self.window:]
        return sum(self.recent) >= self.need
