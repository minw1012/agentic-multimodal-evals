from __future__ import annotations

import argparse
from pathlib import Path

from src.agents.eval_executor_agent import run_eval
from src.datasets.case_loader import load_case
from src.reporting.report_writer import write_report
from src.rubrics.rubric_loader import load_rubric
from src.rubrics.rubric_validator import validate_rubric


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a multimodal eval case.")
    parser.add_argument("--case", required=True, help="Path to an eval case JSON file.")
    parser.add_argument("--rubric", required=True, help="Path to a rubric YAML/JSON file.")
    parser.add_argument("--reports-dir", default="reports", help="Directory where reports are written.")
    args = parser.parse_args()

    eval_case = load_case(args.case)
    rubric = load_rubric(args.rubric)
    validate_rubric(rubric)

    report = run_eval(eval_case, rubric)
    report_path = write_report(report, Path(args.reports_dir))

    print(f"Case: {report.case_id}")
    print(f"Pass: {str(report.passed).lower()}")
    print(f"Overall score: {report.overall_score:.2f}")
    print(f"Recommendation: {report.recommendation}")
    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()
