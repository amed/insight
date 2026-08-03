import Nav from './Nav.jsx';
import Interactions from './Interactions.jsx';
import Upload from './Upload.jsx';
import Summary from './Summary.jsx';
import { useNavigation } from '../hooks/useNavigation.js';

// each section key maps to its view
const views = {
  interactions: Interactions,
  upload: Upload,
  insights: Summary,
};

export default function Layout() {
  const { active } = useNavigation();
  const View = views[active];

  return (
    <div className="layout">
      <header className="header">
        <h1>Insight</h1>
        <Nav />
      </header>
      <main className="content">{View ? <View /> : null}</main>
    </div>
  );
}
