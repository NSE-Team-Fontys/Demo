from __future__ import annotations

import os
import unittest
from unittest import mock

from src.utils import model_device


class ModelDeviceTests(unittest.TestCase):
    def test_auto_detects_rocm_through_pytorch_cuda_api(self) -> None:
        with (
            mock.patch.dict(os.environ, {"MODEL_DEVICE": "auto"}),
            mock.patch.object(model_device.torch.cuda, "is_available", return_value=True),
            mock.patch.object(model_device.torch.version, "hip", "7.2.1"),
        ):
            self.assertEqual(model_device.get_model_device(), "cuda")
            self.assertEqual(model_device.get_pipeline_device(), 0)
            self.assertIn("AMD GPU", model_device.describe_model_device())
            self.assertIn("ROCm/HIP 7.2.1", model_device.describe_model_device())

    def test_rocm_override_resolves_to_cuda_device(self) -> None:
        with (
            mock.patch.dict(os.environ, {"MODEL_DEVICE": "rocm"}),
            mock.patch.object(model_device.torch.cuda, "is_available", return_value=True),
            mock.patch.object(model_device.torch.version, "hip", "7.2.1"),
        ):
            self.assertEqual(model_device.get_model_device(), "cuda")
            self.assertEqual(model_device.get_pipeline_device("hip:0"), 0)

    def test_rocm_override_falls_back_without_rocm_pytorch(self) -> None:
        with (
            mock.patch.dict(os.environ, {"MODEL_DEVICE": "rocm"}),
            mock.patch.object(model_device.torch.cuda, "is_available", return_value=True),
            mock.patch.object(model_device.torch.version, "hip", None),
        ):
            with self.assertLogs(model_device.logger, level="WARNING"):
                self.assertEqual(model_device.get_model_device(), "cpu")

    def test_cuda_build_keeps_nvidia_label(self) -> None:
        with (
            mock.patch.object(model_device.torch.cuda, "is_available", return_value=True),
            mock.patch.object(model_device.torch.version, "hip", None),
        ):
            self.assertEqual(
                model_device.describe_model_device("cuda"),
                "NVIDIA GPU (CUDA via cuda:0)",
            )

    def test_auto_keeps_mps_fallback(self) -> None:
        with (
            mock.patch.dict(os.environ, {"MODEL_DEVICE": "auto"}),
            mock.patch.object(model_device.torch.cuda, "is_available", return_value=False),
            mock.patch.object(model_device, "_mps_available", return_value=True),
        ):
            self.assertEqual(model_device.get_model_device(), "mps")
            self.assertEqual(
                model_device.describe_model_device("mps"),
                "Apple GPU (mps)",
            )


if __name__ == "__main__":
    unittest.main()
