import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Overview from './pages/Overview';
import PipelineDemo from './pages/PipelineDemo';
import ThemeDetail from './pages/ThemeDetail';
import Vergelijken from './pages/Vergelijken';
import Presentatie from './pages/Presentatie';
import NSEDeck from './pages/NSEDeck';
import { VectorDBProvider } from './context/VectorDBContext';

function App() {
  return (
    <VectorDBProvider>
      <Router>
        <NavBar />
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/pipeline-demo" element={<PipelineDemo />} />
          <Route path="/theme/:id" element={<ThemeDetail />} />
          <Route path="/vergelijken" element={<Vergelijken />} />
          <Route path="/presentatie" element={<Presentatie />} />
          <Route path="/presentatie/nse-deck" element={<NSEDeck />} />
        </Routes>
      </Router>
    </VectorDBProvider>
  );
}

export default App;
