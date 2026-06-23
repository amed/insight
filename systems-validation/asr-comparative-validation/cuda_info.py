import torch

def print_cuda_info() -> None:
  available = torch.cuda.is_available()

  print("CUDA available:", available)
  print("GPU:", torch.cuda.get_device_name(0) if available else "None")
  print("CUDA version:", torch.version.cuda)
  print("---------", flush=True)