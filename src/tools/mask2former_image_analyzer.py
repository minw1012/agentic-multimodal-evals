from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.schemas import EvalCase, TaskSpec


DEFAULT_MODEL_NAME = "mask2former_swin-s-p4-w7-224_lsj_8x2_50e_coco"


class Mask2FormerImageAnalyzer:
    name = "image_analyzer"
    version = "mask2former-image-analyzer-v1"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        model_path: str | Path = "./models",
        model_config: str | Path | None = None,
        threshold: float = 0.3,
        max_objects: int = 16,
    ) -> None:
        self.model_name = model_name
        self.model_path = Path(model_path)
        self.model_config = Path(model_config) if model_config else None
        self.threshold = threshold
        self.max_objects = max_objects

        self._model: Any = None
        self._classnames: list[str] | None = None
        self._inference_detector: Any = None

    def run(self, eval_case: EvalCase, task_spec: TaskSpec) -> dict:
        mock = eval_case.output.get("mock_evidence", {})
        dataset_annotations = eval_case.output.get("dataset_annotations", {})
        evidence = {
            "caption": mock.get("caption", "Generated image matching the requested scene."),
            "objects": mock.get("objects", []),
            "style": mock.get("style", task_spec.style),
            "artifacts": mock.get("artifacts", []),
            "composition_quality": mock.get("composition_quality", "good"),
            "prompt_alignment_signals": mock.get("prompt_alignment_signals", []),
            "dataset_annotations": dataset_annotations,
            "detections": [],
            "detector_backend": "mask2former",
            "detector_status": "fallback_to_mock",
        }

        image_path = _resolve_asset_path(eval_case.output.get("asset_path"))
        if image_path is None:
            evidence["detector_message"] = "No local image path was available for detection."
            return evidence

        try:
            detections = self._detect_objects(image_path)
        except Exception as exc:  # pragma: no cover - exercised when dependency/model is missing
            evidence["detector_message"] = f"Object detection failed: {exc}"
            return evidence

        evidence["detections"] = detections
        evidence["objects"] = [item["class"] for item in detections]
        if not evidence["prompt_alignment_signals"]:
            evidence["prompt_alignment_signals"] = evidence["objects"][:3]
        evidence["detector_status"] = "ok"
        evidence["detector_message"] = f"Detected {len(detections)} objects from {image_path}."
        return evidence

    def _detect_objects(self, image_path: Path) -> list[dict[str, Any]]:
        self._ensure_model_loaded()
        raw_result = self._inference_detector(self._model, str(image_path))
        classnames = self._classnames or []

        # mmdetection 2.x output: tuple/list with per-class bbox arrays.
        if isinstance(raw_result, tuple):
            raw_result = raw_result[0]
        if isinstance(raw_result, list):
            detections: list[dict[str, Any]] = []
            for class_index, class_boxes in enumerate(raw_result):
                if class_index >= len(classnames):
                    continue
                for box in class_boxes[: self.max_objects]:
                    score = float(box[4]) if len(box) > 4 else 1.0
                    if score < self.threshold:
                        continue
                    detections.append(
                        {
                            "class": classnames[class_index],
                            "score": round(score, 4),
                            "bbox": [round(float(coord), 2) for coord in box[:4]],
                        }
                    )
            detections.sort(key=lambda item: item["score"], reverse=True)
            return detections[: self.max_objects]

        # mmdetection 3.x output: DetDataSample with pred_instances.
        pred_instances = getattr(raw_result, "pred_instances", None)
        if pred_instances is None:
            raise RuntimeError("Unsupported detector output format.")

        labels = _to_list(getattr(pred_instances, "labels", []))
        scores = _to_list(getattr(pred_instances, "scores", []))
        boxes = _to_list(getattr(pred_instances, "bboxes", []))

        detections = []
        for label, score, box in zip(labels, scores, boxes):
            score_value = float(score)
            if score_value < self.threshold:
                continue
            class_index = int(label)
            class_name = classnames[class_index] if class_index < len(classnames) else f"class_{class_index}"
            detections.append(
                {
                    "class": class_name,
                    "score": round(score_value, 4),
                    "bbox": [round(float(coord), 2) for coord in box[:4]],
                }
            )

        detections.sort(key=lambda item: item["score"], reverse=True)
        return detections[: self.max_objects]

    def _ensure_model_loaded(self) -> None:
        if self._model is not None:
            return

        import torch
        import mmdet
        from mmdet.apis import inference_detector, init_detector

        device = "cuda" if torch.cuda.is_available() else "cpu"
        config_path = self.model_config or (
            Path(mmdet.__file__).resolve().parent
            / "../configs/mask2former/mask2former_swin-s-p4-w7-224_lsj_8x2_50e_coco.py"
        )
        checkpoint_path = self.model_path / f"{self.model_name}.pth"
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"Mask2Former checkpoint not found at {checkpoint_path}. "
                "Download it and set EVAL_MASK2FORMER_MODEL_PATH."
            )

        self._model = init_detector(str(config_path), str(checkpoint_path), device=device)
        self._inference_detector = inference_detector
        self._classnames = _extract_classnames(self._model)


def maybe_build_mask2former_image_analyzer() -> Mask2FormerImageAnalyzer | None:
    try:
        # Validate optional dependency once at setup.
        import mmdet  # noqa: F401
        import torch  # noqa: F401
    except Exception:
        return None

    model_name = os.getenv("EVAL_MASK2FORMER_MODEL", DEFAULT_MODEL_NAME)
    model_path = os.getenv("EVAL_MASK2FORMER_MODEL_PATH", "./models")
    model_config = os.getenv("EVAL_MASK2FORMER_MODEL_CONFIG")
    threshold = float(os.getenv("EVAL_MASK2FORMER_THRESHOLD", "0.3"))
    max_objects = int(os.getenv("EVAL_MASK2FORMER_MAX_OBJECTS", "16"))
    return Mask2FormerImageAnalyzer(
        model_name=model_name,
        model_path=model_path,
        model_config=model_config,
        threshold=threshold,
        max_objects=max_objects,
    )


def _extract_classnames(model: Any) -> list[str]:
    classes = getattr(model, "CLASSES", None)
    if classes:
        return list(classes)

    dataset_meta = getattr(model, "dataset_meta", None)
    if isinstance(dataset_meta, dict) and dataset_meta.get("classes"):
        return list(dataset_meta["classes"])

    return []


def _to_list(value: Any) -> list[Any]:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value)


def _resolve_asset_path(asset_path: str | None) -> Path | None:
    if not asset_path or asset_path.startswith(("mock://", "hf://", "http://", "https://")):
        return None

    path = Path(asset_path).expanduser()
    if not path.is_absolute():
        root = Path(os.getenv("EVAL_ASSET_ROOT", ".")).expanduser()
        path = root / path
    path = path.resolve()
    if not path.exists():
        return None
    return path
