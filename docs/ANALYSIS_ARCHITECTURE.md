# Chat Analysis Architecture

## Production decision

Stream Pulse uses one of two planned multilingual context analyzers:

- Qwen3-0.6B for Low System Mode
- Qwen3-1.7B for High Accuracy Mode

The exact source repositories, immutable revisions, runtime formats, licenses,
download locations, sizes, and checksums have not been selected or verified.
They remain `null` in the manifest. No Qwen model is downloaded, packaged, or
released by this architecture document.

MiniLM and DistilBERT are not selected for production chat analysis. Their
benchmark scripts and report remain archived research only.

## Runtime flow

```text
chat collection
→ deterministic statistics and spam rules
→ recent-message context window
→ selected Qwen context analyzer
→ language prompt/profile
→ strict JSON result
→ alert threshold evaluation
```

1. **Chat collection** gathers ordered, timestamped messages needed for the
   current analysis interval.
2. **Deterministic statistics and spam rules** calculate counts, repetition,
   rates, and other facts that do not require a model.
3. **Recent-message context window** selects a short bounded window so the
   analyzer can interpret interactions rather than isolated messages.
4. **Selected Qwen context analyzer** runs Low System Mode or High Accuracy
   Mode according to the user's system and quality preference.
5. **Language prompt/profile** supplies language-specific instructions,
   terminology, examples, labels, and thresholds without duplicating model
   weights.
6. **Strict JSON result** is parsed and validated. Invalid output is rejected;
   prose or extra fields are not accepted.
7. **Alert threshold evaluation** combines validated model output with
   deterministic signals and configured rules before recommending or showing
   an alert.

## Language prompt/profile packages

There is one small configuration package for each supported language:
`en-US`, `es-ES`, `pt-BR`, `ru-RU`, `de-DE`, `fr-FR`, `ja-JP`, `it-IT`,
`pl-PL`, and `tr-TR`.

Every profile will eventually contain:

- analysis instructions
- Twitch terminology
- common slang examples
- sarcasm examples
- playful-insult examples
- technical-complaint examples
- output labels
- confidence thresholds

Profiles are text or JSON configuration only. They must not contain model
weights, tokenizer weights, ONNX files, or separately trained language models.
The same profile interface must work with both context-analysis modes.

## Strict result contract

The analyzer will eventually return exactly this JSON shape:

```json
{
  "mood": "neutral | positive | playful | tense | hostile | confused",
  "conflictProbability": 0.0,
  "sarcasmProbability": 0.0,
  "complaintProbability": 0.0,
  "questionIntensity": 0.0,
  "spamIntensity": 0.0,
  "confidence": 0.0,
  "alertRecommended": false,
  "reasonCode": "string"
}
```

`mood` must be one allowed label. Every probability, intensity, and confidence
value must be a finite number from `0.0` through `1.0`. `alertRecommended` must
be Boolean, and `reasonCode` must be a stable machine-readable string defined
by the profile/output contract. Runtime validation must reject missing,
additional, malformed, or out-of-range fields.

The result is evidence for alert evaluation, not an instruction to bypass
deterministic thresholds. Statistics and spam rules remain authoritative for
facts they can measure directly.
