import os
import subprocess
import tempfile
import torch
from fastapi import FastAPI, UploadFile
from pyannote.audio import Pipeline

MODEL_NAME = os.environ.get("DIARIZATION_MODEL_NAME", "pyannote/speaker-diarization-community-1")
DEVICE = os.environ.get("DIARIZATION_DEVICE", "cpu")

app = FastAPI()

# the gated pipeline is loaded once at startup and kept warm for the process lifetime.
# HF_TOKEN must be set and the model terms accepted on hugging face, or this fails loudly.
pipeline = Pipeline.from_pretrained(MODEL_NAME)
if pipeline is None:
  raise RuntimeError(
    f"could not load {MODEL_NAME}. it is gated: accept its terms on hugging face "
    "and set a valid HF_TOKEN."
  )
pipeline.to(torch.device(DEVICE))


# the upload is decoded to 16 kHz mono wav, the rate pyannote works at. this avoids the
# mp3 header duration mismatch that breaks pyannote's chunk crop, and normalizes any format.
def to_wav(source, out_path):
  subprocess.run(
    ["ffmpeg", "-y", "-i", source, "-ac", "1", "-ar", "16000", out_path],
    capture_output=True, check=True,
  )


# the audio is diarized into anonymous speaker turns (who spoke when)
@app.post("/diarize")
async def diarize(file: UploadFile):
  with tempfile.TemporaryDirectory() as tmp:
    source = os.path.join(tmp, "input")
    with open(source, "wb") as handle:
      handle.write(await file.read())
    wav = os.path.join(tmp, "audio.wav")
    to_wav(source, wav)
    output = pipeline(wav)

  diarization = getattr(output, "speaker_diarization", output)
  turns = [
    {"start": float(turn.start), "end": float(turn.end), "speaker": str(label)}
    for turn, _, label in diarization.itertracks(yield_label=True)
  ]
  turns.sort(key=lambda t: t["start"])
  speakers = sorted({t["speaker"] for t in turns})

  return {"turns": turns, "speakers": speakers}
