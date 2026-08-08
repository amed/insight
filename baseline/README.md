# Baseline (P1)

TF-IDF + one logistic regression per schema field.
Training data must be prepared by the `dataprep` module. Baline module only trains and serves.

```bash
python3 train.py # fit the classifiers, save model.joblib
```

`train.py` reads `dataprep/out/training/` (in docker: `/app/data`, mounted by
compose) and saves `model.joblib` with the v1 schema claim (name + hash). An
existing artifact is reused only while its claim matches the current schema,
so a schema change retrains automatically. `main.py` serves `/extract`: all
field values from one call, the model version and the schema claim ride along,
and core fails any p1 record whose schema does not match the claim.

Where every training label comes from, how the test batches are built, and
the split discipline (training and testing never share a conversation) are
documented in `dataprep/README.md` and enforced by `dataprep/validate.py`.
