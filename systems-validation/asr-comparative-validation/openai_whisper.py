from pathlib import Path
import whisper
from cuda_info import print_cuda_info

AUDIO_FILE = (
  Path(__file__).parent, "samples", "freesound_community-000981_jfk-space-race-speech-59951.mp3"
)

def main() -> None:
  print_cuda_info()

  model = whisper.load_model("turbo", device="cuda")
  result = model.transcribe(str(AUDIO_FILE), verbose=False)

  print("\n" + result["text"].strip())

if __name__ == "__main__":
  main()