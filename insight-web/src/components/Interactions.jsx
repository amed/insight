import { useState } from 'react';
import { useInteractions } from '../hooks/useInteractions.js';
import InteractionDetail from './InteractionDetail.jsx';

export default function Interactions() {
  const { data, isLoading, isError } = useInteractions();
  const [selectedId, setSelectedId] = useState(null);

  if (isLoading) return <p className="muted">loading...</p>;
  if (isError) return <p className="error">failed to load interactions</p>;
  if (!data || data.length === 0) return <p className="muted">no interactions yet</p>;

  return (
    <div className="interactions">
      <ul className="interaction-list">
        {data.map((interaction) => (
          <li key={interaction.id}>
            <button className="link" onClick={() => setSelectedId(interaction.id)}>
              {interaction.interaction_id} <span className="muted">({interaction.status})</span>
            </button>
          </li>
        ))}
      </ul>
      {selectedId != null && <InteractionDetail id={selectedId} />}
    </div>
  );
}
