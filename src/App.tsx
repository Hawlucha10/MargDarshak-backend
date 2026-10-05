import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SearchPage from './pages/SearchPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Router>
      <div className="h-screen max-h-screen bg-[#E5D5BF] flex flex-col overflow-hidden">
        <main className="flex-1 flex flex-col overflow-hidden">
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
