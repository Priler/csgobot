import torch

# Check if CUDA (NVIDIA GPU) is available
if torch.cuda.is_available():
    print("GPU (CUDA) is available in PyTorch.")
    print(f"Number of GPUs available: {torch.cuda.device_count()}")
    print(f"Current GPU name: {torch.cuda.get_device_name(0)}") # Get the name of the first GPU
else:
    print("PyTorch is running on CPU. GPU (CUDA) is not available.")