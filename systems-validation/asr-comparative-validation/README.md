# ASR Comparative Validation

A lightweight environment for testing and comparing automatic speech recognition models, inference backends, and inference approaches under the same conditions.

## Scope

* Test multiple ASR implementations
* Use the same audio samples
* Check CPU and GPU support
* Compare transcripts and runtime

## Requirements

* Python 3.10+
* FFmpeg
* PyTorch
* CUDA-compatible NVIDIA GPU
* WSL2 or Linux

## Setup

Install system dependencies:

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv
```

Create and activate a virtual environment:

```bash
python3 -m venv ~/asr-playground
source ~/asr-playground/bin/activate
```
### Whisper

Install Python dependencies:

```bash
python -m pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
pip install openai-whisper
```

### Faster Whsiper

```bash
python -m pip install -U \
  faster-whisper \
  nvidia-cublas-cu12 \
  "nvidia-cudnn-cu12==9.*"

export LD_LIBRARY_PATH="$(python -c 'import os, nvidia.cublas.lib, nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'):$LD_LIBRARY_PATH"
```

### Nemotron 3.5 ASR

```bash
python -m pip install -U Cython packaging
python -m pip install torch torchaudio \
  --index-url https://download.pytorch.org/whl/cu126

# python -m pip install "nemo_toolkit[asr]" rnnt_bpe_models_prompt missing
python -m pip install \
  "nemo_toolkit[asr] @ git+https://github.com/NVIDIA-NeMo/NeMo.git@main"
```

## Run

```bash
python openai_whisper.py
python fst_whisper.py
```



## Verify CUDA

```bash
python - <<'PY'
import torch

print("CUDA available:", torch.cuda.is_available())
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")
print("CUDA version:", torch.version.cuda)
PY
```

Expected output:

```text
CUDA available: True
GPU: XXXXXX XXX XXXX
CUDA version: XX
```
