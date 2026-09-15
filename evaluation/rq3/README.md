# Research Question 3 - ASR error propagation

To what extent is BI extraction performance reduced by ASR errors relative to verified transcripts.

Compares the same HarperValleyBank calls as oracle transcripts, supplied ASR transcripts, mono audio and stereo audio.

Measures word error rate, speaker-role accuracy and prediction changes relative to oracle inputs.

After [collecting predictions](../README.md), run from the repository root:

```bash
python3 evaluation/rq3/run.py
```

Writes `results.csv` and `scores.json` to `evaluation/rq3/out/`.
