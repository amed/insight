import tempfile
from fastapi import FastAPI, UploadFile
from faster_whisper import WhisperModel

app = FastAPI()
model = WhisperModel("base", device="cpu", compute_type="int8")


@app.post("/transcribe")
async def transcribe(file: UploadFile):
  with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
    tmp.write(await file.read())
    tmp.flush()
    segments, _ = model.transcribe(tmp.name)
    text = " ".join(s.text.strip() for s in segments)

  return {"text": text}