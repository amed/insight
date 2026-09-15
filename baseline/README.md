# Baseline (P1)

TF-IDF with one logistic regression classifier per field. Produces values without citations.

Prepare the [training data](../dataprep/README.md), then run from the repository root:

```bash
docker compose up --build baseline
```

The container trains before serving `POST /extract` on port 8004.

For local training:

```bash
python3 -m pip install -r baseline/requirements.txt
python3 baseline/train.py
```

The model is saved as `baseline/model.joblib`. P1 is trained for the five v1 fields; core rejects a record if the model's schema name or hash does not match it.
