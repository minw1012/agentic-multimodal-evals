# Agent-Based Multimodal Eval Demo

Image-first demo for an agentic evaluation system based on `agent_based_multimodal_eval_system_v2.md`.

![Agent-based multimodal eval flow](docs/assets/agent_eval_flow.svg)

## Auto Eval Flow

```text
Eval Case
  -> Intent Parser
  -> Rubric Generator / Rubric Loader
  -> Tool Planner
  -> Evidence Tools
  -> Rule-Based Checks
  -> Evidence-Grounded Scoring
  -> JSON Report
```

## What Is Implemented

```text
User quality requirements
  -> rubric_generator.py
  -> draft rubric YAML
  -> human review / edit
  -> runner.py
```

```text
Public dataset sample
  -> dataset_importer.py
  -> eval case JSON
  -> runner.py
  -> reports/<case_id>/result.json
```

```text
Image output
  -> mock image analyzer
  -> mock OCR
  -> mock safety checker
  -> hard constraints + soft scores
```

## Quick Start

Run the built-in image case:

```bash
python3 runner.py \
  --case cases/golden/golden_image_001.json \
  --rubric configs/rubrics/image_generation_general_v1.yaml
```

Run the DiffusionDB public dataset sample:

```bash
python3 runner.py \
  --case cases/golden/diffusiondb_geodesic_landscape_001.json \
  --rubric configs/rubrics/generated_diffusiondb_art_v1.yaml
```

Generate a draft rubric from user requirements:

```bash
python3 rubric_generator.py \
  --requirements "Evaluate image outputs for prompt alignment, visual coherence, safety, and user acceptability." \
  --rubric-id custom_image_art_v1 \
  --name "Custom Image Art Rubric" \
  --output configs/rubrics/custom_image_art_v1.yaml
```

Import the DiffusionDB sample case:

```bash
python3 dataset_importer.py \
  --dataset diffusiondb \
  --output cases/golden/diffusiondb_geodesic_landscape_001.json
```

## Inputs And Outputs

| Layer | File |
|---|---|
| Rubric | `configs/rubrics/image_generation_general_v1.yaml` |
| Generated rubric | `configs/rubrics/generated_diffusiondb_art_v1.yaml` |
| Golden case | `cases/golden/golden_image_001.json` |
| Public dataset case | `cases/golden/diffusiondb_geodesic_landscape_001.json` |
| Regression case | `cases/regression/regression_image_missing_text_001.json` |
| Report | `reports/<case_id>/result.json` |

## Public Dataset

```text
DiffusionDB
  -> text-to-image prompt/image dataset
  -> Hugging Face: https://huggingface.co/datasets/poloclub/diffusiondb
  -> Project: https://poloclub.github.io/diffusiondb/
```

## Test

```bash
python3 -m unittest discover tests
```
