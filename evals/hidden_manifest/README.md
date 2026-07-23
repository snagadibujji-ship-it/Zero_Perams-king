# Hidden Manifest — Private Eval Cases

## Purpose

This directory contains the **schema and tooling** for hidden benchmark cases that are NOT checked into the repository. Hidden cases serve as canary tests to detect:

1. **Contamination** — If AXIMA's source code contains hardcoded answers to benchmark cases, hidden cases will reveal this because the system cannot have seen them.
2. **Overfitting** — If improvements only affect public cases but not hidden ones, the system is overfitting to the known test set.
3. **Regression** — Hidden cases provide an independent validation set for detecting behavioral regressions.

## How It Works

1. **Schema** (`schema.json`) defines the format for hidden cases.
2. **Generation** (`generate_mutations.py`) creates semantic mutations from existing public cases — negations, number changes, entity swaps — to produce novel test inputs.
3. **Storage** — Actual hidden case files (`hidden_cases.json`) are listed in `.gitignore` and stored only in the CI environment or secure storage.

## File Structure

```
evals/hidden_manifest/
├── README.md                  ← This file
├── schema.json                ← Case format definition
├── generate_mutations.py      ← Mutation generator
└── hidden_cases.json          ← NOT in repo (gitignored)
```

## Generating Hidden Cases

```bash
# Generate mutations from public manifest
python evals/hidden_manifest/generate_mutations.py \
    --source evals/public/manifest.json \
    --output evals/hidden_manifest/hidden_cases.json \
    --mutations-per-case 3

# Verify generated cases match schema
python evals/hidden_manifest/generate_mutations.py \
    --validate evals/hidden_manifest/hidden_cases.json
```

## Security

- Hidden cases MUST NOT be committed to the repository.
- Hidden cases MUST NOT be accessible to the AXIMA runtime.
- The runner loads them from a path specified at execution time only.
- Integrity is verified via SHA-256 hash before each run.

## Using Hidden Cases in CI

```yaml
# Example CI step
- name: Run hidden evals
  env:
    HIDDEN_MANIFEST_PATH: ${{ secrets.HIDDEN_MANIFEST_PATH }}
  run: |
    python evals/run_cosmic_evals.py --manifest $HIDDEN_MANIFEST_PATH
```
