"""
Q4 — Utterance-level real streaming demo (proves the full chain fires).

streaming_e2e_benchmark.py replays a real recorded call in blind fixed-size
time slices. That's an honest "replayed at real-time speed in chunks"
implementation per the brief, but a fixed 2s window can slice mid-word,
which is exactly what a naive implementation without endpointing/VAD would
do — real streaming ASR providers avoid this by finalizing on utterance
boundaries (silence/VAD), not a fixed clock.

This script demonstrates that behavior: each line is its own short audio
clip (simulating one VAD-segmented utterance), replayed at its own
real-time duration, decoded fully (not sliced), then run through the same
NudgeController. Every timing number is still real perf_counter output on
real audio — this file exists to prove the ASR -> nudge trigger chain
actually fires end-to-end, which the fixed-chunk run on the noisy real
call audio did not manage to demonstrate (PocketSphinx accuracy on that
recording was too low for any keyword to survive).

Run:
    python3 streaming_e2e_demo_utterance.py
"""

import glob
import time
import wave

from pocketsphinx import Decoder, get_model_path
from nudge_engine import NudgeController

# (audio file, speaker, expected signal or None)
UTTERANCES = [
    ("line1.wav", "agent", None),                 # policy mention, no disclosure -> compliance gap
    ("line2.wav", "customer", "Missed Cross-Sell"),
    ("line3.wav", "customer", "Rising Frustration"),
    ("line4.wav", "customer", "Payment Difficulty"),
    ("line5.wav", "customer", None),               # filler, should NOT trigger
    ("line6.wav", "agent", None),                  # small talk, should NOT trigger
]


def build_decoder(sample_rate: int) -> Decoder:
    model_path = get_model_path()
    config = Decoder.default_config()
    config.set_string("-hmm", f"{model_path}/en-us/en-us")
    config.set_string("-lm", f"{model_path}/en-us/en-us.lm.bin")
    config.set_string("-dict", f"{model_path}/en-us/cmudict-en-us.dict")
    config.set_string("-samprate", str(sample_rate))
    config.set_string("-logfn", "/dev/null")
    return Decoder(config)


def run():
    controller = NudgeController(cooldown_seconds=0.0)
    results = []

    for fname, speaker, expected in UTTERANCES:
        with wave.open(fname, "rb") as w:
            sr = w.getframerate()
            pcm = w.readframes(w.getnframes())
            duration_s = w.getnframes() / sr

        # simulate real-time arrival: this utterance "takes" duration_s to
        # be spoken before it's fully available to the ASR
        time.sleep(duration_s)

        decoder = build_decoder(sr)
        t0 = time.perf_counter()
        decoder.start_utt()
        decoder.process_raw(pcm, False, False)
        decoder.end_utt()
        hyp = decoder.hyp()
        transcript = hyp.hypstr if hyp else ""
        asr_ms = (time.perf_counter() - t0) * 1000

        nudge, signal_ms = controller.evaluate_transcript(transcript, speaker)
        e2e_ms = asr_ms + signal_ms

        fired = nudge["signal"] if nudge else None
        correct = (fired == expected)
        results.append((fname, expected, fired, correct, asr_ms, signal_ms, e2e_ms))

        print(f"[{fname}] speaker={speaker:9} duration={duration_s:.1f}s")
        print(f"   transcript : {transcript!r}")
        print(f"   expected   : {expected}")
        print(f"   fired      : {fired}   {'OK' if correct else 'MISMATCH'}")
        print(f"   asr={asr_ms:.1f}ms  signal={signal_ms:.4f}ms  e2e={e2e_ms:.1f}ms\n")

    n_correct = sum(1 for r in results if r[3])
    print(f"--- {n_correct}/{len(results)} utterances matched expected nudge behavior ---")
    e2e_all = [r[6] for r in results]
    print(f"E2E latency across utterances: min={min(e2e_all):.1f}ms max={max(e2e_all):.1f}ms")


if __name__ == "__main__":
    run()
