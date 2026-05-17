from __future__ import annotations

from src.schemas import EvalCase, EvidenceBundle, TaskSpec, ToolPlan
from src.tools.registry import TOOL_REGISTRY


def execute_tools(eval_case: EvalCase, task_spec: TaskSpec, tool_plan: ToolPlan) -> EvidenceBundle:
    bundle = EvidenceBundle(case_id=eval_case.case_id, modality=eval_case.output_modality)
    for tool_name in tool_plan.tools:
        tool = TOOL_REGISTRY[tool_name]
        bundle.evidence[tool_name] = tool.run(eval_case, task_spec)
        bundle.tool_versions[tool_name] = tool.version
        bundle.references.append(
            {
                "id": tool_name,
                "tool": tool_name,
                "version": tool.version,
                "summary": f"Evidence produced by {tool_name}",
            }
        )
    return bundle
