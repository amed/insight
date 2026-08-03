import { useState } from 'react';
import { useSchemas } from '../hooks/useSchemas.js';
import { useSummary } from '../hooks/useSummary.js';

const pipelines = [
  { key: '', label: 'all pipelines' },
  { key: 'p1', label: 'p1 baseline' },
  { key: 'p2', label: 'p2 grounded' },
  { key: 'p3', label: 'p3 direct' },
];

// one horizontal bar row: label, bar sized as a share of total, count as text
function Bar({ label, count, total, kind }) {
  const percent = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="bar-row" title={`${count} of ${total}`}>
      <span className="bar-label">{label}</span>
      <span className="bar-track">
        <span className={`bar-fill ${kind || ''}`} style={{ width: `${percent}%` }} />
      </span>
      <span className="bar-count">{count}</span>
    </div>
  );
}

export default function Summary() {
  const { data: schemaList, isLoading, isError } = useSchemas();
  const [schemaId, setSchemaId] = useState(null);
  const [pipeline, setPipeline] = useState('');

  if (isLoading) return <p className="muted">loading...</p>;
  if (isError || !schemaList || schemaList.length === 0) {
    return <p className="error">failed to load schemas</p>;
  }

  const fallback = schemaList.find((s) => s.default) || schemaList[0];
  const schema = schemaList.find((s) => s.id === schemaId) || fallback;

  return <SummaryView schema={schema} pipeline={pipeline}
    onSchema={setSchemaId} onPipeline={setPipeline} schemaList={schemaList} />;
}

function SummaryView({ schema, pipeline, onSchema, onPipeline, schemaList }) {
  const { data, isLoading, isError } = useSummary(schema, pipeline || null);

  return (
    <div className="summary">
      <div className="summary-controls">
        <label className="hint">
          schema{' '}
          <select value={schema.id} onChange={(event) => onSchema(event.target.value)}>
            {schemaList.map((s) => (
              <option key={s.id} value={s.id}>{s.id}</option>
            ))}
          </select>
        </label>
        <label className="hint">
          pipeline{' '}
          <select value={pipeline} onChange={(event) => onPipeline(event.target.value)}>
            {pipelines.map((p) => (
              <option key={p.key} value={p.key}>{p.label}</option>
            ))}
          </select>
        </label>
      </div>

      {isLoading && <p className="muted">loading...</p>}
      {isError && <p className="error">failed to load the summary</p>}

      {data && (
        <>
          <p className="muted">
            {data.total} completed record{data.total === 1 ? '' : 's'} under {data.schema}
            {data.pipeline ? `, pipeline ${data.pipeline}` : ''}
          </p>

          {data.total === 0 ? (
            <p className="muted">nothing to chart yet, upload under this schema first.</p>
          ) : (
            <div className="charts">
              {data.fields.map((field) => (
                <section key={field.name} className="chart">
                  <h4 className="chart-title">{field.name}</h4>
                  {field.values.map((entry) => (
                    <Bar key={entry.value} label={entry.value} count={entry.count} total={data.total} />
                  ))}
                  <Bar label="unknown" count={field.unknown} total={data.total} kind="neutral" />
                  <Bar label="missing" count={field.missing} total={data.total} kind="absent" />
                </section>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
