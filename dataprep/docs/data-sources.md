# Source status and licenses

The following is every raw file data preparation module downloads, its source, and its license.

| file(s) in `data/` | source | license |
|---|---|---|
| `abcd_v1.1.json.gz` | github.com/asappresearch/abcd | MIT (LICENSE file, ASAPP Research 2021) |  
| `emowoz-multiwoz.json`<br />`emowoz-dialmage.json` | Zenodo record 6506504 (official EmoWOZ release) | CC BY-NC 4.0 (Zenodo record metadata) |  
| `maia-de_client_01.json`<br />`maia-de_client_02.json`<br />`maia-pt_br_client_02.json`<br />`maia-pt_br_client_04.json`<br />`maia-pt_pt_client_03.json` | github.com/johndmendonca/MAIA-DQE | CC BY-ND 4.0 (LICENSE.md: Attribution-NoDerivatives, not non-commercial) |  
| `harper-valley-bank/` (clone: audio, transcripts, metadata) | github.com/cricketclub/gridspace-stanford-harper-valley | CC BY 4.0 (LICENSE file, confirmed by the repository license field) |  

## Use in this project

1. ABCD (MIT): keep the copyright and license notice when redistributing
   the data or substantial parts of the repository's code. Citing the paper
   covers academic attribution.
2. HarperValleyBank (CC BY 4.0): attribution required, otherwise
   unrestricted; the derived mono and stereo wavs may even be published with
   credit. The calls are scripted with assigned personas, so they contain no
   real personal data.
3. EmoWOZ (CC BY-NC 4.0): non-commercial use only. The project qualifies;
   the constraint would bite only if the system were commercialised, since the
   sentiment classifier is trained on this corpus. Stated in the report's
   limitations.
4. MAIA-DQE (CC BY-ND 4.0): no derivatives may be distributed. Analysing,
   training on, and reporting results is fine (analysis is not distribution),
   but the converted maia-text records are adaptations and must never land in
   the public repository. `data/` and `out/` are gitignored, which enforces
   this; verify it still holds before the repository goes public. Short quoted
   excerpts in the report are normal academic quotation and fine.

Because `prepare.py` re-downloads everything from these exact sources, anyone
cloning the public repository can rebuild the full dataset locally without the
project distributing a single licensed file.

## Data Feeds

| source | training (out/training/) | testing (out/testing/) |
|---|---|---|
| ABCD | `intent`, `issue_type`, `agent_action` (train split) | `abcd-text`: 186 records, gold for the same three fields (test split) |
| EmoWOZ | `sentiment` (with the MAIA train part) | none |
| MAIA-DQE | `sentiment`, `resolution_status` (train part, 400 of 501) | `maia-text`: 101 holdout records, gold `sentiment`, `resolution_status` |
| HarperValleyBank | none | `hvb-audio`: 50 calls as oracle/asr text + mono/stereo wavs, gold `intent`, speaker roles; task labels are the gold for `banking_task` (v2, stored as `intent_source`) |

## Links

- Chen, D., Chen, H., Yang, Y., Lin, A., Yu, Z. (2021). Action-Based
  Conversations Dataset: a corpus for building more in-depth task-oriented
  dialogue systems. NAACL. https://github.com/asappresearch/abcd
- Feng, S., Lubis, N., Geishauser, C., Lin, H., Heck, M., van Niekerk, C.,
  Gasic, M. (2022). EmoWOZ: a large-scale corpus and labelling scheme for
  emotion recognition in task-oriented dialogue systems. LREC.
  https://zenodo.org/record/6506504
- Mendonca, J., Pereira, P., Menezes, M., Cabarrao, V., Moniz, H.,
  Carvalho, J. P., Lavie, A., Trancoso, I. (2023). Dialogue quality and
  emotion annotations for customer support conversations. GEM Workshop,
  EMNLP. https://github.com/johndmendonca/MAIA-DQE
- Wu, M., Nafziger, J., Scodary, A., Maas, A. (2020). HarperValleyBank: a
  domain-specific spoken dialog corpus. arXiv:2010.13929.
  https://github.com/cricketclub/gridspace-stanford-harper-valley
