import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Resumes } from './pages/Resumes';
import { PhoneLinks } from './pages/PhoneLinks';
import { CallHistory } from './pages/CallHistory';
import { Configuration } from './pages/Configuration';
import { Guide } from './pages/Guide';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/resumes" element={<Resumes />} />
          <Route path="/phone-links" element={<PhoneLinks />} />
          <Route path="/calls" element={<CallHistory />} />
          <Route path="/guide" element={<Guide />} />
          <Route path="/config" element={<Configuration />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
