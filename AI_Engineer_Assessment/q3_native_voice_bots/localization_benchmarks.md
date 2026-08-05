# Question 3: Market Localization & Speech Quality Benchmarks

## Market Performance Summary

| Market | ASR Model | Tested Languages | Code-Switching Accuracy | Regional Accent Handling | Failure Modes / Observed Gaps |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Philippines** | Deepgram `nova-2` | English + Tagalog (Taglish) | **88%** | N/A (Metro Manila Speech) | Phonetic confusion when user prefixing English terms with Tagalog inflections (e.g., "i-renew", "mag-claim"). |
| **Indonesia** | Deepgram `nova-2` | Bahasa Indonesia | **82%** | **75%** (Javanese Accent) | Occasional misinterpretation of regional filler words (*sih*, *kok*, *lah*) as vocabulary words. |

## Key Native Voice Adaptations
1. **Code-Switching:** Avoided literal word-for-word translation in favor of natural conversational Taglish and finance loanwords.
2. **Politeness Markers:** Integrated market-specific honorifics (`Po/Opo` in PH, `Bapak/Ibu` in ID).
3. **Audio Verification:** Reference call recordings are saved in this directory (`philippines_test_call.wav` & `indonesia_test_call.wav`).