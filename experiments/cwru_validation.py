"""Tests the "learn normal, flag what is different" idea on real vibration data.

Data: Case Western Reserve University bearing data (12 kHz, drive-end
accelerometer). Normal recordings at 4 motor loads, and bearings with seeded
faults. This is a lab test rig, not a workshop machine, and it has no current
signal, so only the vibration features are used.

The model sees only normal data while learning. Faults are never shown to it.

Run: python experiments/cwru_validation.py /path/to/Data
"""
import glob
import os
import sys
import numpy as np
from scipy.io import loadmat
from scipy.stats import kurtosis
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

WIN = 2048  # about 0.17 s at 12 kHz


def load_de(path):
    m = loadmat(path)
    key = [k for k in m if k.endswith("_DE_time")][0]
    return m[key].ravel().astype(float)


def windows(sig):
    out = []
    for i in range(0, len(sig) - WIN + 1, WIN):
        w = sig[i:i + WIN]
        w = w - w.mean()
        rms = np.sqrt(np.mean(w ** 2))
        out.append([rms, np.abs(w).max(), kurtosis(w)])
    return np.array(out)


def main(data_dir):
    normal = sorted(glob.glob(os.path.join(data_dir, "Normal", "*.mat")))
    nw = {os.path.basename(p): windows(load_de(p)) for p in normal}
    names = list(nw)
    # learn from the first 70% of each normal recording, keep the rest to test
    train = np.vstack([v[: int(len(v) * 0.7)] for v in nw.values()])
    held = np.vstack([v[int(len(v) * 0.7):] for v in nw.values()])
    sc = StandardScaler().fit(train)
    forest = IsolationForest(n_estimators=300, contamination=0.01,
                             random_state=0).fit(sc.transform(train))
    def odd(X):  # same two checks as ramukaka/detector.py
        z = sc.transform(X)
        return (forest.predict(z) == -1) | (np.abs(z).max(axis=1) > 4.0)

    print(f"normal files: {names}")
    print(f"trained on {len(train)} normal windows, no faults shown\n")
    print(f"held-out NORMAL windows flagged by mistake: {odd(held).mean():.1%}")

    groups = {}
    for p in sorted(glob.glob(os.path.join(data_dir, "12k_DE", "*.mat"))):
        name = os.path.basename(p)[:-4]
        kind = ("ball" if name.startswith("B") else
                "inner race" if name.startswith("IR") else "outer race")
        size = name[1:4] if name.startswith("B") else name[2:5]
        groups.setdefault((kind, size), []).append(windows(load_de(p)))
    print("\nfault windows flagged (higher is better):")
    print(f"{'fault':12s}{'size (1/1000 in)':>18s}{'windows':>10s}{'flagged':>10s}")
    allf = []
    for (kind, size), arrs in sorted(groups.items()):
        X = np.vstack(arrs)
        allf.append(odd(X))
        print(f"{kind:12s}{size:>18s}{len(X):>10d}{odd(X).mean():>10.1%}")
    allf = np.concatenate(allf)
    print(f"\nall fault windows flagged: {allf.mean():.1%}")

    # harder check: leave one whole motor load out of learning, then test on it
    print("\nnormal windows of an unseen motor load flagged by mistake:")
    for held in range(len(names)):
        tr = np.vstack([nw[n] for i, n in enumerate(names) if i != held])
        sc2 = StandardScaler().fit(tr)
        f2 = IsolationForest(n_estimators=300, contamination=0.01,
                             random_state=0).fit(sc2.transform(tr))
        z = sc2.transform(nw[names[held]])
        bad = (f2.predict(z) == -1) | (np.abs(z).max(axis=1) > 4.0)
        print(f"  load {held} left out: {bad.mean():.1%}")


if __name__ == "__main__":
    main(sys.argv[1])
