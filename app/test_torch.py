import torch

print("Torch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
x = torch.rand(2, 3)
print("Tensor:", x)
