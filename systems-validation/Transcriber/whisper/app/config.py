import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Settings:
    whisper_model: str = os.getenv("WHISPER_MODEL", "large-v3")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute: str = os.getenv("WHISPER_COMPUTE", "int8")
    whisper_cpu_threads: Optional[int] = int(os.getenv("WHISPER_CPU_THREADS")) if os.getenv("WHISPER_CPU_THREADS") else None
    whisper_num_workers: Optional[int] = int(os.getenv("WHISPER_NUM_WORKERS")) if os.getenv("WHISPER_NUM_WORKERS") else None


settings = Settings()
