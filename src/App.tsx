import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import SearchPage from './pages/SearchPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-brand-cream flex flex-col">
        <Navbar />
        <main className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/results" element={<ResultsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
