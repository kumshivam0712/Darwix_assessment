"""
Runs the nudge engine against a mixed test set to produce REAL latency and
false-positive numbers, instead of asserting them. Run directly:

    python3 benchmark.py

Covers the required test coverage: missed cross-sell, skipped disclosure,
rising frustration, payment difficulty, and noisy/ambiguous lines that
should NOT trigger a nudge (false-positive check).
"""

import statistics
import time

from nudge_engine import NudgeController

TEST_LINES = [
    # (speaker, transcript, should_trigger)
    ("agent", "Let me walk you through our policy options for your vehicle.", True),   # compliance gap
    ("customer", "Actually I also have a second car I'd like covered.", True),          # cross-sell
    ("customer", "This is ridiculous, I want to speak to your manager.", True),         # frustration
    ("customer", "I lost my job recently and I'm behind on payments.", True),           # payment difficulty
    # Noisy / ambiguous — must NOT trigger
    ("customer", "uh, yeah, so, I guess, um, that's fine I think", False),
    ("customer", "sorry can you repeat that, the line's breaking up", False),
    ("agent", "Great, thanks for confirming your address.", False),
    ("customer", "haha no worries, all good on my end", False),
    ("agent", "Just checking in, how's your day going so far?", False),
]


def run_benchmark(n_repeats: int = 50):
    latencies = []
    false_positives = 0
    false_negatives = 0
    total_should_trigger = sum(1 for _, _, expect in TEST_LINES if expect)
    total_should_not = len(TEST_LINES) - total_should_trigger

    for _ in range(n_repeats):
        controller = NudgeController(cooldown_seconds=0.0)  # disable cooldown for clean per-line measurement
        for speaker, text, should_trigger in TEST_LINES:
            nudge, elapsed_ms = controller.evaluate_transcript(text, speaker)
            latencies.append(elapsed_ms)
            triggered = nudge is not None
            if triggered and not should_trigger:
                false_positives += 1
            if not triggered and should_trigger:
                false_negatives += 1

    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95) - 1]

    fp_rate = false_positives / (total_should_not * n_repeats)
    fn_rate = false_negatives / (total_should_trigger * n_repeats)

    print(f"Runs: {n_repeats} passes over {len(TEST_LINES)} lines ({n_repeats * len(TEST_LINES)} evaluations)")
    print(f"Signal extraction latency  P50: {p50:.4f} ms   P95: {p95:.4f} ms")
    print(f"False positive rate (noisy/ambiguous lines that should NOT trigger): {fp_rate:.1%}")
    print(f"False negative rate (real signals that were missed): {fn_rate:.1%}")
    return {
        "p50_ms": round(p50, 4),
        "p95_ms": round(p95, 4),
        "false_positive_rate": round(fp_rate, 4),
        "false_negative_rate": round(fn_rate, 4),
        "n_evaluations": n_repeats * len(TEST_LINES),
    }


if __name__ == "__main__":
    run_benchmark()
