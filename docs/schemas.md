# Schemas - How Extraction Is Configured

This describes the implemented mechanism.
Design decisions are in [`field-configuration.md`](field-configuration.md).
Prediction scoring is documented in [`evaluation/`](../evaluation/README.md).

## Files

A schema is one JSON file in `insight-core/schemas/`, named `<name>.json`.
The file declares its name and an integer version, and the file name must match the declared name.

```json
{
  "name": "v1",
  "version": 1,
  "fields": [
    { "name": "sentiment", "question": "how does the customer feel?", "values": ["positive", "neutral", "negative"] }
  ]
}
```

A version bump is a new file with a new name.
Old files stay in place so their records remain readable.
`v1.json` is the base schema, five fields with closed values.

## Loading and validation

All files are loaded once at startup.
A broken file stops the process with the file name and reason.
The rejected cases are malformed json, a non-lowercase name, a non-integer version, empty or duplicate field names, a missing question, empty values, non-lowercase or duplicate values, the reserved value `unknown` in a values list, and a file whose name does not match its content.
A short content hash is computed per file.
The base schema must be present.

## API

- `GET /schemas` lists the loaded schemas with id, name, version, hash, whether it is the default, and the fields.
- `POST /interactions` takes an optional `schema` form field holding a schema id (`v1`).
  Without it the base schema is used.
  An unknown id is a 400.
- `GET /schemas/:name/summary?pipeline=p2` returns value counts for completed records under exactly that schema's name, version, and current content hash, so partitions are never merged.
  `pipeline` is optional, so evaluation records (the same conversations run through several pipelines) can be separated instead of blending into one distribution.

```bash
curl -s localhost:4000/schemas
curl -s -i -F "file=@examples/transcript.json" -F "schema=v1" localhost:4000/interactions
curl -s "localhost:4000/schemas/v1/summary?pipeline=p2"
```

The summary response emits every schema-defined value per field, zero-filled in schema order.
It also emits the `unknown` count and a `missing` count per field (the field produced nothing, a stage failure, which is a different fact from grounded ignorance).
`total`, the number of completed records in the slice, is the denominator.
Records with null schema stamps (pre-schema rows) never appear.

## What a record carries

Every insight record is stamped at upload with the schema name, version, and content hash.
The api returns the name as `schema` (`v1`) and the hash as `schema_hash` on the record, and `schema` on the list view.
The version is stored but not returned.
Pre-schema records have null stamps and are excluded from any schema-scoped aggregation.
Records are never aggregated across schema names, versions, or hashes.

## Extraction under a schema

The background job resolves the record's stamped schema from the registry (a missing schema fails the record with a traced reason) and loops over its fields.

- p2 retrieves the top-k lines for the field's question, p3 takes all lines.
  Both use the same prompt.
- The prompt lists the field's allowed values plus `unknown` and requires the value to be exactly one of them, with `unknown` when the lines support nothing.
- The answer is trimmed and lowercased, then checked against the closed set.
  An out-of-set answer is stored as `unknown`, its citations are dropped (they supported a rejected answer), and the raw answer lands in the extract trace step with `coerced: true`.
- The grounding filter is unchanged.
  Citations outside the lines shown to the model are dropped.
- The extract trace step records value, coerced flag, citations, dropped citations, lines_given, and prompt_chars.

The prompt change is versioned.
Records extracted under closed values carry `prompt2` in `config_version`, so free-text records from before are distinguishable.

## p1 under a schema

The baseline is trained against a schema file, not a hardcoded field list.
`train.py` reads `insight-core/schemas/v1.json` (in docker the directory is mounted read-only at `/schemas`), takes its fields and allowed values, and aborts if any training label falls outside them.
The artifact carries the schema id and content hash it was trained for, and `/extract` returns them with every prediction.

Core compares that claim to the record's stamp.
On any mismatch (name or hash) the record fails with a traced `schema mismatch` reason instead of storing values that do not belong to the schema.
There is no upload-time guard anymore.
The artifact's claim is the single source of truth for what p1 can serve.

## The web

The upload form offers the schema choice (fed by `GET /schemas`, hidden while only one schema exists).
The Insights tab renders the summary as one card per field with a bar per value, plus neutral bars for `unknown` and a dashed outline for `missing`, filterable by schema and pipeline.
