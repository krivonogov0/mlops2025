# Step 4: Data Validation with Great Expectations

ML pipeline with data validation using Great Expectations and Data Docs.

## Setup

```bash
make install  # poetry install
dvc init
dvc remote add -d local ../../.dvcstore
```

## Run

```bash
dvc repro
```

Pipeline includes data validation step that:

- Checks for null values in total_bill, tip, size
- Validates total_bill range [0, 100]
- Validates size range [1, 10]
- Generates beautiful HTML validation report at `reports/validation/index.html`
- Stops pipeline if validation fails

Open `reports/validation/index.html` in browser to see detailed validation report with styled results and statistics.

## Code formatting

We have a pre-commit template to automatically format your code.

To install pre-commit:

```bash
cd lesson2/seminar/step4_ge_validation_data
pip install pre-commit
```

Then you can run pre-commit with:

```bash
cd lesson2/seminar/step4_ge_validation_data
pre-commit run --all-files
```
