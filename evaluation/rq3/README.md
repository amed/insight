# Research Question 3

To what extent is BI extraction performance reduced by ASR errors relative to verified transcripts.

The module is dedicated to answer the third research question, which is how much the audio path costs compared to a verified transcript.

The build uses the hvb-audio batch: the same 50 calls in four paired variants (oracle transcript, machine transcript, mono audio, stereo audio). Stereo has the roles known by channel, mono makes diarisation infer them, so transcription error and speaker-assignment error are separated by design.


## Stages of evaluation

Evaluation schema is pinned to `insight-core/schemas/v1.json` through all phases.

### Prepare The Data (Stage 1)

Load the hvb-audio batch: per call the oracle record, the asr record, the mono wav, and the stereo wav, paired with gold intent and the gold speaker sequence.

### Runner (Stage 2)

The one cycle (`evaluation/run.py`) runs every call in every variant through each of the three pipelines via the core API, exactly once for all four research questions. This module only reads its prediction store.

### Measure Transcription (Stage 3)

Compute the word error rate of every non-oracle variant against the oracle turns (one pinned text normalisation), and the speaker-role accuracy for mono and stereo via word-overlap alignment.

### Store Scores (Stage 4)

Store per-field accuracy per variant and the paired flips against oracle (same call, same pipeline, did the field change to wrong or to right).

### Report (Stage 5)

Report extraction degradation as a function of measured WER, with diarisation (mono vs stereo) reported separately. The corpus's per-call MOS quality labels are available for stratification. Accent is not annotated anywhere and is stated as a limitation.
