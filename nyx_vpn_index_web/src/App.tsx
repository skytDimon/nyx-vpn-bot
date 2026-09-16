import { HashRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Pricing } from './pages/Pricing';
import { Guides } from './pages/Guides';

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="pricing" element={<Pricing />} />
          <Route path="guides" element={<Guides />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

export default App;
