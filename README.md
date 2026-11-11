# Ramu Kaka

A small sensor box and voice assistant that warns small workshops before a
machine breaks. It does not repair machines. It says "check this machine".

Team LogicXLoop, Tech4Bharat 2026, problem 4.3 (machine breakdowns).
Team: Sirjan Kaur, Gurman Gill, Avneet Kaur, Manpreet Kaur.

## What is in this repo

| Part | State |
|---|---|
| `ramukaka/detector.py` learns each machine's normal running and flags what is not normal (Isolation Forest, trained on healthy data only) | Runs. Tested on made-up data only |
| `ramukaka/simulate.py` makes made-up current and vibration data | Runs. Every number is an assumption |
| `ramukaka/assistant.py` machine history, voice notes (as text), idle hours learned from power data, owner's yes before any call or spending | Runs. Calls, dealers and payment are **simulated** |
| `firmware/ramu_kaka/ramu_kaka.ino` ESP32 reads the SCT-013 clip and the MPU6050 and flags with an LED and buzzer | **Not tested on hardware yet** |
| `tests/` six tests for the above | 6 pass |

## What is not done

- No real motor has been measured yet. The detection numbers printed by the
  demo come from made-up data and say nothing about real accuracy. The papers
  we read report lower numbers (about 73% for a low-cost ESP32 study).
- The firmware has not run on a board. It uses a simple "far from normal"
  check on the box, while the Python code uses Isolation Forest. They will be
  made the same after the first real readings.
- Speech-to-text, real phone calls and payments are not built.
- The assistant's running cost is unknown.

## Run it

    pip install -r requirements.txt
    python -m ramukaka.demo
    python -m pytest

## Next

Wire the box to a small motor, record normal running, add extra load and a
loose mount, and report what the box catches, what it flags by mistake and
what it misses. Then try one real workshop machine with the owner's permission.

## Credits

Reference photos in our deck: Akul Verma, ElectronicWings motor test bench
(Apache-2.0). Hardware: ESP32, SCT-013 clip-on current sensor, MPU6050.
