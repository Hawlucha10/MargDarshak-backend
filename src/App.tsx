import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import SearchPage from './pages/SearchPage';
import ResultsPage from './pages/ResultsPage';
import { ChatAssistant } from './components/ChatAssistant';
import { ChatProvider } from './context/ChatContext';
import DisclaimerBanner from './components/DisclaimerBanner';

function AppContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const searchParams = new URLSearchParams(location.search);
  const currentOrigin = searchParams.get('origin') || undefined;
  const currentDestination = searchParams.get('destination') || undefined;
  const travelDate = searchParams.get('date') || undefined;

  const handleSelectRoute = (orig: string, dest: string) => {
    navigate(`/results?origin=${encodeURIComponent(orig)}&destination=${encodeURIComponent(dest)}`);
  };

  return (
    <div className="h-[100dvh] max-h-[100dvh] w-full bg-[#E5D5BF] flex flex-col overflow-hidden relative">
      <DisclaimerBanner />
      <main className="flex-1 flex flex-col overflow-hidden min-h-0">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/results" element={<ResultsPage />} />
        </Routes>
      </main>
      <ChatAssistant
        currentOrigin={currentOrigin}
        currentDestination={currentDestination}
        travelDate={travelDate}
        onSelectRoute={handleSelectRoute}
      />
    </div>
  );
}

function App() {
  return (
    <Router>
      <ChatProvider>
        <AppContent />
      </ChatProvider>
    </Router>
  );
}

export default App;
