"""
Signal extraction + nudge generation for the Q4 real-time pipeline.

Previously this logic lived inline in app.py with hardcoded latency_ms
values (110, 115, 95) attached to each signal type — those were claims, not
measurements. This module keeps the same rule-based signal detection but
times itself with time.perf_counter() so latency numbers in the report are
real, reproducible output of running this code, not estimates.

Scope note: this measures the signal-extraction + nudge-controller stage
only. ASR latency depends entirely on whichever streaming provider you wire
up (Deepgram/AssemblyAI/etc.) and has to be measured separately against a
live stream — it is NOT included in the numbers this module produces, and
latency_report.md says so explicitly rather than folding in a guessed
number for it.
"""

import time


class NudgeController:
    def __init__(self, cooldown_seconds: float = 15.0):
        self.last_nudge_time = {}
        self.cooldown_seconds = cooldown_seconds

    def _can_trigger(self, key: str, now: float) -> bool:
        if now - self.last_nudge_time.get(key, 0) > self.cooldown_seconds:
            self.last_nudge_time[key] = now
            return True
        return False

    def evaluate_transcript(self, transcript: str, speaker: str, now: float = None) -> dict:
        """Runs signal detection and returns a nudge dict, or None.

        Includes a measured_latency_ms field — the actual wall-clock time
        this call took, not a hardcoded constant.
        """
        start = time.perf_counter()
        now = now if now is not None else time.time()
        text = transcript.lower()
        nudge = None

        # 1. Compliance gap: agent talking policy terms without the
        #    mandatory recording disclosure.
        if speaker == "agent" and "recording" not in text and "policy" in text:
            if self._can_trigger("compliance_disclosure", now):
                nudge = {
                    "signal": "Compliance Gap",
                    "nudge": "ALERT: Mandatory call recording disclosure missing. Remind customer now.",
                    "priority": "HIGH",
                }

        # 2. Missed cross-sell opportunity.
        elif speaker == "customer" and any(
            k in text for k in ["second car", "another vehicle", "wife's car", "two bikes"]
        ):
            if self._can_trigger("cross_sell", now):
                nudge = {
                    "signal": "Missed Cross-Sell",
                    "nudge": "OPPORTUNITY: Customer mentioned a second vehicle. Suggest the multi-vehicle bundle.",
                    "priority": "MEDIUM",
                }

        # 3. Rising frustration.
        elif speaker == "customer" and any(
            k in text for k in ["ridiculous", "waste of time", "manager", "unacceptable"]
        ):
            if self._can_trigger("frustration", now):
                nudge = {
                    "signal": "Rising Frustration",
                    "nudge": "EMPATHY NEEDED: Acknowledge the customer's concern before continuing.",
                    "priority": "HIGH",
                }

        # 4. Payment difficulty.
        elif speaker == "customer" and any(
            k in text for k in ["can't afford", "lost my job", "behind on payments", "financial trouble"]
        ):
            if self._can_trigger("payment_difficulty", now):
                nudge = {
                    "signal": "Payment Difficulty",
                    "nudge": "Offer an approved payment-support plan or schedule a callback.",
                    "priority": "HIGH",
                }

        elapsed_ms = (time.perf_counter() - start) * 1000
        if nudge is not None:
            nudge["measured_latency_ms"] = round(elapsed_ms, 3)
        return nudge, elapsed_ms
