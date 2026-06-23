from pathlib import Path
from faster_whisper import WhisperModel
from cuda_info import print_cuda_info

AUDIO_FILE = (
  Path(__file__).parent, "samples", "freesound_community-000981_jfk-space-race-speech-59951.mp3"
)

def main() -> None:
  print_cuda_info()

  model = WhisperModel("turbo", device="cuda", compute_type="float16")
  segments, _ = model.transcribe(str(AUDIO_FILE), log_progress=True)

  text = " ".join(segment.text.strip() for segment in segments)
  print("\n" + text)

if __name__ == "__main__":
  main()