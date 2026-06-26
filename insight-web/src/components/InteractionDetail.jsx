import { useInteraction } from '../hooks/useInteraction.js';
import { useSteps } from '../hooks/useSteps.js';

// the message shown when the fields list is empty, based on record status
function emptyFieldsMessage(record) {
  if (!record) return 'no record';
  if (record.status === 'pending') return 'processing, this updates automatically';
  if (record.status === 'failed') return 'processing failed (are embeddings and ollama running?)';
  return 'no fields were extracted';
}

export default function InteractionDetail({ id }) {
  const { data, isLoading, isError } = useInteraction(id);
  const poll = data?.record?.status === 'pending';
  const { data: steps } = useSteps(id, poll);

  if (isLoading) return <p className="muted">loading...</p>;
  if (isError || !data) return <p className="error">failed to load interaction</p>;

  const record = data.record;
  const fields = record ? record.fields : [];

  return (
    <div className="detail">
      <h3>{data.interaction_id}</h3>
      <p className="muted">status: {record ? record.status : 'n/a'}</p>

      <h4>lines</h4>
      <ul className="lines">
        {data.lines.map((line) => (
          <li key={line.line_id}>
            <span className="muted">{line.line_id} {line.speaker}:</span> {line.text}
          </li>
        ))}
      </ul>

      <h4>fields</h4>
      {fields.length > 0 ? (
        <ul className="fields">
          {fields.map((field) => (
            <li key={field.name}>
              <strong>{field.name}:</strong> {field.value}{' '}
              <span className="muted">[{field.citations.join(', ')}]</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">{emptyFieldsMessage(record)}</p>
      )}

      <h4>steps</h4>
      {steps && steps.length > 0 ? (
        <ul className="steps">
          {steps.map((step) => (
            <li key={step.id}>
              <span className={`step-status step-${step.status}`}>{step.status}</span> {step.name}
              {step.detail && <pre className="step-detail">{JSON.stringify(step.detail)}</pre>}
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">no steps recorded</p>
      )}
    </div>
  );
}
