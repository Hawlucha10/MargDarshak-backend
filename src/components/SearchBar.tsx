import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import StationAutocomplete from './StationAutocomplete';
import CustomDatePicker from './CustomDatePicker';

const DYNAMIC_PLACEHOLDERS = [
  'Delhi to Mumbai before 8 PM...',
  'Howrah to Patna morning superfast...',
  'Bengaluru to Chennai with AC bus option...',
  'Ahmedabad to Jaipur next Friday...',
  'Lucknow to Varanasi fast train...',
  'Chandigarh se Amritsar dopahar mein...',
];

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
  const navigate = useNavigate();

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

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (isNlpMode) {
      if (nlpQuery.trim()) {
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
      className="bg-[#F6F0E6] p-6 sm:p-7 rounded-2xl sm:rounded-3xl shadow-[0_12px_36px_rgba(74,93,48,0.12)] border border-[#4A5D30]/20 w-full transition-all font-['OFLGoudyStM'] backdrop-blur-sm"
    >
      {/* Mode Toggle: Symmetrical equal width boxes (exact same size for both options) */}
      <div className="flex justify-center mb-5">
        <div className="inline-flex items-center bg-[#E5D5BF]/75 p-1 rounded-full border border-[#4A5D30]/20 shadow-inner w-full max-w-[440px]">
          <button
            type="button"
            onClick={() => {
              setIsNlpMode(false);
              setErrorMsg('');
            }}
            className={`flex-1 h-10 sm:h-11 px-3 sm:px-4 rounded-full text-[17px] sm:text-[19px] font-semibold tracking-wide transition-all cursor-pointer inline-flex items-center justify-center leading-none text-center ${
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
            className={`flex-1 h-10 sm:h-11 px-3 sm:px-4 rounded-full text-[17px] sm:text-[19px] font-semibold tracking-wide transition-all cursor-pointer inline-flex items-center justify-center leading-none text-center ${
              isNlpMode
                ? 'bg-[#4A5D30] text-[#F6F0E6] shadow-sm'
                : 'text-stone-700 hover:text-stone-950'
            }`}
          >
            <span className="translate-y-[0.5px]">Ask in Plain Language</span>
          </button>
        </div>
      </div>

      {/* Content Panels: Superposed in CSS Grid so the whole box keeps the exact same size */}
      <div className="grid grid-cols-1 grid-rows-1 mb-5">
        {/* Panel 1: Station Search */}
        <div
          className={`col-start-1 row-start-1 space-y-4 transition-opacity duration-150 ${
            !isNlpMode
              ? 'opacity-100 relative z-10'
              : 'opacity-0 pointer-events-none invisible select-none'
          }`}
          aria-hidden={isNlpMode}
        >
          {/* Origin, Swap, Destination in a SINGLE COMPACT LINE */}
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="flex-1 min-w-0">
              <label className="block text-[17px] sm:text-[18px] font-semibold text-stone-700 uppercase tracking-wider mb-1.5 font-['OFLGoudyStM']">
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
            <div className="pt-7 shrink-0">
              <button
                type="button"
                disabled={isNlpMode}
                onClick={handleSwap}
                className="w-11 h-11 sm:w-12 sm:h-12 rounded-xl border border-[#4A5D30]/25 bg-[#FAF7F2] hover:bg-[#E5D5BF] text-[#4A5D30] flex items-center justify-center transition-all shadow-2xs hover:border-[#4A5D30] active:scale-95 cursor-pointer disabled:opacity-50"
                title="Swap stations"
              >
                <svg className="w-5 h-5 text-[#4A5D30]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
              </button>
            </div>

            <div className="flex-1 min-w-0">
              <label className="block text-[17px] sm:text-[18px] font-semibold text-stone-700 uppercase tracking-wider mb-1.5 font-['OFLGoudyStM']">
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
          <div className="pt-3 border-t border-[#4A5D30]/15">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <label className="text-[17px] sm:text-[18px] font-semibold text-stone-700 uppercase tracking-wider shrink-0 font-['OFLGoudyStM'] leading-none">
                  Date:
                </label>
                <CustomDatePicker
                  value={date}
                  onChange={setDate}
                  minDate={todayStr}
                  disabled={isNlpMode}
                />
                {date && (
                  <span className="hidden sm:inline-flex h-11 sm:h-12 items-center justify-center px-4 rounded-full text-[18px] sm:text-[19px] font-semibold text-[#4A5D30] bg-[#E5D5BF]/60 border border-[#4A5D30]/20 font-['Timeless'] leading-none">
                    <span className="translate-y-[0.5px]">{getFormattedDatePreview(date)}</span>
                  </span>
                )}
              </div>

              {/* Quick Select Chips using Timeless font & rounded-full */}
              <div className="flex items-center gap-2 overflow-x-auto pb-0.5 sm:pb-0 font-['Timeless']">
                <button
                  type="button"
                  disabled={isNlpMode}
                  onClick={() => setQuickDate(0)}
                  className={`w-28 sm:w-32 h-11 sm:h-12 rounded-full text-[17px] sm:text-[18.5px] font-semibold border transition-all cursor-pointer inline-flex items-center justify-center leading-none ${
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
                  className={`w-28 sm:w-32 h-11 sm:h-12 rounded-full text-[17px] sm:text-[18.5px] font-semibold border transition-all cursor-pointer inline-flex items-center justify-center leading-none ${
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
          className={`col-start-1 row-start-1 space-y-4 transition-opacity duration-150 ${
            isNlpMode
              ? 'opacity-100 relative z-10'
              : 'opacity-0 pointer-events-none invisible select-none'
          }`}
          aria-hidden={!isNlpMode}
        >
          {/* Query Input with Matching Label Height (Groq AI badge removed) */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-[17px] sm:text-[18px] font-semibold text-stone-700 uppercase tracking-wider font-['OFLGoudyStM']">
                Ask in Plain Language (Hindi, Hinglish, English)
              </label>
            </div>
            <div className="relative">
              <input
                type="text"
                value={nlpQuery}
                onChange={(e) => setNlpQuery(e.target.value)}
                disabled={!isNlpMode}
                placeholder={`Try: "${DYNAMIC_PLACEHOLDERS[placeholderIdx]}"`}
                className="w-full bg-[#FAF7F2] border border-[#4A5D30]/25 rounded-xl px-4 py-3 font-['Timeless'] text-[#111111] text-[19px] sm:text-[20px] outline-none focus:bg-white focus:ring-2 focus:ring-[#4A5D30]/30 focus:border-[#4A5D30] placeholder:text-stone-400 transition-all shadow-2xs"
              />
              {nlpQuery && (
                <button
                  type="button"
                  onClick={() => setNlpQuery('')}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-stone-400 hover:text-[#4A5D30] text-base font-bold p-1 cursor-pointer"
                  title="Clear query"
                >
                  ✕
                </button>
              )}
            </div>
          </div>

          {/* Quick Example Chips with Identical Height to Date Row */}
          <div className="pt-3 border-t border-[#4A5D30]/15">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2 overflow-x-auto pb-0.5 sm:pb-0">
                <span className="text-[17px] sm:text-[18px] font-semibold text-stone-700 uppercase tracking-wider shrink-0 font-['OFLGoudyStM'] leading-none">
                  Try:
                </span>
                <div className="flex items-center gap-2 font-['Timeless']">
                  <button
                    type="button"
                    disabled={!isNlpMode}
                    onClick={() => setNlpQuery('Pune se Gwalior agle hafte subah')}
                    className="h-11 sm:h-12 px-4 rounded-full text-[17px] sm:text-[18px] font-semibold border bg-[#FAF7F2] border-[#4A5D30]/20 text-stone-700 hover:bg-[#E5D5BF] transition-all cursor-pointer inline-flex items-center justify-center leading-none active:scale-95"
                  >
                    <span className="translate-y-[0.5px]">Pune → Gwalior</span>
                  </button>
                  <button
                    type="button"
                    disabled={!isNlpMode}
                    onClick={() => setNlpQuery('Delhi to Mumbai before 8 PM')}
                    className="h-11 sm:h-12 px-4 rounded-full text-[17px] sm:text-[18px] font-semibold border bg-[#FAF7F2] border-[#4A5D30]/20 text-stone-700 hover:bg-[#E5D5BF] transition-all cursor-pointer inline-flex items-center justify-center leading-none active:scale-95"
                  >
                    <span className="translate-y-[0.5px]">Delhi → Mumbai</span>
                  </button>
                  <button
                    type="button"
                    disabled={!isNlpMode}
                    onClick={() => setNlpQuery('Kanpur se Lucknow sabse sasta')}
                    className="hidden md:inline-flex h-11 sm:h-12 px-4 rounded-full text-[17px] sm:text-[18px] font-semibold border bg-[#FAF7F2] border-[#4A5D30]/20 text-stone-700 hover:bg-[#E5D5BF] transition-all cursor-pointer items-center justify-center leading-none active:scale-95"
                  >
                    <span className="translate-y-[0.5px]">Kanpur → Lucknow</span>
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0 font-['Timeless']">
                <span className="h-11 sm:h-12 inline-flex items-center justify-center px-4 rounded-full text-[17px] sm:text-[18px] font-semibold text-[#4A5D30] bg-[#E5D5BF]/60 border border-[#4A5D30]/20 leading-none">
                  <span className="translate-y-[0.5px]">Bus & Train Aware</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Error feedback if fields are incomplete */}
      {errorMsg && (
        <div className="mb-4 px-5 py-2.5 rounded-xl bg-[#E5D5BF]/80 border border-[#4A5D30]/30 text-[#4A5D30] font-semibold text-[17px] sm:text-[19px] text-center">
          {errorMsg}
        </div>
      )}

      {/* Submit Button in GREEN */}
      <button
        type="submit"
        className="w-full bg-[#4A5D30] hover:bg-[#3D4C27] text-[#F6F0E6] font-bold text-[19px] sm:text-[21px] rounded-xl py-3.5 sm:py-4 transition-all shadow-[0_4px_16px_rgba(74,93,48,0.20)] hover:shadow-[0_6px_20px_rgba(74,93,48,0.30)] hover:-translate-y-0.5 active:translate-y-0 cursor-pointer flex items-center justify-center gap-2.5"
      >
        <span>Search Optimal Routes</span>
        <svg className="w-5 h-5 text-[#F6F0E6]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
        </svg>
      </button>
    </form>
  );
}
