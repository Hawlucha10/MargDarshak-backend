import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import StationAutocomplete from './StationAutocomplete';

const DYNAMIC_PLACEHOLDERS = [
  'Delhi to Mumbai before 8 PM...',
  'Howrah to Patna morning superfast...',
  'Bengaluru to Chennai with AC bus option...',
  'Ahmedabad to Jaipur next Friday...',
  'Lucknow to Varanasi fast train...',
  'Chandigarh se Amritsar dopahar mein...',
];

export default function SearchBar() {
  const [originCode, setOriginCode] = useState('');
  const [destCode, setDestCode] = useState('');
  const [originDisplay, setOriginDisplay] = useState('');
  const [destDisplay, setDestDisplay] = useState('');
  
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

  const setNextWeekend = () => {
    const d = new Date();
    const day = d.getDay(); // 0 is Sunday, 6 is Saturday
    const daysUntilSaturday = day === 6 ? 7 : (6 - day);
    d.setDate(d.getDate() + daysUntilSaturday);
    setDate(d.toISOString().split('T')[0]);
  };

  const handleSwap = () => {
    const tmpCode = originCode;
    const tmpDisp = originDisplay;
    setOriginCode(destCode);
    setOriginDisplay(destDisplay);
    setDestCode(tmpCode);
    setDestDisplay(tmpDisp);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (isNlpMode && nlpQuery.trim()) {
      navigate(`/results?nlp=${encodeURIComponent(nlpQuery.trim())}`);
    } else if (originCode && destCode) {
      const dateParam = date || todayStr;
      navigate(`/results?origin=${encodeURIComponent(originCode)}&destination=${encodeURIComponent(destCode)}&date=${dateParam}`);
    }
  };

  // Format date preview
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
      className="bg-white/90 backdrop-blur-xl p-6 sm:p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-stone-200/90 w-full transition-all"
    >
      {/* Mode Toggle: Rectangular with rounded-xl, no capsules */}
      <div className="flex justify-center mb-6">
        <div className="inline-flex bg-stone-100 p-1 rounded-xl border border-stone-200/70 shadow-2xs">
          <button
            type="button"
            onClick={() => setIsNlpMode(false)}
            className={`px-5 py-2 rounded-lg font-[var(--font-ui)] text-xs sm:text-sm font-semibold tracking-wide transition-all ${
              !isNlpMode
                ? 'bg-[#1A2766] text-white shadow-xs'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            Station Search
          </button>
          <button
            type="button"
            onClick={() => setIsNlpMode(true)}
            className={`px-5 py-2 rounded-lg font-[var(--font-ui)] text-xs sm:text-sm font-semibold tracking-wide transition-all ${
              isNlpMode
                ? 'bg-[#1A2766] text-white shadow-xs'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            Ask in Plain Language
          </button>
        </div>
      </div>

      {isNlpMode ? (
        <div className="mb-6 space-y-3">
          <div className="relative">
            <input
              type="text"
              value={nlpQuery}
              onChange={(e) => setNlpQuery(e.target.value)}
              placeholder={`Try: "${DYNAMIC_PLACEHOLDERS[placeholderIdx]}"`}
              className="w-full bg-[#FAF8F5] border border-stone-200 rounded-2xl px-5 py-4 font-[var(--font-ui)] text-stone-900 text-base sm:text-lg outline-none focus:bg-white focus:ring-3 focus:ring-brand-blue/20 focus:border-brand-blue placeholder:text-stone-400 transition-all shadow-2xs"
            />
            {nlpQuery && (
              <button
                type="button"
                onClick={() => setNlpQuery('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-700 text-sm font-bold p-1 rounded-md"
              >
                ✕
              </button>
            )}
          </div>
          <p className="text-xs text-stone-500 font-[var(--font-ui)] px-2">
            Ask naturally in English or Hinglish with timings, preferences, or intermediate bus wishes.
          </p>
        </div>
      ) : (
        <div className="space-y-4 mb-6">
          {/* Origin, Swap, Destination Grid */}
          <div className="grid grid-cols-1 md:grid-cols-[1fr,auto,1fr] gap-3 items-end">
            <div>
              <label className="block text-xs font-[var(--font-ui)] font-semibold text-stone-700 uppercase tracking-wider mb-1.5">
                From Station or City
              </label>
              <StationAutocomplete
                value={originDisplay}
                onChange={(code, name) => {
                  setOriginCode(code);
                  setOriginDisplay(`${name} (${code})`);
                }}
                placeholder="Origin (e.g. NDLS, Mumbai, Pune)"
              />
            </div>

            {/* Swap Button */}
            <div className="flex justify-center pb-1">
              <button
                type="button"
                onClick={handleSwap}
                className="w-10 h-10 rounded-xl border border-stone-200 bg-white hover:bg-stone-50 text-stone-700 flex items-center justify-center transition-all shadow-2xs hover:border-brand-blue active:scale-95 cursor-pointer"
                title="Swap stations"
              >
                <svg className="w-4 h-4 text-[#1A2766]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
              </button>
            </div>

            <div>
              <label className="block text-xs font-[var(--font-ui)] font-semibold text-stone-700 uppercase tracking-wider mb-1.5">
                To Station or City
              </label>
              <StationAutocomplete
                value={destDisplay}
                onChange={(code, name) => {
                  setDestCode(code);
                  setDestDisplay(`${name} (${code})`);
                }}
                placeholder="Destination (e.g. HWH, Chennai, Gwalior)"
              />
            </div>
          </div>

          {/* Date Picker & Quick Select Chips */}
          <div className="pt-2 border-t border-stone-100">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
              <label className="text-xs font-[var(--font-ui)] font-semibold text-stone-700 uppercase tracking-wider">
                Date of Travel
              </label>
              {date && (
                <span className="text-xs font-[var(--font-ui)] font-medium text-brand-blue bg-blue-50 px-2.5 py-0.5 rounded-lg border border-blue-100">
                  {getFormattedDatePreview(date)}
                </span>
              )}
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              {/* Native Date Input with min={todayStr} */}
              <input
                type="date"
                min={todayStr}
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="bg-[#FAF8F5] border border-stone-200 rounded-xl px-4 py-2.5 font-[var(--font-ui)] text-stone-800 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-brand-blue/30 focus:border-brand-blue transition-all cursor-pointer"
              />

              {/* Quick Select Chips */}
              <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
                <button
                  type="button"
                  onClick={() => setQuickDate(0)}
                  className={`px-3 py-2 rounded-xl text-xs font-[var(--font-ui)] font-semibold border transition-all ${
                    date === todayStr
                      ? 'bg-[#1A2766] text-white border-[#1A2766] shadow-xs'
                      : 'bg-white border-stone-200 text-stone-700 hover:bg-stone-50'
                  }`}
                >
                  Today
                </button>
                <button
                  type="button"
                  onClick={() => setQuickDate(1)}
                  className={`px-3 py-2 rounded-xl text-xs font-[var(--font-ui)] font-semibold border transition-all ${
                    date === new Date(Date.now() + 86400000).toISOString().split('T')[0]
                      ? 'bg-[#1A2766] text-white border-[#1A2766] shadow-xs'
                      : 'bg-white border-stone-200 text-stone-700 hover:bg-stone-50'
                  }`}
                >
                  Tomorrow
                </button>
                <button
                  type="button"
                  onClick={setNextWeekend}
                  className="px-3 py-2 rounded-xl text-xs font-[var(--font-ui)] font-semibold border bg-white border-stone-200 text-stone-700 hover:bg-stone-50 transition-all"
                >
                  This Weekend
                </button>
                <button
                  type="button"
                  onClick={() => setQuickDate(7)}
                  className="px-3 py-2 rounded-xl text-xs font-[var(--font-ui)] font-semibold border bg-white border-stone-200 text-stone-700 hover:bg-stone-50 transition-all"
                >
                  +1 Week
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Submit Button: No capsule, elegant rounded-2xl */}
      <button
        type="submit"
        className="w-full bg-[#1A2766] hover:bg-[#121B47] text-white font-[var(--font-ui)] font-bold text-base rounded-2xl py-4 transition-all shadow-[0_4px_16px_rgba(26,39,102,0.18)] hover:shadow-[0_6px_20px_rgba(26,39,102,0.25)] hover:-translate-y-0.5 active:translate-y-0 cursor-pointer flex items-center justify-center gap-2"
      >
        <span>Search Optimal Routes</span>
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
        </svg>
      </button>
    </form>
  );
}
