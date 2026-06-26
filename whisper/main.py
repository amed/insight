import os
import tempfile
import subprocess
from fastapi import FastAPI, UploadFile, Form
from faster_whisper import WhisperModel

app = FastAPI()
model = WhisperModel("base", device="cpu", compute_type="int8")


# the audio channel count is read with ffprobe
def channel_count(path):
  result = subprocess.run(
    ["ffprobe", "-v", "error", "-select_streams", "a:0",
     "-show_entries", "stream=channels", "-of", "csv=p=0", path],
    capture_output=True, text=True,
  )
  try:
    return int(result.stdout.strip())
  except ValueError:
    return 1


# a single channel is extracted into a mono wav file
def extract_channel(path, index, out_path):
  subprocess.run(
    ["ffmpeg", "-y", "-i", path, "-af", f"pan=mono|c0=c{index}", out_path],
    capture_output=True,
  )


# the file is transcribed; each segment is tagged with the given channel and start time
def transcribe_file(path, channel):
  segments, _ = model.transcribe(path)
  return [
    {"channel": channel, "start": float(s.start), "end": float(s.end), "text": s.text.strip()}
    for s in segments
  ]


# split is opt-in: it is only safe when each channel holds a single speaker.
# by default the whole file is transcribed once (stereo is downmixed).
@app.post("/transcribe")
async def transcribe(file: UploadFile, split: bool = Form(False)):
  with tempfile.TemporaryDirectory() as tmp:
    source = os.path.join(tmp, "input")
    with open(source, "wb") as handle:
      handle.write(await file.read())

    channels = channel_count(source)

    if split and channels >= 2:
      segments = []
      for index in (0, 1):
        out_path = os.path.join(tmp, f"ch{index}.wav")
        extract_channel(source, index, out_path)
        segments.extend(transcribe_file(out_path, index))
      segments.sort(key=lambda s: s["start"])
      split_done = True
    else:
      segments = transcribe_file(source, None)
      split_done = False

  text = " ".join(s["text"] for s in segments)
  return {"text": text, "channels": channels, "split": split_done, "segments": segments}
