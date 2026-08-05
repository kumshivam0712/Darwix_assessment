# AI Engineer Assessment — CareShield

Voice-grounded lead qualification, a hybrid retrieval knowledge base, localized Philippines/Indonesia voice agents, and a real-time call-nudge engine.

---

# Project Status

| Question                            | Status     |
| ----------------------------------- | ---------- |
| **Q1 — Voice Agent**                | ✅ Complete |
| **Q2 — Knowledge Base**             | ✅ Complete |
| **Q3 — Native-Language Voice Bots** | ✅ Complete |
| **Q4 — Real-Time Call Nudges**      | ✅ Complete |

All required deliverables have been implemented, tested, and verified.

---

# Project Overview

This repository contains a complete implementation of the CareShield AI Engineer Assessment.

The project demonstrates:

* Voice-based lead qualification
* Hybrid Knowledge Base Retrieval (BM25 + TF-IDF)
* Localized multilingual voice agents for the Philippines and Indonesia
* Real-time conversation signal detection and agent nudges
* End-to-end benchmarking and latency measurement

---

# Features

## Q1 — Voice Agent

Implemented:

* Voice agent configuration
* System prompt
* Tool definitions
* Knowledge-grounded responses
* Lead qualification workflow
* Human escalation
* Lead creation tool
* Objection handling
* Missing-information handling
* Conflict resolution

Testing:

* ✅ All required test-call scenarios recorded
* ✅ Audio recordings included
* ✅ Complete transcripts included
* ✅ Call logs validated

Files:

```
q1_voice_agent/
```

Contains:

* system_prompt.txt
* tools.json
* call_transcripts.json
* recorded test calls

---

## Q2 — Knowledge Base

Implemented:

* Hybrid Retrieval

  * BM25
  * TF-IDF cosine similarity
* Retrieval fusion
* Confidence thresholding
* JSON schema
* Knowledge cleaning pipeline
* PII masking
* Test matrix

Files:

```
q2_knowledge_base/
```

Run:

```bash
cd q2_knowledge_base

python ingest_and_clean.py

python hybrid_retrieval.py
```

---

## Q3 — Native-Language Voice Bots

Implemented:

### Philippines

* English
* Filipino
* Taglish
* Accent handling
* Localization examples
* Recorded test calls
* Complete transcripts

### Indonesia

* Bahasa Indonesia
* English switching
* Accent handling
* Localization examples
* Recorded test calls
* Complete transcripts

Files:

```
q3_native_voice_bots/
```

Contains:

* Market configs
* Localization examples
* Recorded calls
* Call transcripts

---

## Q4 — Real-Time Call Nudges

Implemented:

Signal Detection

* Compliance Gap
* Missed Cross-Sell
* Rising Frustration
* Payment Difficulty

Features

* Real-time signal detection
* Per-signal cooldown
* Live WebSocket updates
* Dashboard
* End-to-end latency benchmark
* Offline streaming benchmark
* Real audio replay
* ASR → Signal → Nudge pipeline

Files:

```
q4_realtime_nudges/
```

Run:

```bash
cd q4_realtime_nudges

python benchmark.py

python streaming_e2e_benchmark.py "../q1_voice_agent/Q1 Audio.wav.wav"

python streaming_e2e_demo_utterance.py

python app.py
```

Open:

```
dashboard.html
```

to view live nudges.

---

# Repository Structure

```
.
├── q1_voice_agent
│   ├── system_prompt.txt
│   ├── tools.json
│   ├── call_transcripts.json
│   └── recorded_calls/
│
├── q2_knowledge_base
│   ├── ingest_and_clean.py
│   ├── hybrid_retrieval.py
│   ├── schema.json
│   └── knowledge_base_records.json
│
├── q3_native_voice_bots
│   ├── configs/
│   ├── localization_examples/
│   ├── recorded_calls/
│   └── call_transcripts.json
│
├── q4_realtime_nudges
│   ├── app.py
│   ├── benchmark.py
│   ├── streaming_e2e_benchmark.py
│   ├── streaming_e2e_demo_utterance.py
│   ├── nudge_engine.py
│   ├── latency_report.md
│   └── dashboard.html
│
└── requirements.txt
```

---

# Setup

Install dependencies

```bash
pip install -r requirements.txt
```

Configure environment

```bash
cp .env.example .env
```

Fill in the required API keys if using hosted ASR, TTS, or voice services.

---

# Validation

The repository has been validated for:

* JSON syntax
* Python compilation
* Retrieval pipeline
* Knowledge base ingestion
* Voice agent configuration
* Benchmark execution
* End-to-end nudge pipeline
* Audio processing
* Dashboard functionality

---

# Technologies Used

* Python
* BM25
* scikit-learn TF-IDF
* PocketSphinx
* WebSockets
* HTML
* JavaScript
* JSON Schema

---

# Architecture

```
Voice Call
      │
      ▼
Speech Recognition
      │
      ▼
Knowledge Retrieval
(BM25 + TF-IDF)
      │
      ▼
Voice Agent
      │
      ├─────────────► Lead Creation
      │
      └─────────────► Real-Time Signal Detection
                            │
                            ▼
                     Live Agent Nudges
```

---

# Notes

* Hybrid retrieval combines lexical and semantic-style ranking using BM25 and TF-IDF.
* The voice agent always retrieves information from the knowledge base before responding.
* Real-time nudges are generated using measurable conversation signals with configurable cooldowns.
* Localization has been implemented for both Philippine and Indonesian markets with recorded validation calls and transcripts.

---

# Assessment Status

All four assessment sections have been fully implemented and completed.

Deliverables included:

* ✅ Voice Agent
* ✅ Knowledge Base
* ✅ Native-Language Voice Bots
* ✅ Real-Time Call Nudges
* ✅ Recorded Calls
* ✅ Transcripts
* ✅ Benchmarks
* ✅ Documentation
* ✅ Validation
* ✅ End-to-End Pipeline

The repository is complete and ready for evaluation.
