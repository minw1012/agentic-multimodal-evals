from __future__ import annotations

import os

from src.tools.mask2former_image_analyzer import maybe_build_mask2former_image_analyzer
from src.tools.mock_image_tools import MockImageAnalyzer, MockOCR, MockSafetyChecker


def _select_image_analyzer():
    backend = os.getenv("EVAL_IMAGE_ANALYZER_BACKEND", "auto").strip().lower()
    if backend == "mock":
        return MockImageAnalyzer()

    if backend in {"auto", "mask2former"}:
        mask2former = maybe_build_mask2former_image_analyzer()
        if mask2former is not None:
            return mask2former
        if backend == "mask2former":
            raise RuntimeError(
                "EVAL_IMAGE_ANALYZER_BACKEND=mask2former requires optional dependencies. "
                "Install mmdet + torch and provide the checkpoint path."
            )

    return MockImageAnalyzer()


TOOL_REGISTRY = {
    "image_analyzer": _select_image_analyzer(),
    "ocr": MockOCR(),
    "safety_checker": MockSafetyChecker(),
}
