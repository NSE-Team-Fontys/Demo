from __future__ import annotations

import logging
import os
from typing import Optional

import torch

logger = logging.getLogger(__name__)


def _mps_available() -> bool:
    mps_backend = getattr(torch.backends, "mps", None)
    if mps_backend is None:
        return False
    is_built = getattr(mps_backend, "is_built", lambda: False)
    return bool(is_built() and mps_backend.is_available())


def get_model_device() -> str:
    """
    Return the preferred PyTorch device for local models.

    Set MODEL_DEVICE=cpu|cuda|mps to force a device; otherwise auto mode uses
    CUDA first, then Apple Silicon MPS, then CPU.
    """
    requested = os.environ.get("MODEL_DEVICE", "auto").strip().lower()

    if requested in {"cuda", "cuda:0"}:
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
    device = device or get_model_device()
    if device == "cuda":
        return 0
    if device == "mps":
        return torch.device("mps")
    return -1


def describe_model_device(device: Optional[str] = None) -> str:
    device = device or get_model_device()
    if device == "cuda":
        return "GPU (cuda:0)"
    if device == "mps":
        return "Apple GPU (mps)"
    return "CPU"
