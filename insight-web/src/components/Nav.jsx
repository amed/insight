import { sections } from '../sections.js';
import { useNavigation } from '../hooks/useNavigation.js';

export default function Nav() {
  const { active, setActive } = useNavigation();

  return (
    <nav className="nav">
      {sections.map((section) => (
        <button
          key={section.key}
          className={section.key === active ? 'nav-item active' : 'nav-item'}
          onClick={() => setActive(section.key)}
        >
          {section.label}
        </button>
      ))}
    </nav>
  );
}
