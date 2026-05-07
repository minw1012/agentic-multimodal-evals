# Agent-Based Multimodal Eval Demo

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

## Quick Start

Run the built-in image case:

```bash
python3 runner.py \
  --case cases/golden/golden_image_001.json \
  --rubric configs/rubrics/image_generation_general_v1.yaml
```

Run a public DiffusionDB sample:

```bash
python3 runner.py \
  --case cases/golden/diffusiondb_geodesic_landscape_001.json \
  --rubric configs/rubrics/generated_diffusiondb_art_v1.yaml
```

Example output:

```text
Case: golden_image_001
Pass: true
Overall score: 4.95
Recommendation: Accept
Report saved to reports/golden_image_001/result.json
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

## Make It Discoverable

To help more people find the repo:

```text
1. Add a short GitHub repo description:
   Agent-based multimodal eval demo with rubrics, evidence extraction, and traceable reports.

2. Add GitHub topics:
   llm-evaluation
   multimodal-evaluation
   agentic-evals
   evals
   rubric
   vlm
   ocr
   diffusiondb
   python

3. Keep the README searchable:
   mention LLM eval, multimodal eval, rubric generation, evidence extraction, JSON reports.

4. Share a concrete demo:
   "Run one DiffusionDB image eval and inspect the report."

5. Add a good social preview image:
   use docs/assets/schema.png as the repository social preview.
```

## Test

```bash
python3 -m unittest discover tests
```
