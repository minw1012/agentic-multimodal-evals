# Rubric-Driven Multimodal Eval Agent for Image Generation

This repo is a small, runnable demo of an agent-based evaluation system for multimodal model outputs. It starts with image generation, but the architecture is designed to extend to text, audio, and video.

<img src="docs/assets/schema.png" alt="Agent-based multimodal evaluation system architecture" width="100%">

## Why This Exists

Most simple eval demos ask an LLM judge a broad question like:

```text
Is this output good?
```

That is hard to trust because the judge may score from intuition. This demo uses a more inspectable flow:

```text
Prompt + model output
  -> parse user intent
  -> load or generate a rubric
  -> choose evidence tools
  -> extract structured evidence
  -> run deterministic hard checks
  -> score soft quality dimensions
  -> write a traceable report
```

The important idea is: **rubrics are explicit configuration, and judges score from evidence.**

## What Works Now

| You can... | What happens |
|---|---|
| Generate a rubric from quality requirements | The system creates a draft rubric with hard constraints, soft score dimensions, weights, and thresholds. |
| Run an image eval case | The runner parses the prompt, plans tools, extracts evidence, checks constraints, scores quality, and writes a JSON report. |
| Evaluate a public dataset sample | A DiffusionDB text-to-image sample is converted into the same eval-case format and run through the same pipeline. |
| Inspect why a case passed or failed | The report includes hard-check results, soft scores, failure modes, evidence, rubric version, and tool versions. |

Current tool implementations are mocks, but they sit behind replaceable interfaces:

```text
mock OCR / mock image analyzer / mock safety checker
  -> same evidence schema
  -> replace later with real OCR, VLM, safety, audio, or video tools
```

Intent parsing now follows:

```text
LLM structured parse (optional) -> schema normalization -> regex fallback
```

You can control parser behavior:

```bash
export EVAL_INTENT_PARSER_BACKEND=regex   # force regex-only mode
export EVAL_INTENT_PARSER_BACKEND=openai  # call OpenAI Responses API (requires OPENAI_API_KEY)
```

## Quick Start

Run the built-in image case:

```bash
python3 runner.py \
  --case cases/golden/golden_image_001.json \
  --rubric configs/rubrics/image_generation_general_v1.yaml

python3 runner.py \
  --case cases/golden/golden_image_001.json \
  --rubric configs/rubrics/image_generation_quantitative_v1.yaml
```

Run a public DiffusionDB sample:

```bash
python3 runner.py \
  --case cases/golden/diffusiondb_geodesic_landscape_001.json \
  --rubric configs/rubrics/generated_diffusiondb_art_v1.yaml
```

## Demo

Built-in image eval:

```console
$ python3 runner.py \
    --case cases/golden/golden_image_001.json \
    --rubric configs/rubrics/image_generation_general_v1.yaml

Case: golden_image_001
Pass: true
Overall score: 4.95
Recommendation: Accept
Report saved to reports/golden_image_001/result.json
```

Public DiffusionDB sample:

```console
$ python3 runner.py \
    --case cases/golden/diffusiondb_geodesic_landscape_001.json \
    --rubric configs/rubrics/generated_diffusiondb_art_v1.yaml

Case: diffusiondb_geodesic_landscape_001
Pass: true
Overall score: 4.95
Recommendation: Accept
Report saved to reports/diffusiondb_geodesic_landscape_001/result.json
```

Report preview:

```json
{
  "case_id": "golden_image_001",
  "passed": true,
  "overall_score": 4.95,
  "recommendation": "Accept",
  "failure_modes": [],
  "rubric_version": "image_generation_general_v1@1.0",
  "tool_versions": {
    "image_analyzer": "mock-image-analyzer-v1",
    "ocr": "mock-ocr-v1",
    "safety_checker": "mock-safety-checker-v1"
  }
}
```

## Generate A Rubric

Create a draft rubric from user requirements:

```bash
python3 rubric_generator.py \
  --requirements "Evaluate image outputs for prompt alignment, visual coherence, safety, and user acceptability." \
  --rubric-id custom_image_art_v1 \
  --name "Custom Image Art Rubric" \
  --output configs/rubrics/custom_image_art_v1.yaml
```

The generated rubric is intentionally marked as a draft. A human should review/edit it before using it as a reproducible evaluation standard.

## Import Dataset Sample

Generate the included DiffusionDB eval case:

```bash
python3 dataset_importer.py \
  --dataset diffusiondb \
  --output cases/golden/diffusiondb_geodesic_landscape_001.json
```

DiffusionDB is a public text-to-image prompt/image dataset:

```text
https://huggingface.co/datasets/poloclub/diffusiondb
https://poloclub.github.io/diffusiondb/
```

## Report Shape

Each run writes a JSON report with:

```text
pass/fail
overall score
recommendation
hard constraint results
soft scores
failure modes
structured evidence
tool versions
rubric version
metadata
```

## Test

```bash
python3 -m unittest discover tests
```
