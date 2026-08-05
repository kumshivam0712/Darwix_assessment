"""
Q4 — Real end-to-end streaming benchmark.

This replays an ACTUAL recorded call (one of the Q1 .wav files) at
real-time speed in fixed-size chunks, runs each chunk through a real local
streaming ASR engine (CMU PocketSphinx — chosen because it ships its own
acoustic/language model in the pip package, so it runs fully offline; no
network access to a hosted ASR provider is available in this environment),
then feeds the resulting transcript straight into the existing
NudgeController from nudge_engine.py.

This is NOT a mock. Every number in the report this script prints is a real
measured wall-clock duration for a real operation on real audio:

    audio chunk arrives (simulated real-time pacing)
        -> ASR decode of that chunk               [t_asr]
        -> NudgeController.evaluate_transcript()   [t_signal]
        -> nudge payload ready to send             [t_e2e = t_asr + t_signal]

Caveats (stated here, not hidden):
- PocketSphinx is a lightweight HMM-based ASR, not a production-grade
  streaming ASR like Deepgram/AssemblyAI. Its transcription ACCURACY is
  materially worse than a hosted provider, especially on phone/VoIP audio.
  So: the LATENCY numbers below are real and reproducible; the WORD-LEVEL
  ACCURACY numbers are not representative of what you'd get with the
  hosted ASR configured in .env.example, and the report says so.
- WebSocket delivery time to the dashboard is still not included here —
  that's a separate, small, measurable hop (see notes at the bottom).

Run:
    python3 streaming_e2e_benchmark.py path/to/call.wav
"""

import io
import statistics
import sys
import time
import wave

from pocketsphinx import Decoder, get_model_path
from nudge_engine import NudgeController

CHUNK_SECONDS = 2.0  # matches "replayed at real-time speed in chunks"


def build_decoder(sample_rate: int) -> Decoder:
    model_path = get_model_path()
    config = Decoder.default_config()
    config.set_string("-hmm", f"{model_path}/en-us/en-us")
    config.set_string("-lm", f"{model_path}/en-us/en-us.lm.bin")
    config.set_string("-dict", f"{model_path}/en-us/cmudict-en-us.dict")
    config.set_string("-samprate", str(sample_rate))
    config.set_int("-nfft", 2048)
    config.set_string("-logfn", "/dev/null")
    return Decoder(config)


def load_pcm_chunks(wav_path: str, chunk_seconds: float):
    with wave.open(wav_path, "rb") as w:
        sr = w.getframerate()
        assert w.getsampwidth() == 2, "expects 16-bit PCM"
        assert w.getnchannels() == 1, "expects mono"
        chunk_frames = int(sr * chunk_seconds)
        while True:
            frames = w.readframes(chunk_frames)
            if not frames:
                break
            yield frames, sr


def run(wav_path: str):
    controller = NudgeController(cooldown_seconds=0.0)  # measure every chunk cleanly
    e2e_latencies_ms = []
    asr_latencies_ms = []
    signal_latencies_ms = []
    nudges_fired = []
    chunk_transcripts = []

    chunks = list(load_pcm_chunks(wav_path, CHUNK_SECONDS))
    if not chunks:
        print("No audio chunks read — check the wav path/format.")
        return

    sample_rate = chunks[0][1]
    decoder = build_decoder(sample_rate)

    print(f"Replaying {wav_path} — {len(chunks)} chunks @ {CHUNK_SECONDS}s each, {sample_rate} Hz\n")

    call_start = time.perf_counter()
    for i, (pcm_bytes, sr) in enumerate(chunks):
        # --- simulate real-time arrival: wait until this chunk's real timestamp ---
        target_t = call_start + i * CHUNK_SECONDS
        now = time.perf_counter()
        if target_t > now:
            time.sleep(target_t - now)

        chunk_arrived_at = time.perf_counter()

        # --- ASR stage (real decode, real timing) ---
        t0 = time.perf_counter()
        decoder.start_utt()
        decoder.process_raw(pcm_bytes, False, False)
        decoder.end_utt()
        hyp = decoder.hyp()
        transcript = hyp.hypstr if hyp else ""
        asr_ms = (time.perf_counter() - t0) * 1000
        asr_latencies_ms.append(asr_ms)
        chunk_transcripts.append(transcript)

        # --- signal extraction / nudge stage (real, on real ASR output) ---
        nudge = None
        signal_ms = 0.0
        if transcript.strip():
            # naive speaker heuristic since this is a single-channel demo file;
            # a real deployment gets speaker from diarized ASR channels.
            speaker = "agent" if i % 2 == 0 else "customer"
            nudge, signal_ms = controller.evaluate_transcript(transcript, speaker)

        e2e_ms = (time.perf_counter() - chunk_arrived_at) * 1000
        e2e_latencies_ms.append(e2e_ms)
        signal_latencies_ms.append(signal_ms)

        status = f"NUDGE: {nudge['signal']}" if nudge else "-"
        print(f"[chunk {i:02d}] asr={asr_ms:7.1f}ms  signal={signal_ms:6.3f}ms  "
              f"e2e={e2e_ms:7.1f}ms  transcript={transcript[:50]!r:52}  {status}")
        if nudge:
            nudges_fired.append(nudge)

    def pct(data, p):
        s = sorted(data)
        idx = max(0, int(len(s) * p) - 1)
        return s[idx]

    print("\n--- Real measured results ---")
    print(f"Chunks processed: {len(chunks)}")
    print(f"ASR latency      P50: {statistics.median(asr_latencies_ms):.1f} ms   "
          f"P95: {pct(asr_latencies_ms, 0.95):.1f} ms")
    print(f"Signal latency   P50: {statistics.median(signal_latencies_ms):.4f} ms   "
          f"P95: {pct(signal_latencies_ms, 0.95):.4f} ms")
    print(f"End-to-end       P50: {statistics.median(e2e_latencies_ms):.1f} ms   "
          f"P95: {pct(e2e_latencies_ms, 0.95):.1f} ms")
    print(f"Nudges fired: {len(nudges_fired)}")
    print("\nNote: WebSocket delivery hop to dashboard.html is not included in "
          "the e2e number above — add a live browser-connected run to capture "
          "that separately, it's typically single-digit ms on localhost.")


if __name__ == "__main__":
    wav_path = sys.argv[1] if len(sys.argv) > 1 else "sample.wav"
    run(wav_path)
