from __future__ import annotations

from src.schemas import EvalCase, TaskSpec


class MockImageAnalyzer:
    name = "image_analyzer"
    version = "mock-image-analyzer-v1"

    def run(self, eval_case: EvalCase, task_spec: TaskSpec) -> dict:
        mock = eval_case.output.get("mock_evidence", {})
        return {
            "caption": mock.get("caption", "Generated image matching the requested scene."),
            "objects": mock.get("objects", []),
            "style": mock.get("style", task_spec.style),
            "artifacts": mock.get("artifacts", []),
            "composition_quality": mock.get("composition_quality", "good"),
            "prompt_alignment_signals": mock.get("prompt_alignment_signals", []),
        }


class MockOCR:
    name = "ocr"
    version = "mock-ocr-v1"

    def run(self, eval_case: EvalCase, task_spec: TaskSpec) -> dict:
        mock = eval_case.output.get("mock_evidence", {})
        text = mock.get("ocr_text", "")
        required = task_spec.required_text
        return {
            "text": text,
            "confidence": mock.get("ocr_confidence", 0.95 if text else 0.0),
            "required_text": required,
            "required_text_present": bool(required and required.lower() in text.lower()),
            "legibility": mock.get("text_legibility", "legible" if text else "not_applicable"),
        }


class MockSafetyChecker:
    name = "safety_checker"
    version = "mock-safety-checker-v1"

    def run(self, eval_case: EvalCase, task_spec: TaskSpec) -> dict:
        mock = eval_case.output.get("mock_evidence", {})
        flags = mock.get("safety_flags", [])
        return {
            "safe": len(flags) == 0,
            "flags": flags,
            "risk_level": mock.get("risk_level", "low" if not flags else "high"),
        }


TOOL_REGISTRY = {
    "image_analyzer": MockImageAnalyzer(),
    "ocr": MockOCR(),
    "safety_checker": MockSafetyChecker(),
}
