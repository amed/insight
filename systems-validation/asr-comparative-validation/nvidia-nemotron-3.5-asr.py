# from pathlib import Path
# import nemo.collections.asr as nemo_asr
# from cuda_info import print_cuda_info

# AUDIO_FILE = Path(
#   Path(__file__).parent, "samples", "freesound_community-000981_jfk-space-race-speech-59951.wav"
# )

# MODEL_NAME = "nvidia/nemotron-3.5-asr-streaming-0.6b"

# def main() -> None:
#   print_cuda_info()

#   model = nemo_asr.models.ASRModel.from_pretrained(MODEL_NAME)
#   model = model.cuda().eval()

#   config = model.get_transcribe_config()
#   config.use_lhotse = False
#   config.target_lang = "en-US"

#   result = model.transcribe(
#     [str(AUDIO_FILE)],
#     override_config=config,
#   )[0]

#   text = result.text if hasattr(result, "text") else str(result)

#   print("\n" + text.strip())

# if __name__ == "__main__":
#   main()

from pathlib import Path
import subprocess
import tempfile

import nemo.collections.asr as nemo_asr

AUDIO_FILE = Path(__file__).parent / "samples" / (
  "freesound_community-000981_jfk-space-race-speech-59951.mp3"
)

MODEL_NAME = "nvidia/nemotron-3.5-asr-streaming-0.6b"


def main() -> None:
  model = nemo_asr.models.ASRModel.from_pretrained(MODEL_NAME)
  model = model.cuda().eval()

  config = model.get_transcribe_config()
  config.use_lhotse = False
  config.target_lang = "en-US"
  config.batch_size = 1

  # split the audio into short chunks - OOM is hit :/
  with tempfile.TemporaryDirectory() as temp_dir:
    chunk_pattern = str(Path(temp_dir) / "chunk_%03d.wav")

    subprocess.run(
      [
        "ffmpeg",
        "-y",
        "-i",
        str(AUDIO_FILE),
        "-f",
        "segment",
        "-segment_time",
        "30",
        "-ac",
        "1",
        "-ar",
        "16000",
        chunk_pattern,
      ],
      check=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
    )

    transcript = []

    for chunk in sorted(Path(temp_dir).glob("chunk_*.wav")):
      result = model.transcribe(
        [str(chunk)],
        override_config=config,
      )[0]

      text = result.text if hasattr(result, "text") else str(result)
      transcript.append(text.strip())

  print("\n" + " ".join(transcript))


if __name__ == "__main__":
  main()