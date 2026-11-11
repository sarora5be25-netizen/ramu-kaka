import numpy as np
from ramukaka.simulate import make_windows
from ramukaka.detector import Baseline, Watcher, machine_state
from ramukaka.assistant import History, learn_idle_hours, handle_flag


def base():
    X = np.vstack([make_windows(1500, "running", None, 0),
                   make_windows(500, "idle", None, 1)])
    return Baseline().fit(X)


def test_state():
    assert machine_state(0.1) == "idle" and machine_state(2.0) == "running"


def test_few_false_alarms():
    b = base()
    X = make_windows(300, "running", None, 9)
    assert np.mean([b.is_odd(x) for x in X]) < 0.1


def test_catches_faults():
    b = base()
    for f in ("overload", "loose_mount"):
        X = make_windows(200, "running", f, 3)
        assert np.mean([b.is_odd(x) for x in X]) > 0.8


def test_watcher_waits_for_several_windows():
    w = Watcher(base())
    odd = make_windows(1, "running", "overload", 4)[0]
    assert not w.push(odd)


def test_idle_hours():
    assert learn_idle_hours({2: [0.1] * 10, 9: [2.0] * 10}) == [2]


def test_owner_yes_needed():
    h = History()
    out = handle_flag("L1", h, ["M"], [2], False, {"M": True})
    assert not any("accepted" in l for l in out)
    out = handle_flag("L1", h, ["M"], [2], True, {"M": True})
    assert any("accepted" in l for l in out)
