# Agent-Based Multimodal Eval Demo

An image-first demo of an agentic evaluation system for multimodal model outputs.

<img src="docs/assets/schema.png" alt="Agent-based multimodal evaluation system architecture" width="100%">

## Core Idea

```text
Do not ask an LLM judge to score by intuition alone.

User task + model output
  -> extract structured evidence
  -> evaluate evidence against an explicit rubric
  -> produce a traceable JSON report
```

## What This Repo Implements

```text
Rubric authoring
  User quality requirements
  -> rubric_generator.py
  -> draft rubric
  -> human review / edit
```

```text
Image eval execution
  Eval case
  -> intent parser
  -> tool planner
  -> image analyzer + OCR + safety checker
  -> rule-based checks + soft scores
  -> report JSON
```

```text
Dataset path
  DiffusionDB sample
  -> dataset_importer.py
  -> eval case
  -> eval report
```

## Run

```bash
python3 runner.py \
  --case cases/golden/golden_image_001.json \
  --rubric configs/rubrics/image_generation_general_v1.yaml
```

```bash
python3 runner.py \
  --case cases/golden/diffusiondb_geodesic_landscape_001.json \
  --rubric configs/rubrics/generated_diffusiondb_art_v1.yaml
```

## Generate A Rubric

```bash
python3 rubric_generator.py \
  --requirements "Evaluate image outputs for prompt alignment, visual coherence, safety, and user acceptability." \
  --rubric-id custom_image_art_v1 \
  --name "Custom Image Art Rubric" \
  --output configs/rubrics/custom_image_art_v1.yaml
```

## Import Dataset Sample

```bash
python3 dataset_importer.py \
  --dataset diffusiondb \
  --output cases/golden/diffusiondb_geodesic_landscape_001.json
```

DiffusionDB:

```text
https://huggingface.co/datasets/poloclub/diffusiondb
https://poloclub.github.io/diffusiondb/
```

## Test

```bash
python3 -m unittest discover tests
```
