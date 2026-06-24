from faster_whisper import WhisperModel
from .config import settings


def load_model() -> WhisperModel:
    kwargs: dict[str, object] = {
        "device": settings.whisper_device,
        "compute_type": settings.whisper_compute,
    }
    if settings.whisper_cpu_threads is not None:
        kwargs["cpu_threads"] = settings.whisper_cpu_threads
    if settings.whisper_num_workers is not None:
        kwargs["num_workers"] = settings.whisper_num_workers
    return WhisperModel(settings.whisper_model, **kwargs)
