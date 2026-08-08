# Datasets

NOTE: No selected corpus provides accent or speaker-demographic annotations. this is reported as a limitation. No corpus provides evidence line identifiers indicating which transcript lines support each schema value. If citation recall is evaluated directly, this would require manual annotation on a small subset.



## Field-to-source summary

| Schema field        | Trained on            | Tested against           | Rationale                                             |
| ------------------- | --------------------- | ------------------------ | ----------------------------------------------------- |
| `intent`            | ABCD train            | `abcd-text`, `hvb-audio` | Task labels represent the customer's goal.            |
| `issue_type`        | ABCD train            | `abcd-text`              | Flow labels represent the problem category.           |
| `agent_action`      | ABCD train            | `abcd-text`              | Logged actions record what the agent did.             |
| `sentiment`         | EmoWOZ and MAIA train | `maia-text`              | Human emotion annotations support sentiment labels.   |
| `resolution_status` | MAIA train            | `maia-text`              | Human task-success judgements support outcome labels. |
| `banking_task` (v2) | not trained, P1 refuses by design | `hvb-audio` | Task labels give gold for the configuration-added RQ4 field. |


## Research Questions

The four research questions require four data properties, not necessarily four separate datasets.


### Research Question 1

How accurately are predefined BI fields extracted by the three pipelines when evaluated against the same annotated reference set?
(Controlled pipeline comparison)

All pipelines process the same records and BI fields, evaluated against one annotated test set using accuracy and macroF1.

RQ1 requires a fixed human-annotated reference set: conversations in the same input format accepted by the system, with trusted gold labels for each schema field represented somewhere in the test data.
This allows all three pipelines to be evaluated on identical records.
Because P1 is supervised, RQ1 also requires labelled training text for each field, strictly disjoint from the test records.


### Research Question 2

Are unsupported field values reduced by retrieval grounding compared with direct LLM extraction under matched conditions?
(Controlled grounding experiment)

Grounded and direct LLM pipelines use the same model, schema, prompts, and settings, differing only in retrieval. They are compared using evidence support and unsupported-claim rate.

RQ2 does not require additional data, but it does require matched evaluation conditions.
The same records must be processed by both the grounded and direct pipelines, using the evidence citations already stored by the system.
A small hand-annotated set of gold evidence lines would strengthen support-level evaluation, but it is not required for the basic comparison.


### Research Question 3

To what extent is BI extraction performance reduced by ASR errors relative to verified transcripts?
(Paired audio evaluation)

Each interaction is processed from both reference and ASR transcripts. WER and downstream extraction degradation are measured, with diarisation controlled or reported separately.

RQ3 requires paired inputs: the same interaction must be available as both a verified human transcript and audio processed through ASR. Ideally, the audio should include variants that separate transcription error from speaker-assignment error, such as stereo audio with known channels and mono audio requiring diarisation. The verified transcript is also needed as the reference for word error rate.


### Research Question 4

Can new BI fields be introduced through configuration without retraining or code changes while acceptable accuracy and evidential support are maintained? 
(Post-development configuration test)

New BI fields are added through configuration without retraining or code changes, then evaluated for schema validity, accuracy, and evidence support.

RQ4 requires a labelled field that is not already present in the deployed schema. This allows a new field to be added through configuration and scored immediately against existing gold labels.
Other data properties, such as accent annotations or additional corpora, are useful only if they support these requirements.



## Why these datasets

All data built here is mapped directly and exclusively to the v1 schema: the mapping files are stamped `"schema": "v1"`, labels and gold are validated against v1's value sets at build time, and every output manifest records the v1 content hash.

Since the data will be used for evaluation and training (baseline), it requires three types of data that are not available in a single public corpus:

- labelled text for training baseline models across the schema fields
- human-annotated gold data for testing all pipelines
- audio with verified transcripts for assessing ASR effects

Because no public corpus directly annotates all required business fields, such as resolution status or agent action, each field is sourced from the corpus whose human annotations map most defensibly to that field.
The selection criteria were public availability, research-compatible licensing, human annotation rather than model-generated labels, and a documented structure that could be checked against the downloaded data.


## ABCD - text, training and testing

The Action-Based Conversations Dataset contains 10,000 human-to-human retail support dialogues. Each conversation includes a flow label, covering 10 categories, a subflow label, covering 55 scenarios. The dataset is described by Chen et al. (2021) and is released under the MIT license.

ABCD was selected because, among the corpora reviewed for this project, it provides the strongest public source of agent-customer service conversations with per-conversation task labels. It also includes predefined splits, ensuring that the training and testing sets do not share conversations.

Three v1 schema fields are extracted from ABCD.

`intent` is derived from the subflow label using the reviewed mapping in `corpora/abcd_mapping.json`, since the subflow describes the customer's goal.
Six subflows do not map to a schema value and are left unlabelled.

`issue_type` is derived from the flow label using the same mapping file, because the flow represents the problem category.

`agent_action` is derived from the logged action buttons and grouped into schema-level categories

## EmoWOZ - text, training only

EmoWOZ contains approximately 11,000 task-oriented dialogues based on MultiWOZ and the DialMAGE human-machine dataset.
Each user turn has a gold emotion and sentiment label produced by three annotators with adjudication.

EmoWOZ was selected as a sentiment-training source because it provides a large set of human sentiment annotations on service-style dialogue.
DialMAGE adds negative examples that are less common in polite service corpora.

One `sentiment` example is extracted per dialogue.
The customer's final non-neutral gold sentiment is used as the conversation-level label. 
If no non-neutral sentiment is present, the label is neutral. This rule reflects the intended meaning of a closing-sentiment business field.
Averaging sentiment across the full dialogue was avoided because it could obscure cases where an initially negative interaction is resolved by the end.


## MAIA-DQE - text, training and testing

MAIA-DQE contains genuine customer support conversations. It provides per-sentence customer emotion annotations and two dialogue-level human judgements: task success on a 1-5 scale and whether the conversation was dropped.

MAIA-DQE was selected because it is a public source of real customer support traffic with both emotion and outcome annotations.
This makes it the most defensible gold source for `sentiment` and `resolution_status`.
The dataset has no official split, so the module deduplicates the data, sorts the dialogues, and holds out every fifth dialogue for testing.
The holdout identifiers are written to disk, and the test batch is built only from those identifiers.

Two schema fields are extracted from MAIA-DQE.

`sentiment` uses the same final non-neutral rule as EmoWOZ, based on per-sentence customer emotions.
Happiness maps to positive. disappointment, confusion, frustration, anger, and anxiety map to negative. Empathy and neutral remain neutral.

`resolution_status` is derived from the human outcome judgements: dropped conversations are labelled unresolved, task-success scores of 4-5 are labelled resolved, scores of 1-2 are labelled unresolved, and score 3 is treated as ambiguous and therefore unlabelled. 

## HarperValleyBank - audio, testing only

HarperValleyBank contains 1,446 scripted bank calls with per-party WAV files, human-corrected and machine transcripts per segment, speaker roles, and a task label for each call.

HarperValleyBank was selected for the ASR question because its structure supports controlled comparison. The per-party recordings allow the module to construct both a mono mix, where diarisation must infer the speaker, and a stereo version, where roles are known by channel, for the same call. The paired human and machine transcripts support oracle-versus-ASR comparison. Speaker roles are provided by construction, so role-assignment accuracy can be evaluated without additional annotation.

The extraction uses 50 task-stratified calls, each represented in four variants: oracle text, ASR text, mono WAV, and stereo WAV.

Gold `intent` is derived from the task label using `corpora/hvb_mapping.json`. Four banking tasks have no schema value and remain unlabelled. The gold speaker sequence is also extracted for role-scoring.
Non-speech markers such as `[noise]` are removed because they are not lexical content and would inflate word error rate.
