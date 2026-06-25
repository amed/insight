import { createContext, useState } from 'react';
import { sections } from '../sections.js';

export const NavigationContext = createContext(null);

export function NavigationProvider({ children }) {
  const [active, setActive] = useState(sections[0].key);

  return (
    <NavigationContext.Provider value={{ active, setActive }}>
      {children}
    </NavigationContext.Provider>
  );
}
