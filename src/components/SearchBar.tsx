import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import StationAutocomplete from './StationAutocomplete';
import CustomDatePicker from './CustomDatePicker';
import { getRecentSearches, saveRecentSearch, type RecentSearchItem } from '../utils/recentSearches';

const DYNAMIC_PLACEHOLDERS = [
  'Delhi to Mumbai before 8 PM...',
  'Howrah to Patna morning superfast...',
  'Bengaluru to Chennai with AC bus option...',
  'Ahmedabad to Jaipur next Friday...',
  'Lucknow to Varanasi fast train...',
  'Chandigarh se Amritsar dopahar mein...',
];

const API_BASE = import.meta.env.VITE_API_URL || '';

export default function SearchBar() {
  const [originCode, setOriginCode] = useState('');
  const [destCode, setDestCode] = useState('');
  const [originDisplay, setOriginDisplay] = useState('');
  const [destDisplay, setDestDisplay] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  
  // Disallow past dates
  const todayStr = new Date().toISOString().split('T')[0];
  const [date, setDate] = useState(todayStr);
  
  const [nlpQuery, setNlpQuery] = useState('');
  const [isNlpMode, setIsNlpMode] = useState(false);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const [recentSearches, setRecentSearches] = useState<RecentSearchItem[]>([]);
  const navigate = useNavigate();

  // Load and subscribe to recent searches
  useEffect(() => {
    setRecentSearches(getRecentSearches());
    const handleUpdate = () => setRecentSearches(getRecentSearches());
    window.addEventListener('recentSearchesUpdated', handleUpdate);
    return () => window.removeEventListener('recentSearchesUpdated', handleUpdate);
  }, []);

  // Dynamic placeholder cycling for NLP search
  useEffect(() => {
    const timer = setInterval(() => {
      setPlaceholderIdx((prev) => (prev + 1) % DYNAMIC_PLACEHOLDERS.length);
    }, 3500);
    return () => clearInterval(timer);
  }, []);

  // Quick Date Helpers
  const setQuickDate = (daysAhead: number) => {
    const d = new Date();
    d.setDate(d.getDate() + daysAhead);
    setDate(d.toISOString().split('T')[0]);
  };

  const handleSwap = () => {
    const tmpCode = originCode;
    const tmpDisp = originDisplay;
    setOriginCode(destCode);
    setOriginDisplay(destDisplay);
    setDestCode(tmpCode);
    setDestDisplay(tmpDisp);
    setErrorMsg('');
  };

  const resolveStation = async (displayStr: string, currentCode: string): Promise<string> => {
    if (currentCode) return currentCode;
    const trimmed = displayStr.trim();
    if (!trimmed) return '';

    // Match parenthesized station code e.g. "NEW DELHI (NDLS)" -> "NDLS"
    const match = trimmed.match(/\(([A-Za-z0-9]+)\)$/);
    if (match) return match[1].toUpperCase();

    // Direct 2-5 letter code entered e.g. "NDLS"
    if (/^[A-Za-z]{2,5}$/.test(trimmed)) {
      return trimmed.toUpperCase();
    }

    // Auto-resolve against stations API
    try {
      const res = await fetch(`${API_BASE}/api/v1/stations/autocomplete?q=${encodeURIComponent(trimmed)}`);
      if (res.ok) {
        const list = await res.json();
        if (list && list.length > 0) return list[0].code;
      }
    } catch {}

    return '';
  };

  const handleSelectRecent = (item: RecentSearchItem) => {
    if (item.type === 'station' && item.originCode && item.destCode) {
      setOriginCode(item.originCode);
      setOriginDisplay(item.origin || item.originCode);
      setDestCode(item.destCode);
      setDestDisplay(item.destination || item.destCode);
      const dateParam = date || todayStr;
      navigate(`/results?origin=${encodeURIComponent(item.originCode)}&destination=${encodeURIComponent(item.destCode)}&date=${dateParam}`);
    } else if (item.query) {
      setNlpQuery(item.query);
      navigate(`/results?nlp=${encodeURIComponent(item.query)}`);
    } else if (item.label) {
      setNlpQuery(item.label);
      navigate(`/results?nlp=${encodeURIComponent(item.label)}`);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (isNlpMode) {
      if (nlpQuery.trim()) {
        saveRecentSearch({
          type: 'nlp',
          query: nlpQuery.trim(),
          label: nlpQuery.trim(),
        });
        navigate(`/results?nlp=${encodeURIComponent(nlpQuery.trim())}`);
      } else {
        setErrorMsg('Please enter your travel query or destination.');
      }
      return;
    }

    const finalOrigin = await resolveStation(originDisplay, originCode);
    const finalDest = await resolveStation(destDisplay, destCode);

    if (finalOrigin && finalDest) {
      const dateParam = date || todayStr;
      saveRecentSearch({
        type: 'station',
        origin: originDisplay || finalOrigin,
        originCode: finalOrigin,
        destination: destDisplay || finalDest,
        destCode: finalDest,
        label: `${finalOrigin} → ${finalDest}`,
        date: dateParam,
      });
      navigate(`/results?origin=${encodeURIComponent(finalOrigin)}&destination=${encodeURIComponent(finalDest)}&date=${dateParam}`);
    } else {
      if (!finalOrigin && !finalDest) {
        setErrorMsg('Please choose your departure and arrival stations.');
      } else if (!finalOrigin) {
        setErrorMsg('Please select a valid origin station.');
      } else {
        setErrorMsg('Please select a valid destination station.');
      }
    }
  };

  // Format date preview using Timeless font
  const getFormattedDatePreview = (isoDate: string) => {
    try {
      const [year, month, day] = isoDate.split('-').map(Number);
      const d = new Date(year, month - 1, day);
      return d.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' });
    } catch {
      return isoDate;
    }
  };

  return (
    <form
      onSubmit={handleSearch}
      className="bg-[#F6F0E6] p-4 sm:p-6 rounded-2xl sm:rounded-3xl shadow-[0_12px_36px_rgba(74,93,48,0.12)] border border-[#4A5D30]/20 w-full transition-all font-['OFLGoudyStM'] backdrop-blur-sm"
    >
      {/* Mode Toggle: Symmetrical equal width boxes (exact same size for both options) */}
      <div className="flex justify-center mb-2.5 sm:mb-4">
        <div className="inline-flex items-center bg-[#E5D5BF]/75 p-1 rounded-full border border-[#4A5D30]/20 shadow-inner w-full max-w-[370px]">
          <button
            type="button"
            onClick={() => {
              setIsNlpMode(false);
              setErrorMsg('');
            }}
            className={`flex-1 h-9 sm:h-9.5 px-3 rounded-full text-[14px] sm:text-[16px] font-semibold tracking-wide transition-all cursor-pointer inline-flex items-center justify-center leading-none text-center ${
              !isNlpMode
                ? 'bg-[#4A5D30] text-[#F6F0E6] shadow-sm'
                : 'text-stone-700 hover:text-stone-950'
            }`}
          >
            <span className="translate-y-[0.5px]">Station Search</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setIsNlpMode(true);
              setErrorMsg('');
            }}
            className={`flex-1 h-9 sm:h-9.5 px-3 rounded-full text-[14px] sm:text-[16px] font-semibold tracking-wide transition-all cursor-pointer inline-flex items-center justify-center leading-none text-center ${
              isNlpMode
                ? 'bg-[#4A5D30] text-[#F6F0E6] shadow-sm'
                : 'text-stone-700 hover:text-stone-950'
            }`}
          >
            <span className="translate-y-[0.5px]">Type it up</span>
          </button>
        </div>
      </div>

      {/* Content Panels: Superposed in CSS Grid so the whole box keeps the exact same size */}
      <div className="grid grid-cols-1 grid-rows-1 mb-4">
        {/* Panel 1: Station Search */}
        <div
          className={`col-start-1 row-start-1 space-y-3.5 transition-opacity duration-150 ${
            !isNlpMode
              ? 'opacity-100 relative z-10'
              : 'opacity-0 pointer-events-none invisible select-none'
          }`}
          aria-hidden={isNlpMode}
        >
          {/* Origin, Swap, Destination in a SINGLE COMPACT LINE */}
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="flex-1 min-w-0">
              <label className="block text-[14px] sm:text-[15px] font-semibold text-stone-700 uppercase tracking-wider mb-1 font-['OFLGoudyStM']">
                From Station or City
              </label>
              <StationAutocomplete
                value={originDisplay}
                disabled={isNlpMode}
                onChange={(code, name) => {
                  setOriginCode(code);
                  setOriginDisplay(`${name} (${code})`);
                }}
                placeholder="Origin (e.g. NDLS, Pune)"
              />
            </div>

            {/* Swap Button */}
            <div className="pt-5 sm:pt-6 shrink-0">
              <button
                type="button"
                disabled={isNlpMode}
                onClick={handleSwap}
                className="w-10 h-10 sm:w-10.5 sm:h-10.5 rounded-xl border border-[#4A5D30]/25 bg-[#FAF7F2] hover:bg-[#E5D5BF] text-[#4A5D30] flex items-center justify-center transition-all shadow-2xs hover:border-[#4A5D30] active:scale-95 cursor-pointer disabled:opacity-50"
                title="Swap stations"
              >
                <svg className="w-4 h-4 text-[#4A5D30]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
              </button>
            </div>

            <div className="flex-1 min-w-0">
              <label className="block text-[14px] sm:text-[15px] font-semibold text-stone-700 uppercase tracking-wider mb-1 font-['OFLGoudyStM']">
                To Station or City
              </label>
              <StationAutocomplete
                value={destDisplay}
                disabled={isNlpMode}
                onChange={(code, name) => {
                  setDestCode(code);
                  setDestDisplay(`${name} (${code})`);
                }}
                placeholder="Destination (e.g. HWH, Gwalior)"
              />
            </div>
          </div>

          {/* Date Picker & Quick Select Chips with Timeless font */}
          <div className="pt-2.5 border-t border-[#4A5D30]/15">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
              <div className="flex items-center gap-2">
                <label className="text-[12px] sm:text-[13px] font-semibold text-stone-700 uppercase tracking-wider shrink-0 font-['OFLGoudyStM'] leading-none">
                  Date:
                </label>
                <CustomDatePicker
                  value={date}
                  onChange={setDate}
                  minDate={todayStr}
                  disabled={isNlpMode}
                />
                {date && (
                  <span className="hidden sm:inline-flex h-8 sm:h-8.5 items-center justify-center px-2.5 rounded-full text-[12px] sm:text-[13px] font-medium text-[#4A5D30] bg-[#E5D5BF]/60 border border-[#4A5D30]/20 font-['Timeless'] leading-none whitespace-nowrap">
                    <span className="translate-y-[0.5px]">{getFormattedDatePreview(date)}</span>
                  </span>
                )}
              </div>

              {/* Quick Select Chips using Timeless font & rounded-full */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 sm:pb-0 font-['Timeless']">
                <button
                  type="button"
                  disabled={isNlpMode}
                  onClick={() => setQuickDate(0)}
                  className={`px-3.5 sm:px-4 h-8 sm:h-8.5 rounded-full text-[12px] sm:text-[13px] font-semibold border transition-all cursor-pointer inline-flex items-center justify-center leading-none whitespace-nowrap ${
                    date === todayStr
                      ? 'bg-[#4A5D30] text-[#F6F0E6] border-[#4A5D30] shadow-xs'
                      : 'bg-[#FAF7F2] border-[#4A5D30]/20 text-stone-700 hover:bg-[#E5D5BF]'
                  }`}
                >
                  <span className="translate-y-[0.5px]">Today</span>
                </button>
                <button
                  type="button"
                  disabled={isNlpMode}
                  onClick={() => setQuickDate(1)}
                  className={`px-3.5 sm:px-4 h-8 sm:h-8.5 rounded-full text-[12px] sm:text-[13px] font-semibold border transition-all cursor-pointer inline-flex items-center justify-center leading-none whitespace-nowrap ${
                    date === new Date(Date.now() + 86400000).toISOString().split('T')[0]
                      ? 'bg-[#4A5D30] text-[#F6F0E6] border-[#4A5D30] shadow-xs'
                      : 'bg-[#FAF7F2] border-[#4A5D30]/20 text-stone-700 hover:bg-[#E5D5BF]'
                  }`}
                >
                  <span className="translate-y-[0.5px]">Tomorrow</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Panel 2: Ask in Plain Language */}
        <div
          className={`col-start-1 row-start-1 space-y-3.5 transition-opacity duration-150 ${
            isNlpMode
              ? 'opacity-100 relative z-10'
              : 'opacity-0 pointer-events-none invisible select-none'
          }`}
          aria-hidden={!isNlpMode}
        >
          {/* Query Input with Matching Label Height */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-[14px] sm:text-[15px] font-semibold text-stone-700 uppercase tracking-wider font-['OFLGoudyStM']">
                Type it up (Hindi, Hinglish, English)
              </label>
            </div>
            <div className="relative">
              <input
                type="text"
                value={nlpQuery}
                onChange={(e) => setNlpQuery(e.target.value)}
                disabled={!isNlpMode}
                placeholder={`Try: "${DYNAMIC_PLACEHOLDERS[placeholderIdx]}"`}
                className="w-full bg-[#FAF7F2] border border-[#4A5D30]/25 rounded-xl px-3.5 py-2.5 font-['Timeless'] text-[#111111] text-[16px] sm:text-[17px] outline-none focus:bg-white focus:ring-2 focus:ring-[#4A5D30]/30 focus:border-[#4A5D30] placeholder:text-stone-400 transition-all shadow-2xs"
              />
              {nlpQuery && (
                <button
                  type="button"
                  onClick={() => setNlpQuery('')}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-stone-400 hover:text-[#4A5D30] text-sm font-bold p-1 cursor-pointer"
                  title="Clear query"
                >
                  ✕
                </button>
              )}
            </div>
          </div>

          {/* Quick Example Chips with Identical Height to Date Row */}
          <div className="pt-2.5 border-t border-[#4A5D30]/15">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
              <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 sm:pb-0">
                <span className="text-[12px] sm:text-[13px] font-semibold text-stone-700 uppercase tracking-wider shrink-0 font-['OFLGoudyStM'] leading-none">
                  {recentSearches.length > 0 ? 'Recent:' : 'Try:'}
                </span>
                <div className="flex items-center gap-1.5 font-['Timeless']">
                  {recentSearches.length > 0 ? (
                    <>
                      {recentSearches.map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          disabled={!isNlpMode}
                          onClick={() => handleSelectRecent(item)}
                          className="h-8 sm:h-8.5 px-3 rounded-full text-[12px] sm:text-[13px] font-semibold border bg-[#FAF7F2] border-[#4A5D30]/20 text-[#4A5D30] hover:bg-[#E5D5BF] transition-all cursor-pointer inline-flex items-center justify-center leading-none whitespace-nowrap active:scale-95"
                          title={`Search ${item.label}`}
                        >
                          <span className="translate-y-[0.5px]">{item.label}</span>
                        </button>
                      ))}
                      {recentSearches.length === 1 && (
                        <button
                          type="button"
                          disabled={!isNlpMode}
                          onClick={() => {
                            setNlpQuery('Delhi to Mumbai before 8 PM');
                            navigate(`/results?nlp=${encodeURIComponent('Delhi to Mumbai before 8 PM')}`);
                          }}
                          className="h-8 sm:h-8.5 px-3 rounded-full text-[12px] sm:text-[13px] font-semibold border bg-[#FAF7F2] border-[#4A5D30]/20 text-stone-700 hover:bg-[#E5D5BF] transition-all cursor-pointer inline-flex items-center justify-center leading-none whitespace-nowrap active:scale-95"
                        >
                          <span className="translate-y-[0.5px]">Delhi → Mumbai</span>
                        </button>
                      )}
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        disabled={!isNlpMode}
                        onClick={() => {
                          setNlpQuery('Pune se Gwalior agle hafte subah');
                          navigate(`/results?nlp=${encodeURIComponent('Pune se Gwalior agle hafte subah')}`);
                        }}
                        className="h-8 sm:h-8.5 px-3 rounded-full text-[12px] sm:text-[13px] font-semibold border bg-[#FAF7F2] border-[#4A5D30]/20 text-stone-700 hover:bg-[#E5D5BF] transition-all cursor-pointer inline-flex items-center justify-center leading-none whitespace-nowrap active:scale-95"
                      >
                        <span className="translate-y-[0.5px]">Pune → Gwalior</span>
                      </button>
                      <button
                        type="button"
                        disabled={!isNlpMode}
                        onClick={() => {
                          setNlpQuery('Delhi to Mumbai before 8 PM');
                          navigate(`/results?nlp=${encodeURIComponent('Delhi to Mumbai before 8 PM')}`);
                        }}
                        className="h-8 sm:h-8.5 px-3 rounded-full text-[12px] sm:text-[13px] font-semibold border bg-[#FAF7F2] border-[#4A5D30]/20 text-stone-700 hover:bg-[#E5D5BF] transition-all cursor-pointer inline-flex items-center justify-center leading-none whitespace-nowrap active:scale-95"
                      >
                        <span className="translate-y-[0.5px]">Delhi → Mumbai</span>
                      </button>
                    </>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0 font-['Timeless']">
                <span className="h-8 sm:h-8.5 inline-flex items-center justify-center px-2.5 rounded-full text-[12px] sm:text-[13px] font-semibold text-[#4A5D30] bg-[#E5D5BF]/60 border border-[#4A5D30]/20 leading-none whitespace-nowrap">
                  <span className="translate-y-[0.5px]">Bus & Train Aware</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Error feedback if fields are incomplete */}
      {errorMsg && (
        <div className="mb-3 px-4 py-2 rounded-xl bg-[#E5D5BF]/80 border border-[#4A5D30]/30 text-[#4A5D30] font-semibold text-[14px] sm:text-[16px] text-center">
          {errorMsg}
        </div>
      )}

      {/* Submit Button in GREEN */}
      <button
        type="submit"
        className="w-full bg-[#4A5D30] hover:bg-[#3D4C27] text-[#F6F0E6] font-bold text-[16px] sm:text-[18px] rounded-xl py-3 sm:py-3.5 transition-all shadow-[0_4px_16px_rgba(74,93,48,0.20)] hover:shadow-[0_6px_20px_rgba(74,93,48,0.30)] hover:-translate-y-0.5 active:translate-y-0 cursor-pointer flex items-center justify-center gap-2"
      >
        <span>Search Optimal Routes</span>
        <svg className="w-4.5 h-4.5 text-[#F6F0E6]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
        </svg>
      </button>

      {/* Recent Searches Quick Suggestions (Last 2 cached searches) */}
      {recentSearches.length > 0 && (
        <div className="mt-2.5 hidden sm:flex items-center justify-center gap-2 flex-wrap font-['Timeless'] text-xs">
          <span className="text-stone-600 font-medium font-['OFLGoudyStM']">Recent:</span>
          {recentSearches.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => handleSelectRecent(item)}
              className="px-3 py-1 rounded-full bg-[#FAF7F2] hover:bg-[#E5D5BF] border border-[#4A5D30]/25 text-[#4A5D30] font-semibold transition-all cursor-pointer text-xs flex items-center gap-1 active:scale-95"
              title={`Quick search ${item.label}`}
            >
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </form>
  );
}
