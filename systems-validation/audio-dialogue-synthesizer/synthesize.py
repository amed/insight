import argparse
import csv
import os
import sys

import numpy as np
import soundfile as sf
from kokoro import KPipeline

# kokoro outputs 24 khz float audio
SAMPLE_RATE = 24000

# silence inserted between turns, in seconds
GAP_SECONDS = 0.3

# american english. the voice prefixes (af_, am_) must match this language code.
LANG_CODE = "a"

# one voice per speaker, indexed by csv column. two distinct genders are used so the
# parties are easy to tell apart, which is the point of the validation audio.
VOICES = ("af_heart", "am_adam")


# a kokoro audio chunk is converted to a 1d float32 numpy array
def to_numpy(audio):
  if hasattr(audio, "detach"):
    audio = audio.detach().cpu().numpy()
  return np.asarray(audio, dtype=np.float32)


# one line of text is synthesized with the given voice into a single waveform
def synthesize_turn(pipeline, text, voice):
  chunks = []
  for result in pipeline(text, voice=voice):
    audio = getattr(result, "audio", None)
    if audio is None:
      audio = result[2]
    chunks.append(to_numpy(audio))
  if not chunks:
    return np.zeros(0, dtype=np.float32)
  return np.concatenate(chunks)


# the csv is read into ordered turns. each row holds one speaker's line in its column and
# leaves the other column empty. a row with both columns filled is an overlap and rejected.
def read_turns(path):
  turns = []
  with open(path, newline="", encoding="utf-8") as handle:
    for number, row in enumerate(csv.reader(handle), start=1):
      left = row[0].strip() if len(row) > 0 else ""
      right = row[1].strip() if len(row) > 1 else ""
      if not left and not right:
        continue
      if left and right:
        raise ValueError(f"row {number}: both columns are filled, speakers must not overlap")
      turns.append((0, left) if left else (1, right))
  if not turns:
    raise ValueError("no turns found in the csv")
  return turns


# both speakers are mixed into one mono track, turn after turn
def build_mono(segments):
  gap = np.zeros(int(GAP_SECONDS * SAMPLE_RATE), dtype=np.float32)
  parts = []
  for _, audio in segments:
    parts.append(audio)
    parts.append(gap)
  return np.concatenate(parts)


# each speaker is placed on its own channel (column 0 left, column 1 right). while one
# speaker talks the other channel is silent, so the parties are separated by channel.
def build_stereo(segments):
  gap = np.zeros(int(GAP_SECONDS * SAMPLE_RATE), dtype=np.float32)
  left, right = [], []
  for speaker, audio in segments:
    silence = np.zeros(len(audio), dtype=np.float32)
    left.append(audio if speaker == 0 else silence)
    right.append(silence if speaker == 0 else audio)
    left.append(gap)
    right.append(gap)
  return np.stack([np.concatenate(left), np.concatenate(right)], axis=1)


def main():
  parser = argparse.ArgumentParser(
    description="synthesize a two-speaker dialogue from a csv using kokoro"
  )
  parser.add_argument(
    "csv",
    help="csv file with 2 columns, one speaker per column, one non-empty cell per row",
  )
  parser.add_argument(
    "--stereo",
    action="store_true",
    help="put each speaker on its own channel (left/right). without it both share one mono channel",
  )
  args = parser.parse_args()

  turns = read_turns(args.csv)

  pipeline = KPipeline(lang_code=LANG_CODE)
  segments = [
    (speaker, synthesize_turn(pipeline, text, VOICES[speaker]))
    for speaker, text in turns
  ]

  audio = build_stereo(segments) if args.stereo else build_mono(segments)

  mode = "stereo" if args.stereo else "mono"
  output = f"{os.path.splitext(args.csv)[0]}-{mode}.wav"
  sf.write(output, audio, SAMPLE_RATE, subtype="PCM_16")

  print(f"wrote {output}: {mode}, {len(turns)} turns")


if __name__ == "__main__":
  try:
    main()
  except Exception as error:
    print(f"error: {error}", file=sys.stderr)
    sys.exit(1)
