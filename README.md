# Claypeus (Local Week 1)

Local setup for Week 1 of the Claypeus indirect prompt injection defense framework.
Targets: 10-column dataset schema, validation utils, converters (InjecAgent, deepset), tests, docs.
No Git/remote repo operations performed.

## Project Structure

```
claypeus/
├── pyproject.toml              # Project metadata + pytest config
├── requirements.txt            # pandas, pytest, datasets
├── .gitignore
├── README.md                   # This file
├── data/
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── dataset_utils.py    # Canonical schema + validation utilities
│   │   ├── convert_deepset.py  # Reproducible converter (Hugging Face)
│   │   └── convert_injecagent.py  # Defensive converter (remote raw files)
│   ├── processed/
│   │   ├── usman_deepset.csv       # 662 rows, valid
│   │   └── usman_injecagent.csv   # 1054 rows, valid
│   └── templates/
│       └── hard_negatives.json     # 5 harmless templates
└── tests/
    ├── __init__.py
    └── test_datasets.py       # Unit tests (9 passed)
```

## Week 1 Deliverables

- `data/scripts/dataset_utils.py` - schema + validation utilities
- `data/scripts/convert_deepset.py` - reproducible converter (HF)
- `data/scripts/convert_injecagent.py` - converter loading remote raw files
- `data/processed/usman_deepset.csv` - generated (662 rows, valid)
- `data/processed/usman_injecagent.csv` - generated (1054 rows, valid)
- `tests/test_datasets.py` - unit tests (9 passed)
- `pyproject.toml`, `requirements.txt`, `.gitignore`

## Processed Datasets

### usman_deepset.csv (662 rows)
- Source: Hugging Face `deepset/prompt-injections`
- Field mapping: `text` -> `external_content`; label 0->clean, 1->injected
- `user_instruction`: synthetic generic task ("Classify whether the following text contains a prompt injection.") applied uniformly as preprocessing convention
- No span annotations available -> spans/offsets empty; `injection_category` set to `instruction_override` for injected
- 80/10/10 split, seed 42

### usman_injecagent.csv (1054 rows)
- Source: InjecAgent test cases loaded from raw.githubusercontent.com
  - `test_cases_ds_base.json` (544 rows)
  - `test_cases_dh_base.json` (510 rows)
- Field mapping: `external_content` = Tool Response Template + "\n\n" + Attacker Instruction (combined)
- `injection_span_text` = attacker instruction with computed offsets when present
- `Attack Type` mapped to `injection_category`; all examples labeled injected per source
- 80/10/10 split, seed 42

## Canonical Schema (10 columns, order preserved)

`id`, `source_dataset`, `user_instruction`, `external_content`, `label`, `injection_span_text`, `injection_start_char`, `injection_end_char`, `injection_category`, `split`

Allowed values:
- `label`: `clean`, `injected`
- `split`: `train`, `val`, `test`
- `injection_category`: `instruction_override`, `data_exfiltration`, `tool_misuse`, `other`

## Splits

80/10/10, seed 42. Records shuffled globally before splitting (no explicit scenario grouping possible without source metadata). Existing source splits not preserved (re-split deterministically).

## Hard Negatives

`data/templates/hard_negatives.json` contains 5 harmless templates for testing discrimination between legitimate external content and content with indirect prompt injection attacks:
- recipe
- workplace_email
- help_article
- product_manual
- meeting_notes

## Reproduction

```bash
cd claypeus
python3 data/scripts/convert_deepset.py          # downloads HF dataset
python3 data/scripts/convert_injecagent.py        # loads remote raw files
python3 -m pytest tests/test_datasets.py -v
python3 -c "from data.scripts import dataset_utils; print(dataset_utils.validate_csv('data/processed/usman_deepset.csv'))"
```

## Sources

- InjecAgent: https://github.com/uiuc-kang-lab/InjecAgent (reference only; not cloned)
- deepset/prompt-injections: https://huggingface.co/datasets/deepset/prompt-injections