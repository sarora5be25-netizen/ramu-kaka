"""End to end demo on made-up data. Run: python -m ramukaka.demo"""
import numpy as np
from .simulate import make_windows, window
from .detector import Baseline, Watcher
from .assistant import History, learn_idle_hours, voice_note, handle_flag


def rates(baseline, fault, n=200, seed=1):
    X = make_windows(n, "running", fault, seed)
    return float(np.mean([baseline.is_odd(x) for x in X]))


def main():
    # three weeks of normal running and idle windows for one machine
    train = np.vstack([make_windows(1500, "running", None, 0),
                       make_windows(500, "idle", None, 1)])
    base = Baseline().fit(train)

    print("Made-up data. These numbers only show the code works, not how")
    print("accurate it is on a real motor.\n")
    print(f"healthy windows flagged by mistake: {rates(base, None):.0%}")
    for f in ("overload", "loose_mount", "bearing"):
        print(f"{f:12s} windows caught: {rates(base, f):.0%}")

    # the watcher needs several odd windows in a row
    w, rng, raised = Watcher(base), np.random.default_rng(5), None
    for i in range(30):
        x = window("running", "loose_mount" if i >= 10 else None, rng)
        if w.push(x) and raised is None:
            raised = i
    print(f"\nloose mount starts at window 10, flag raised at window {raised}")

    # assistant steps (calls and payment are simulated)
    h = History()
    voice_note("Loom 3", "belt sound is louder since morning", h)
    hourly = {hr: list(np.random.default_rng(hr).normal(0.15, 0.02, 20))
              for hr in (1, 2, 3, 4)}
    hourly.update({hr: [2.0] * 20 for hr in range(8, 20)})
    idle = learn_idle_hours(hourly)
    print("\n--- assistant, owner has not answered ---")
    print("\n".join(handle_flag("Loom 3", h, ["Mechanic Raju", "Dealer"], idle,
                                False, {})))
    print("\n--- assistant, owner says yes ---")
    print("\n".join(handle_flag("Loom 3", h, ["Mechanic Raju", "Dealer"], idle,
                                True, {"Dealer": True})))


if __name__ == "__main__":
    main()
