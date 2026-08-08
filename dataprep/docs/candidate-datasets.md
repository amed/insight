# Candidate Datasets

This following list represents the revised candidate datasets considered for the project.
Most datasets were not ultimately used, they were selected in the review because each offered a potential contribution to the project's data requirements.

## Audio Datasets

The first five satisfy your minimum requirement for downloadable service-domain speech. Datasets 6 and 7 strengthen the possibility of a demographic/fairness research questions.

### 1 LEGOv2

Telephone calls to the deployed CMU Let's Go bus-information service. It provides user-utterance WAV files, full-call recordings, CSV/MySQL interaction data, 548 calls and 13,836 exchanges. Crucially, it includes age, gender, dialogue outcome, human interaction-quality ratings and human emotion labels such as friendly, neutral and angry. The complete download is approximately 1.1 GB.
Best overall dataset for sentiment, satisfaction, task completion, age/gender disparity, and audio-to-BI evaluation.

[https://www.uni-bamberg.de/en/ds/ressources/lego-spoken-dialogue-corpus/](https://www.uni-bamberg.de/en/ds/ressources/lego-spoken-dialogue-corpus/)

### 2 HarperValleyBank

Simulated human-human banking contact-centre calls: about 23 hours, 1,446 conversations and 59 speakers. Every conversation has separate caller and agent WAV files, human-corrected transcripts, machine transcripts, speaker roles, tasks/intents and dialogue-act outputs.

Best direct contact-centre simulation. Particularly strong for comparing manual transcript => BI against audio => ASR => BI.

[https://arxiv.org/abs/2010.13929](https://arxiv.org/abs/2010.13929)

### 3 SpokenWOZ

A large human-human spoken service-dialogue benchmark covering eight domains: 5,700 dialogues, 203,000 turns and 249 hours of audio. It includes dialogue goals, dialogue state, acts, corresponding audio and ASR word-level output. It is distributed under CC BY-NC 4.0.

Best large-scale multimodal evaluation corpus for ASR error propagation, slots, dialogue state, task success and cross-turn reasoning.

[https://spokenwoz.github.io/](https://spokenwoz.github.io/)

### 4 DSTC2 and DSTC3

Spoken human-system service interactions in restaurant and tourist-information domains. The official release includes labeled train/development/test corpora plus audio archives containing WAV files for all turns. The GitHub release currently exposes 22 downloadable assets, including multiple multi-gigabyte audio archives.

Best established benchmark for dialogue-state tracking under ASR errors.

[https://github.com/matthen/dstc](https://github.com/matthen/dstc)

### 5 MInDS-14

Spoken e-banking requests covering 14 banking intents and 14 language varieties. Every example includes 8 kHz audio, a native-language transcript, English translation, intent and language ID. It is licensed under CC BY.

Best banking-intent and multilingual/language-variety test. It is single-turn speech rather than a full agent-customer call.

[https://huggingface.co/datasets/PolyAI/minds14](https://huggingface.co/datasets/PolyAI/minds14)

### 6 SLURP

Spoken-language-understanding audio with textual annotations for scenarios, actions, intents and entities. The download script retrieves approximately 6 GB of audio. Speaker metadata encodes female/male/unknown and native/non-native English status. Text is CC BY 4.0; audio is CC BY-NC 4.0.

Best supplementary dataset for gender and native/non-native robustness. It is a spoken-intent proxy, not customer support.

[https://github.com/pswietojanski/slurp](https://github.com/pswietojanski/slurp)

### 7 FaiST-EV

Natural U.S. conversational speech with metadata for self-identified race, ethnicity and national origin, along with the exact dialogue span where the identification occurred. The current Zenodo record provides a 2.5 GB audio archive and a 13.4 MB metadata file.

Best supplementary fairness audit for race/ethnicity. It is not customer-service speech and should not be used as if it were.

[https://zenodo.org/records/16997247](https://zenodo.org/records/16997247)

## Text-Based Customer-Support Datasets

### CallCenterEN / AIxBlock 92K

91,706 real-world English call-centre transcripts corresponding to approximately 10,500 hours of inbound and outbound calls. It includes Indian, American and Filipino accent categories, word timestamps, ASR confidence, domain/topic tags and PII redaction. The audio is not included, and the transcripts were generated using commercial ASR.

Best text corpus for real call-centre language, scale and domain-shift testing. Do not use it as human gold for measuring your ASR WER.

[https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english](https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english)

### ABCD

More than 10,000 fully labeled human-human customer-service dialogues with 55 user intents, agent actions, company-policy constraints, action flows and task success. The official repository is MIT licensed.

Best structured customer-service corpus for actions, policy compliance, resolution and task success.

[https://aclanthology.org/2021.naacl-main.239/](https://aclanthology.org/2021.naacl-main.239/)

### MultiDoGO

More than 81,000 human-human dialogues across airline, fast food, finance, insurance, media and software; over 54,000 conversations have intent and slot annotations. It uses a Wizard-of-Oz setup in which a crowd customer interacts with a trained agent. The repository supplies train/dev/test TSV files and uses the CDLA Permissive License.

Best cross-domain intent and entity/slot benchmark.

[https://aclanthology.org/D19-1460/](https://aclanthology.org/D19-1460/)

### TweetSumm

1,100 real-world Twitter customer-support dialogues, each with three human extractive and three human abstractive summaries-close to 6,500 summaries altogether. The repository is CC0, but readable conversations are reconstructed using the original Customer Support on Twitter `twcs.csv` file.

Best corpus for issue/resolution summaries, agent handover notes and summary factuality.

[https://aclanthology.org/2021.findings-emnlp.24/](https://aclanthology.org/2021.findings-emnlp.24/)
