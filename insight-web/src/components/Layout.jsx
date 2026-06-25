import Nav from './Nav.jsx';
import Placeholder from './Placeholder.jsx';
import { sections } from '../sections.js';
import { useNavigation } from '../hooks/useNavigation.js';

export default function Layout() {
  const { active } = useNavigation();
  const section = sections.find((s) => s.key === active);

  return (
    <div className="layout">
      <header className="header">
        <h1>Insight</h1>
        <Nav />
      </header>
      <main className="content">
        <Placeholder title={section ? section.label : 'Insight'} />
      </main>
    </div>
  );
}
