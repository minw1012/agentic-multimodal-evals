# Agent-Based Multimodal Eval MVP

This is a Phase 1 implementation of an agent-based evaluation system, starting with image outputs.

![Agent-based multimodal eval architecture](docs/assets/agent_eval_system.png)

The key idea is simple: do not let a judge model score by intuition alone. First convert the output into structured evidence, then evaluate that evidence against an explicit, portable rubric.

The MVP intentionally uses mock image, OCR, and safety tools. The interfaces are shaped so real OCR, VLM, and safety tools can replace the mocks later.

## Current Image MVP Flow

```mermaid
flowchart LR
    A[Image Eval Case<br/>prompt + output + metadata] --> B[Intent Parser<br/>required text, style, negatives]
    B --> C[Rubric Loader<br/>image_generation_general_v1]
    C --> D[Tool Planner<br/>image analyzer + OCR + safety]
    D --> E[Mock Evidence Extraction]
    E --> F[Rule-Based Hard Checks<br/>safety, exact text, forbidden objects]
    E --> G[Evidence-Grounded Soft Scoring<br/>alignment, quality, text, safety]
    F --> H[Score Aggregator]
    G --> H
    H --> I[JSON Eval Report<br/>pass/fail, score, failures, recommendation]
```

## Target System Architecture

```mermaid
flowchart LR
    A[Input / Eval Case<br/>prompt, output, metadata] --> B[Eval Agent Orchestration]
    B --> B1[Intent Parser]
    B --> B2[Rubric Generator<br/>human-approved templates]
    B --> B3[Tool Planner]
    B --> B4[Execution Orchestrator]

    B4 --> C[Evidence Extraction]
    C --> C1[Text Analyzer]
    C --> C2[OCR]
    C --> C3[Image / VLM Analyzer]
    C --> C4[ASR]
    C --> C5[Video Analyzer]
    C --> C6[Safety Checker]
    C --> C7[Structured Evidence]

    C7 --> D[Judge / Scoring Layer]
    D --> D1[Rule-Based Checks]
    D --> D2[LLM Judge]
    D --> D3[Eval Result]

    D3 --> E[Result Storage & Analysis]
    E --> E1[Report Store]
    E --> E2[Dashboard]
    E --> E3[Experiment Tracking]

    E --> F[Continuous Improvement Loop]
    F --> F1[Human Review / Calibration]
    F --> F2[User Behavior Signals]
    F --> F3[Update Dataset & Rubric]
    F3 --> B
```

## Run

```bash
cd multimodal_eval_agent
python3 runner.py \
  --case cases/golden/golden_image_001.json \
  --rubric configs/rubrics/image_generation_general_v1.yaml
```

Expected output:

```text
Case: golden_image_001
Pass: true
Overall score: 4.95
Recommendation: Accept
Report saved to reports/golden_image_001/result.json
```

Run a regression case:

```bash
python3 runner.py \
  --case cases/regression/regression_image_missing_text_001.json \
  --rubric configs/rubrics/image_generation_general_v1.yaml
```

## Test

```bash
python3 -m unittest discover tests
```

## Files

- `configs/rubrics/image_generation_general_v1.yaml`: portable rubric config.
- `cases/golden/golden_image_001.json`: passing image eval case.
- `cases/regression/regression_image_missing_text_001.json`: hard failure for missing exact text.
- `src/agents/`: intent parsing, tool planning, and eval orchestration.
- `src/tools/`: mock evidence extraction tools.
- `src/evaluators/`: hard checks and soft score aggregation.
- `src/reporting/`: report writer.
