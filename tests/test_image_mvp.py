from __future__ import annotations

import unittest
from pathlib import Path

from src.agents.eval_executor_agent import run_eval
from src.agents.intent_parser import parse_intent
from src.agents.tool_planner import plan_tools
from src.datasets.case_loader import load_case
from src.evaluators.rule_based_checks import run_hard_checks
from src.rubrics.rubric_loader import load_rubric
from src.rubrics.rubric_validator import validate_rubric
from src.schemas import EvalCase
from src.tools.executor import execute_tools


ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = ROOT / "configs" / "rubrics" / "image_generation_general_v1.yaml"
QUANT_RUBRIC_PATH = ROOT / "configs" / "rubrics" / "image_generation_quantitative_v1.yaml"
GOLDEN_CASE_PATH = ROOT / "cases" / "golden" / "golden_image_001.json"
REGRESSION_CASE_PATH = ROOT / "cases" / "regression" / "regression_image_missing_text_001.json"


class ImageMVPTests(unittest.TestCase):
    def test_rubric_loads_and_validates(self) -> None:
        rubric = load_rubric(RUBRIC_PATH)
        validate_rubric(rubric)
        self.assertEqual(rubric.rubric_id, "image_generation_general_v1")
        self.assertEqual(len(rubric.hard_constraints), 3)

    def test_intent_parser_extracts_required_text_and_negative_constraint(self) -> None:
        eval_case = load_case(GOLDEN_CASE_PATH)
        task_spec = parse_intent(eval_case)
        self.assertEqual(task_spec.task_type, "image_generation")
        self.assertEqual(task_spec.required_text, "SPRING SALE")
        self.assertIn("logos", task_spec.negative_constraints)

    def test_intent_parser_uses_structured_intent_when_present(self) -> None:
        eval_case = EvalCase(
            case_id="structured_intent_case",
            prompt="Generate a poster with big text and no watermarks.",
            output_modality="image",
            output={"type": "mock_image", "asset_path": "mock://structured.png", "mock_evidence": {}},
            eval_spec={
                "task_type": "image_generation",
                "intent_structured": {
                    "required_text": "HELLO",
                    "negative_constraints": ["watermark"],
                    "expected_objects": ["poster"],
                    "expected_object_counts": {"poster": 1},
                    "style": "minimal",
                },
            },
        )
        task_spec = parse_intent(eval_case)
        self.assertEqual(task_spec.required_text, "HELLO")
        self.assertEqual(task_spec.negative_constraints, ["watermark"])
        self.assertEqual(task_spec.explicit_constraints["expected_objects"], ["poster"])
        self.assertEqual(task_spec.explicit_constraints["expected_object_counts"], {"poster": 1})

    def test_intent_parser_rejects_non_image_generation_task(self) -> None:
        eval_case = EvalCase(
            case_id="bad_task_case",
            prompt="Describe this image.",
            output_modality="image",
            output={"type": "mock_image", "asset_path": "mock://bad_task.png", "mock_evidence": {}},
            eval_spec={"task_type": "image_captioning"},
        )
        with self.assertRaises(ValueError):
            parse_intent(eval_case)

    def test_tool_planner_chooses_image_ocr_and_safety(self) -> None:
        eval_case = load_case(GOLDEN_CASE_PATH)
        rubric = load_rubric(RUBRIC_PATH)
        task_spec = parse_intent(eval_case)
        plan = plan_tools(task_spec, rubric)
        self.assertEqual(plan.tools, ["image_analyzer", "ocr", "safety_checker"])

    def test_golden_case_passes(self) -> None:
        eval_case = load_case(GOLDEN_CASE_PATH)
        rubric = load_rubric(RUBRIC_PATH)
        report = run_eval(eval_case, rubric)
        self.assertTrue(report.passed)
        self.assertEqual(report.recommendation, "Accept")
        self.assertGreaterEqual(report.overall_score, 4.3)

    def test_regression_case_fails_required_text(self) -> None:
        eval_case = load_case(REGRESSION_CASE_PATH)
        rubric = load_rubric(RUBRIC_PATH)
        task_spec = parse_intent(eval_case)
        evidence = execute_tools(eval_case, task_spec, plan_tools(task_spec, rubric))
        hard_results = run_hard_checks(rubric, task_spec, evidence)

        required_text = next(item for item in hard_results if item.constraint_id == "required_text_exact")
        self.assertFalse(required_text.passed)

        report = run_eval(eval_case, rubric)
        self.assertFalse(report.passed)
        self.assertEqual(report.recommendation, "Reject")
        self.assertIn("required_text_exact", report.failure_modes)

    def test_quantitative_rubric_checks_expected_objects_and_counts(self) -> None:
        eval_case = EvalCase(
            case_id="quant_case_001",
            prompt='Create an image with exactly two cats and include text "SALE".',
            output_modality="image",
            output={
                "type": "mock_image",
                "asset_path": "mock://quant_case_001.png",
                "mock_evidence": {
                    "objects": ["cat", "cat", "poster"],
                    "prompt_alignment_signals": ["two cats"],
                    "ocr_text": "SALE",
                    "safety_flags": [],
                },
            },
            eval_spec={
                "task_type": "image_generation",
                "constraints": {
                    "expected_objects": ["cat"],
                    "expected_object_counts": {"cat": 2},
                },
            },
        )
        rubric = load_rubric(QUANT_RUBRIC_PATH)
        task_spec = parse_intent(eval_case)
        evidence = execute_tools(eval_case, task_spec, plan_tools(task_spec, rubric))
        hard_results = run_hard_checks(rubric, task_spec, evidence)
        hard_by_id = {item.constraint_id: item for item in hard_results}
        self.assertTrue(hard_by_id["required_objects_present"].passed)
        self.assertTrue(hard_by_id["object_count_match"].passed)


if __name__ == "__main__":
    unittest.main()
