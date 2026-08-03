import { useState } from 'react';
import { useCreateInteraction } from '../hooks/useCreateInteraction.js';
import { useSchemas } from '../hooks/useSchemas.js';
import { buildTranscriptFile } from '../lib/transcript.js';

const modes = [
  { key: 'file', label: 'Transcript' },
  { key: 'text', label: 'Text' },
  { key: 'audio', label: 'Audio' },
];

export default function Upload() {
  const [mode, setMode] = useState('file');
  const [file, setFile] = useState(null);
  const [text, setText] = useState('');
  const [channels, setChannels] = useState(null);
  const [splitChannels, setSplitChannels] = useState(false);
  const [agentChannel, setAgentChannel] = useState(0);
  const [schemaId, setSchemaId] = useState(null);
  const { data: schemaList } = useSchemas();
  const mutation = useCreateInteraction();

  // the batch's schema; the base schema until another is picked
  const fallback = schemaList && (schemaList.find((s) => s.default) || schemaList[0]);
  const schema = schemaId || (fallback && fallback.id) || null;

  // the inputs are reset when the mode changes
  function changeMode(next) {
    setMode(next);
    setFile(null);
    setText('');
    setChannels(null);
    setSplitChannels(false);
    mutation.reset();
  }

  // the channel count is read in the browser so the audio type can be shown
  async function selectAudio(event) {
    const picked = event.target.files[0] || null;
    setFile(picked);
    setChannels(null);
    setSplitChannels(false);
    if (!picked) return;
    try {
      const buffer = await picked.arrayBuffer();
      const ctx = new AudioContext();
      const decoded = await ctx.decodeAudioData(buffer);
      setChannels(decoded.numberOfChannels);
      ctx.close();
    } catch {
      setChannels(null);
    }
  }

  // the active input is uploaded; per-channel split is sent only when opted in
  function submit(event) {
    event.preventDefault();
    const payload = mode === 'text' ? buildTranscriptFile(text) : file;
    if (!payload) return;
    const fields = {
      ...(schema ? { schema } : {}),
      ...(mode === 'audio' && channels >= 2 && splitChannels
        ? { split_channels: '1', agent_channel: agentChannel }
        : {}),
    };
    mutation.mutate(
      { file: payload, fields },
      {
        onSuccess: () => {
          setFile(null);
          setText('');
        },
      }
    );
  }

  return (
    <form className="upload" onSubmit={submit}>
      <div className="upload-modes">
        {modes.map((m) => (
          <button
            key={m.key}
            type="button"
            className={m.key === mode ? 'tab active' : 'tab'}
            onClick={() => changeMode(m.key)}
          >
            {m.label}
          </button>
        ))}
      </div>

      {mode === 'file' && (
        <>
          <p className="hint">
            a json transcript: {'{ "interaction_id": "...", "turns": [{ "speaker": "...", "text": "..." }] }'}
          </p>
          <input
            type="file"
            accept="application/json,.json"
            onChange={(event) => setFile(event.target.files[0] || null)}
          />
        </>
      )}

      {mode === 'text' && (
        <>
          <p className="hint">
            paste the conversation, one turn per line. a line may be prefixed with "speaker:" to label who is talking.
          </p>
          <textarea
            className="upload-text"
            rows={8}
            placeholder={'customer: I want a refund\nagent: sure, can I get your order number?'}
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        </>
      )}

      {mode === 'audio' && (
        <>
          <p className="hint">an audio file (mp3, wav). it is transcribed by whisper.</p>
          <input type="file" accept="audio/*" onChange={selectAudio} />
          {channels >= 2 && (
            <div className="audio-info">
              <p className="hint">dual-channel detected.</p>
              <label className="hint">
                <input
                  type="checkbox"
                  checked={splitChannels}
                  onChange={(event) => setSplitChannels(event.target.checked)}
                />{' '}
                separate speakers (one per channel)
              </label>
              {splitChannels ? (
                <label className="hint">
                  agent channel:{' '}
                  <select value={agentChannel} onChange={(event) => setAgentChannel(Number(event.target.value))}>
                    <option value={0}>left</option>
                    <option value={1}>right</option>
                  </select>
                </label>
              ) : (
                <p className="hint">combined: speaker roles are inferred from the content.</p>
              )}
            </div>
          )}
          {channels === 1 && (
            <p className="hint">mono: speakers are mixed, roles are inferred from the content.</p>
          )}
        </>
      )}

      {schemaList && schemaList.length > 1 && (
        <label className="hint">
          schema{' '}
          <select value={schema || ''} onChange={(event) => setSchemaId(event.target.value)}>
            {schemaList.map((s) => (
              <option key={s.id} value={s.id}>{s.id}</option>
            ))}
          </select>
        </label>
      )}

      <button type="submit" className="button" disabled={mutation.isPending}>
        {mutation.isPending ? 'Uploading...' : 'Upload'}
      </button>

      {mutation.isError && <p className="error">upload failed</p>}
      {mutation.isSuccess && (
        <p className="success">uploaded, id {mutation.data.id}. open the Interactions tab to see it.</p>
      )}
    </form>
  );
}
