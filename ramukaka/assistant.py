"""The assistant side of Ramu Kaka.

Mechanic, dealer and payment steps are SIMULATED. Nothing here calls a real
phone number or moves real money. The owner's yes is required before any
step that spends money or stops production.
"""
import json
import numpy as np
from datetime import datetime


class History:
    """Machine history: flags, voice notes and repairs."""
    def __init__(self, path=None):
        self.path, self.events = path, []

    def add(self, machine, kind, text):
        self.events.append({"time": datetime.now().isoformat(timespec="seconds"),
                            "machine": machine, "kind": kind, "text": text})
        if self.path:
            with open(self.path, "w") as f:
                json.dump(self.events, f, indent=2)

    def of(self, machine):
        return [e for e in self.events if e["machine"] == machine]


def learn_idle_hours(hourly_current, idle_below=0.5, share=0.9):
    """Hours of the day when the machine is almost always idle.

    hourly_current: dict hour(0-23) -> list of current readings seen in that hour.
    Those hours are the safe quiet windows to fix things.
    """
    return sorted(h for h, v in hourly_current.items()
                  if len(v) and np.mean(np.array(v) < idle_below) >= share)


def voice_note(machine, text, history):
    """Stores a worker's note. Speech-to-text is not built; text goes in here."""
    history.add(machine, "voice_note", text)


def call_in_order(contacts, simulate_answers):
    """Tries mechanics, then dealers, in the owner's order (simulated calls)."""
    for who in contacts:
        if simulate_answers.get(who, False):
            return who
    return None


def handle_flag(machine, history, contacts, idle_hours, owner_says_yes,
                simulate_answers):
    """What the assistant does after the box flags a machine."""
    log = [f"Check {machine}: it is not running like its normal."]
    history.add(machine, "flag", "box flagged unusual running")
    if idle_hours:
        log.append(f"Quiet hours learned for {machine}: {idle_hours[0]}:00 to "
                   f"{idle_hours[-1]}:00. Suggest fixing then.")
    if not owner_says_yes:
        log.append("Waiting for the owner's yes before calling anyone.")
        return log
    who = call_in_order(contacts, simulate_answers)
    if who:
        log.append(f"[simulated] {who} accepted. Visit planned in a quiet hour.")
        history.add(machine, "call", f"{who} accepted (simulated)")
    else:
        log.append("[simulated] nobody answered. Added to the technician's weekly list.")
    return log
