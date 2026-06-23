from faster_whisper import WhisperModel
from .config import settings
from .formatters import normalize_probability


def run_transcription(
    model: WhisperModel,
    input_path: str,
    task: str,
    language: str | None,
    vad_filter: bool,
    word_timestamps: bool,
) -> dict:
    segments, info = model.transcribe(
        input_path,
        task=task,
        language=language,
        vad_filter=vad_filter,
        word_timestamps=word_timestamps,
    )
    normalized_segments = []
    full_text_parts = []
    for segment in segments:
        full_text_parts.append(segment.text.strip())
        words = []
        if word_timestamps and segment.words:
            words = [
                {"start": float(word.start), "end": float(word.end), "word": str(word.word)}
                for word in segment.words
            ]
        normalized_segments.append(
            {"start": float(segment.start), "end": float(segment.end), "text": segment.text.strip(), "words": words}
        )
    return {
        "model": settings.whisper_model,
        "task": task,
        "language": info.language or "",
        "language_probability": normalize_probability(info.language_probability),
        "duration": float(info.duration),
        "text": " ".join(full_text_parts).strip(),
        "segments": normalized_segments,
    }
