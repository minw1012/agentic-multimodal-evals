from __future__ import annotations

from src.agents.intent_parser import parse_intent
from src.agents.tool_planner import plan_tools
from src.evaluators.mock_llm_judge import score_soft_dimensions
from src.evaluators.rule_based_checks import run_hard_checks
from src.evaluators.score_aggregator import aggregate_score, final_decision
from src.schemas import EvalCase, EvalReport, Rubric
from src.tools.executor import execute_tools


JUDGE_VERSION = "mock-evidence-grounded-judge-v1"


def run_eval(eval_case: EvalCase, rubric: Rubric) -> EvalReport:
    task_spec = parse_intent(eval_case)
    tool_plan = plan_tools(task_spec, rubric)
    evidence_bundle = execute_tools(eval_case, task_spec, tool_plan)
    hard_results = run_hard_checks(rubric, task_spec, evidence_bundle)
    soft_scores = score_soft_dimensions(rubric, task_spec, evidence_bundle)
    overall_score = aggregate_score(soft_scores)
    passed, recommendation, action, failure_modes = final_decision(rubric, hard_results, soft_scores, overall_score)

    return EvalReport(
        case_id=eval_case.case_id,
        passed=passed,
        overall_score=overall_score,
        recommendation=recommendation,
        hard_constraint_results=hard_results,
        soft_scores=soft_scores,
        failure_modes=failure_modes,
        recommended_action=action,
        evidence=evidence_bundle.evidence,
        evidence_references=evidence_bundle.references,
        rubric_version=f"{rubric.rubric_id}@{rubric.version}",
        judge_version=JUDGE_VERSION,
        tool_versions=evidence_bundle.tool_versions,
        metadata=eval_case.metadata,
    )
