from pathlib import Path
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from .config import settings
from .model import load_model
from .transcribe import run_transcription

app = FastAPI(title="Internal Whisper Service", docs_url=None, redoc_url=None, openapi_url=None)
model = load_model()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": settings.whisper_model,
        "device": settings.whisper_device,
        "compute_type": settings.whisper_compute,
    }


@app.post("/internal/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    task: str = Form(default="transcribe"),
    language: str | None = Form(default=None),
    vad_filter: bool = Form(default=True),
    word_timestamps: bool = Form(default=False),
):
    if task not in {"transcribe", "translate"}:
        raise HTTPException(status_code=422, detail="task must be transcribe or translate")

    suffix = Path(file.filename or "upload").suffix
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp_path = temp.name
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                temp.write(chunk)
        if not temp_path or Path(temp_path).stat().st_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        data = run_transcription(model, temp_path, task, language, vad_filter, word_timestamps)
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        await file.close()
