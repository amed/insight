import { NavigationProvider } from './context/NavigationContext.jsx';
import Layout from './components/Layout.jsx';

export default function App() {
  return (
    <NavigationProvider>
      <Layout />
    </NavigationProvider>
  );
}
