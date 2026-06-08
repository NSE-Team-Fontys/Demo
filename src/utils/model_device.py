from __future__ import annotations

import logging
import os
from typing import Optional

import torch

logger = logging.getLogger(__name__)

_CUDA_DEVICE_ALIASES = {"cuda", "cuda:0"}
_ROCM_DEVICE_ALIASES = {"rocm", "rocm:0", "hip", "hip:0"}


def _mps_available() -> bool:
    mps_backend = getattr(torch.backends, "mps", None)
    if mps_backend is None:
        return False
    is_built = getattr(mps_backend, "is_built", lambda: False)
    return bool(is_built() and mps_backend.is_available())


def is_rocm_pytorch() -> bool:
    """Return whether this PyTorch build uses AMD ROCm/HIP."""
    return bool(getattr(torch.version, "hip", None))


def _canonical_device(device: str) -> str:
    normalized = str(device).strip().lower()
    if normalized in _CUDA_DEVICE_ALIASES | _ROCM_DEVICE_ALIASES:
        # PyTorch intentionally exposes ROCm devices through the CUDA API.
        return "cuda"
    return normalized


def get_model_device() -> str:
    """
    Return the preferred PyTorch device for local models.

    Set MODEL_DEVICE=cpu|cuda|rocm|hip|mps to force a device. ROCm/HIP aliases
    resolve to ``cuda``, which is PyTorch's device name for AMD GPUs.
    """
    requested = os.environ.get("MODEL_DEVICE", "auto").strip().lower()

    if requested in _ROCM_DEVICE_ALIASES:
        if is_rocm_pytorch() and torch.cuda.is_available():
            return "cuda"
        logger.warning(
            "MODEL_DEVICE=%s requested but the installed PyTorch build has no "
            "available ROCm/HIP device; using CPU.",
            requested,
        )
        return "cpu"

    if requested in _CUDA_DEVICE_ALIASES:
        if torch.cuda.is_available():
            return "cuda"
        logger.warning("MODEL_DEVICE=%s requested but CUDA is unavailable; using CPU.", requested)
        return "cpu"

    if requested == "mps":
        if _mps_available():
            return "mps"
        logger.warning("MODEL_DEVICE=mps requested but Apple MPS is unavailable; using CPU.")
        return "cpu"

    if requested == "cpu":
        return "cpu"

    if requested not in {"", "auto"}:
        logger.warning("Unknown MODEL_DEVICE=%s; using auto device selection.", requested)

    if torch.cuda.is_available():
        return "cuda"
    if _mps_available():
        return "mps"
    return "cpu"


def get_pipeline_device(device: Optional[str] = None):
    device = _canonical_device(device or get_model_device())
    if device == "cuda":
        return 0
    if device == "mps":
        return torch.device("mps")
    return -1


def describe_model_device(device: Optional[str] = None) -> str:
    device = _canonical_device(device or get_model_device())
    if device == "cuda":
        if is_rocm_pytorch():
            return f"AMD GPU (ROCm/HIP {torch.version.hip} via cuda:0)"
        return "NVIDIA GPU (CUDA via cuda:0)"
    if device == "mps":
        return "Apple GPU (mps)"
    return "CPU"
