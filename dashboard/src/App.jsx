import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Overview from './pages/Overview';
import PipelineDemo from './pages/PipelineDemo';
import ThemeDetail from './pages/ThemeDetail';
import ViewMorePage from './pages/ViewMorePage';
import Vergelijken from './pages/Vergelijken';
import { VectorDBProvider } from './context/VectorDBContext';

function App() {
  return (
    <VectorDBProvider>
      <Router>
        <NavBar />
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/pipeline-demo" element={<PipelineDemo />} />
          <Route path="/thema/:id" element={<ViewMorePage />} />
          <Route path="/thema/:id/subtheme/:subthemeName" element={<ViewMorePage />} />
          <Route path="/theme/:id" element={<ThemeDetail />} />
          <Route path="/vergelijken" element={<Vergelijken />} />
        </Routes>
      </Router>
    </VectorDBProvider>
  );
}

export default App;
