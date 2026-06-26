# Audio dialogue synthesizer

Generates two-speaker dialogue audio from a csv using kokoro, to produce test material for
the asr and diarization pipeline. Two output modes:

- mono: both speakers share one channel (tests diarization, who spoke when).
- stereo: each speaker is on its own channel (tests channel based separation).

The speakers never overlap, so the timeline is just one turn after another.

## Setup

Python 3.10 to 3.12 is expected. One system package is needed for phonemization.

```bash
# linux
sudo apt-get install espeak-ng
# macos
brew install espeak-ng

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The kokoro model (a few hundred mb) is downloaded from hugging face on the first run.

## CSV format

Two columns, no header. The first column is speaker 1, the second column is speaker 2.
Each row holds one line in one column and leaves the other empty. The row order is the turn
order. A row with both columns filled is treated as an overlap and rejected.

```csv
"Hi, thanks for calling support. How can I help?",
,"Hi, I was charged twice for my order last week."
"Can I get your order number?",
,"Sure, it's 48213."
```

See `example.csv`.

## Usage

```bash
# both speakers on one mono channel
python synthesize.py example.csv

# each speaker on a separate channel (column 1 left, column 2 right)
python synthesize.py --stereo example.csv
```

The output is written next to the csv as `<name>-mono.wav` or `<name>-stereo.wav` at
24 khz.

## Voices

One kokoro voice is assigned per speaker. The two voices are the `VOICES` constant at the
top of `synthesize.py`; change them there.
