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
from src.tools.executor import execute_tools


ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = ROOT / "configs" / "rubrics" / "image_generation_general_v1.yaml"
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
        self.assertEqual(task_spec.required_text, "SPRING SALE")
        self.assertIn("logos", task_spec.negative_constraints)

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


if __name__ == "__main__":
    unittest.main()
