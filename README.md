# Ramu Kaka

Ramu Kaka is a small box for workshops that run old machines. A clip goes around each machine's power wire and a small chip sits near the motor. The box learns how each machine normally runs and lights a lamp and sounds a buzzer when one starts running differently. It does not repair anything. It only says "check this machine", early enough that the owner can fix it on a quiet day.

We are Team LogicXLoop (Sirjan Kaur, Gurman Gill, Avneet Kaur, Manpreet Kaur) and this is our idea submission for Tech4Bharat 2026, problem 4.3, machine breakdowns.

## What is here

The detector (`ramukaka/detector.py`) learns from healthy running only. It makes one model for each machine and each state, running or idle. For every short time window it looks at four numbers: current, how much the current changed since the last window, how hard the machine shakes, and the sharpest shake. A window is odd if an Isolation Forest finds it unusual, or if one number is far from its normal range. The flag is raised only when several recent windows are odd, so a single noisy reading does nothing.

The assistant (`ramukaka/assistant.py`) keeps a history for each machine, stores a worker's note, works out the quiet hours from when the current drops, and asks the owner before it contacts anyone.

The firmware (`firmware/ramu_kaka/ramu_kaka.ino`) is for the ESP32. It reads the current clip and the vibration chip and does the same "far from normal" check on the board.

`ramukaka/simulate.py` makes made-up sensor data so the code can be tested. `tests/` has six tests.

## What works and what does not

Working: the detector, the simulator, the assistant steps and the tests. Run `python -m ramukaka.demo` to see them.

Not working or not done:
- We have not measured a real motor yet. The demo uses made-up data, so its numbers only show that the code runs.
- The firmware has never run on a board.
- The assistant's calls to mechanics and dealers, and any payment, are simulated. Voice notes go in as text. Speech recognition is not built.
- We do not know yet what the assistant will cost to run.

## Test on real data

`experiments/cwru_validation.py` runs the detector on the Case Western Reserve University bearing data, which is real vibration recorded on a lab test rig. The model learned from normal recordings only. Results are in `experiments/cwru_results.txt`.

- It flagged 2% of held-out normal windows by mistake.
- It flagged every window of the faulty bearings (ball, inner race and outer race, all sizes in the data).
- When we left one motor load out of the learning, it flagged 1% to 2% of normal windows from three of the loads, but 29% from the lightest load. A machine running at a load it never saw while learning gets false alarms.

Do not read this as the accuracy we will get. The faults in that data were cut into the bearings on purpose and shake 2 to 10 times harder than a healthy one. Early wear in a workshop will be much harder to see. The rig also has no current sensor, so only vibration was used. A 2025 low-cost ESP32 study we read reached about 73%, and we expect to land nearer that than to 100%.

To get the data, clone a CWRU copy such as `XiongMeijing/CWRU-1` and run `python experiments/cwru_validation.py <path to its Data folder>`. We did not copy the data into this repo.

## Next

Wire the box to a small motor, record normal running, then add extra load and a loose mount and see what the box catches, what it flags by mistake and what it misses. After that, try it on one real machine with the owner's permission.

## Run it

    pip install -r requirements.txt
    python -m ramukaka.demo
    python -m pytest

## Credits

The reference photos in our deck are from Akul Verma's motor test bench on ElectronicWings (Apache-2.0). Test data: Case Western Reserve University Bearing Data Center. Licence for this repo: MIT.
