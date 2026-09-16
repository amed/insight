# Example uploads

Every kind of input Insight accepts.
All commands run from the repository root against a running stack (see `docs/getting-started.md`).

## Files

| file | what it is | how to upload |
|---|---|---|
| `transcript.json` | A four-turn minimal invented refund chat. | Transcript upload. |
| `retail-chat.json` | A real retail support chat about an invalid promo code, from ABCD. | Transcript upload. |
| `pasted-text.txt` | The same retail chat as `speaker: text` lines. | Paste into the Text tab of the web upload. |
| `bank-call.json` | The verified human transcript of the bank call below. | Transcript upload. |
| `bank-call-machine-transcript.json` | The corpus machine transcript of the same call, with its recognition errors. | Transcript upload. |
| `bank-call-mono.wav` | The bank call with both parties mixed into one channel. | Audio upload, diarisation infers the speakers. |
| `bank-call-stereo.wav` | The bank call with the agent on channel 0 and the customer on channel 1. | Audio upload with `split_channels`, roles come from the channels. |
| `bank-call.mp3`, `.m4a`, `.ogg`, `.flac`, `.webm` | The mono call in every other audio format the upload accepts. | Audio upload, same as the mono wav. |

The bank call is a customer who lost a credit card and asks for a replacement.
It lasts 39 seconds and has 9 turns.
Under schema v1 its intent is `replacement_request`, under schema v2 its `banking_task` is `replace_card`.

## Upload a transcript

```bash
curl -s -i -F "file=@examples/retail-chat.json" localhost:4000/interactions
```

Every transcript carries an `interaction_id`.
The id must be unique, a second upload of the same file is refused with 409 until the id is changed.

## Upload audio

```bash
# Combined audio, diarisation decides who spoke when.
curl -s -i -F "file=@examples/bank-call-mono.wav" localhost:4000/interactions

# Separated channels, the speaker follows from the channel and no diarisation runs.
curl -s -i -F "file=@examples/bank-call-stereo.wav" -F "split_channels=true" -F "agent_channel=0" localhost:4000/interactions

# Any other accepted format goes the same way as the mono wav.
curl -s -i -F "file=@examples/bank-call.mp3" localhost:4000/interactions
```

Audio uploads get a generated interaction id, so the same file can be uploaded repeatedly.
Without `split_channels` a stereo file is downmixed and treated as combined audio.

## Choose the pipeline and the schema

```bash
# p1 tf-idf baseline, p2 retrieval-grounded llm (the default), p3 direct llm.
curl -s -i -F "file=@examples/bank-call.json" -F "pipeline=p3" localhost:4000/interactions

# Schema v2 adds the banking_task field, which this call answers.
curl -s -i -F "file=@examples/bank-call.json" -F "schema=v2" localhost:4000/interactions
```

The pipeline p1 refuses schema v2 by design, because its trained artifact claims v1.

## Read the result

```bash
# The id comes from the upload response.
curl -s localhost:4000/interactions/<id>
curl -s localhost:4000/interactions/<id>/steps
```

The record stays `pending` until extraction finishes.
Audio takes minutes on cpu.

## Where the files come from

The bank call is call `057d15ba6b9044d2` of the Gridspace-Stanford Harper Valley Bank corpus.
The corpus ships each party as its own recording, and the agent's recording starts 2.04 seconds later than the customer's.
The agent track is delayed by that gap so both tracks sit on the same clock.
The mono file mixes the two tracks into one channel, the stereo file keeps them as channels 0 and 1, and the other formats are encoded from the mono file with ffmpeg.
The two transcripts are the corpus's human-corrected and machine transcripts for that call, with non-speech markers removed.
The calls are scripted with assigned personas, so they contain no real personal data.

The retail chat is conversation `2677` of the Action-Based Conversations Dataset test split.
Agent system actions are removed, only the spoken turns remain.
`pasted-text.txt` is the same conversation as plain text.

`transcript.json` is invented for this project.

## Licences and credit

**Harper Valley Bank** is released under CC BY 4.0 by Gridspace and Stanford, `https://github.com/cricketclub/gridspace-stanford-harper-valley`.
The audio and transcript files derived from it may be shared with this credit.

Wu, M., Nafziger, J., Scodary, A., Maas, A. (2020). HarperValleyBank: A Domain-Specific Spoken Dialog Corpus. arXiv:2010.13929.

**ABCD** is released under the MIT licence, Copyright (c) 2021 ASAPP Research, `https://github.com/asappresearch/abcd`.

Chen, D., Chen, H., Yang, Y., Lin, A., Yu, Z. (2021). Action-Based Conversations Dataset: A Corpus for Building More In-Depth Task-Oriented Dialogue Systems. NAACL.

## How the files were generated

Everything starts from the outputs of `python3 dataprep/prepare.py`, which downloads both corpora and writes the transcripts as upload-ready JSON.
The audio is built here from the corpus's per-party recordings rather than copied from dataprep, so the two tracks can be aligned first.

In the corpus transcript every segment carries `start_ms`, its time on the party's own recording, and `offset_ms`, its time on the shared call clock.
For this call the difference is 2040 ms on every agent segment and 0 on every customer segment, so the agent recording began 2.04 seconds into the call.
The agent track is delayed by that amount before the two are combined.
`amix` pads to the longer track on its own.
`amerge` stops at the shorter input, so both inputs are padded and the output is cut at the customer track's length of 38.87 seconds.

```bash
SRC=dataprep/data/harper-valley-bank/data/audio
AGENT=$SRC/agent/057d15ba6b9044d2.wav
CALLER=$SRC/caller/057d15ba6b9044d2.wav
cd examples
ffmpeg -i $AGENT -i $CALLER -filter_complex "[0]adelay=2040:all=1[a];[a][1]amix=inputs=2:duration=longest" -ac 1 bank-call-mono.wav
ffmpeg -i $AGENT -i $CALLER -filter_complex "[0]adelay=2040:all=1,aformat=channel_layouts=mono,apad[a];[1]aformat=channel_layouts=mono,apad[b];[a][b]amerge=inputs=2" -ac 2 -t 38.87 bank-call-stereo.wav
ffmpeg -i bank-call-mono.wav -c:a libmp3lame -q:a 4 bank-call.mp3
ffmpeg -i bank-call-mono.wav -c:a aac -b:a 64k bank-call.m4a
ffmpeg -i bank-call-mono.wav -c:a libvorbis -q:a 4 bank-call.ogg
ffmpeg -i bank-call-mono.wav -c:a flac bank-call.flac
ffmpeg -i bank-call-mono.wav -ar 16000 -c:a libopus -b:a 32k bank-call.webm
```

The transcripts are the dataprep records with a new `interaction_id`.

```python
import json
def copy(src, dst, iid):
  turns = json.load(open(src))["turns"]
  json.dump({"interaction_id": iid, "turns": turns}, open(dst, "w"), indent=2)

copy("dataprep/out/testing/hvb-audio/records/hvb-057d15ba6b9044d2.json", "examples/bank-call.json", "example-bank-call")
copy("dataprep/out/testing/hvb-audio/records/hvb-057d15ba6b9044d2.asr.json", "examples/bank-call-machine-transcript.json", "example-bank-call-machine-transcript")
copy("dataprep/out/testing/abcd-text/records/abcd-2677.json", "examples/retail-chat.json", "example-retail-chat")
```

`pasted-text.txt` is `retail-chat.json` flattened to one `speaker: text` line per turn.
