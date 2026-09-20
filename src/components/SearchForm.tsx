import React, { useState, useEffect } from 'react';
import { 
  ArrowRight, 
  ArrowLeftRight, 
  Calendar, 
  MapPin, 
  Sparkles
} from 'lucide-react';
import { searchStations } from '../api/client';
import type { StationItem } from '../api/types';

interface SearchFormProps {
  onSearch: (params: {
    origin: string;
    destination: string;
    travelDate: string;
    priority: string;
    accessibleOnly: boolean;
  }) => void;
  isLoading: boolean;
}

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, isLoading }) => {
  const [originQuery, setOriginQuery] = useState('GWL');
  const [originSelected, setOriginSelected] = useState<StationItem>({
    code: 'GWL',
    name: 'Gwalior Junction',
    state: 'Madhya Pradesh'
  });
  const [originSuggestions, setOriginSuggestions] = useState<StationItem[]>([]);
  const [showOriginMenu, setShowOriginMenu] = useState(false);

  const [destQuery, setDestQuery] = useState('PUNE');
  const [destSelected, setDestSelected] = useState<StationItem>({
    code: 'PUNE',
    name: 'Pune Junction',
    state: 'Maharashtra'
  });
  const [destSuggestions, setDestSuggestions] = useState<StationItem[]>([]);
  const [showDestMenu, setShowDestMenu] = useState(false);

  // Set default travel date to 7 days from now
  const defaultDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const [travelDate, setTravelDate] = useState(defaultDate);
  const [priority, setPriority] = useState('balanced');
  const [accessibleOnly, setAccessibleOnly] = useState(false);
  const [nlpInput, setNlpInput] = useState('');

  // Debounced station autocomplete for origin
  useEffect(() => {
    if (originQuery.trim().length >= 2 && showOriginMenu) {
      const timer = setTimeout(async () => {
        const results = await searchStations(originQuery);
        setOriginSuggestions(results);
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [originQuery, showOriginMenu]);

  // Debounced station autocomplete for destination
  useEffect(() => {
    if (destQuery.trim().length >= 2 && showDestMenu) {
      const timer = setTimeout(async () => {
        const results = await searchStations(destQuery);
        setDestSuggestions(results);
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [destQuery, showDestMenu]);

  const handleSwap = () => {
    const tempQ = originQuery;
    const tempSel = originSelected;
    setOriginQuery(destQuery);
    setOriginSelected(destSelected);
    setDestQuery(tempQ);
    setDestSelected(tempSel);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!originSelected.code || !destSelected.code) return;
    onSearch({
      origin: originSelected.code,
      destination: destSelected.code,
      travelDate,
      priority,
      accessibleOnly,
    });
  };

  const handleNlpSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nlpInput.trim()) return;
    const lower = nlpInput.toLowerCase();
    
    // Quick keyword matching for common corridors
    if (lower.includes('pune') && (lower.includes('gwalior') || lower.includes('gwl'))) {
      setOriginSelected({ code: 'GWL', name: 'Gwalior Junction' });
      setOriginQuery('GWL');
      setDestSelected({ code: 'PUNE', name: 'Pune Junction' });
      setDestQuery('PUNE');
    } else if (lower.includes('delhi') && lower.includes('mumbai')) {
      setOriginSelected({ code: 'NDLS', name: 'New Delhi' });
      setOriginQuery('NDLS');
      setDestSelected({ code: 'BCT', name: 'Mumbai Central' });
      setDestQuery('BCT');
    }

    if (lower.includes('cheap') || lower.includes('sasta')) {
      setPriority('cheapest');
    } else if (lower.includes('fast') || lower.includes('jaldi')) {
      setPriority('fastest');
    }

    onSearch({
      origin: originSelected.code,
      destination: destSelected.code,
      travelDate,
      priority: lower.includes('cheap') ? 'cheapest' : lower.includes('fast') ? 'fastest' : priority,
      accessibleOnly,
    });
  };

  return (
    <div className="w-full max-w-5xl mx-auto">
      {/* Bauhaus Framing Box */}
      <div className="border border-[#0F172A] bg-white shadow-[6px_6px_0px_0px_#0F172A] p-6 sm:p-8 relative">
        {/* Top Architectural Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#E2DFD7] pb-5 mb-6 gap-3">
          <div>
            <span className="font-mono text-xs uppercase tracking-widest text-[#1D4ED8] font-bold">
              [ 01 ] // ROUTE INITIALIZATION
            </span>
            <h2 className="text-2xl font-black tracking-tight text-[#0F172A] uppercase">
              Plan Intercity Multi-Hop Journey
            </h2>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#64748B]">
            <span className="w-2 h-2 bg-[#D97706] inline-block"></span>
            <span>AGRD ELLIPSE FILTERING ACTIVE</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Origin & Destination Grid */}
          <div className="grid grid-cols-1 md:grid-cols-[1fr,auto,1fr] gap-4 items-center">
            {/* FROM FIELD */}
            <div className="relative">
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-[#475569] mb-1">
                From Station or City
              </label>
              <div className="border border-[#0F172A] bg-[#F8FAFC] flex items-center px-3 py-2.5 focus-within:border-[#1D4ED8] focus-within:bg-white transition-all">
                <MapPin className="w-4 h-4 text-[#1D4ED8] mr-2 shrink-0" />
                <input
                  type="text"
                  value={originQuery}
                  onChange={(e) => {
                    setOriginQuery(e.target.value);
                    setShowOriginMenu(true);
                  }}
                  onFocus={() => setShowOriginMenu(true)}
                  placeholder="e.g. Gwalior or Noida"
                  className="w-full bg-transparent font-mono font-bold text-sm text-[#0F172A] outline-none"
                />
                {originSelected.code && (
                  <span className="ml-2 font-mono text-xs bg-[#0F172A] text-white px-2 py-0.5 font-bold shrink-0">
                    {originSelected.code}
                  </span>
                )}
              </div>

              {/* Origin Autocomplete Dropdown */}
              {showOriginMenu && originSuggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-[#0F172A] shadow-lg z-50 max-h-60 overflow-y-auto">
                  <div className="p-1.5 bg-[#F1EFE9] border-b border-[#E2DFD7] text-[11px] font-mono font-bold text-[#64748B] uppercase">
                    Select Station / Nearby Hub
                  </div>
                  {originSuggestions.map((item) => (
                    <div
                      key={item.code}
                      onClick={() => {
                        setOriginSelected(item);
                        setOriginQuery(item.name);
                        setShowOriginMenu(false);
                      }}
                      className="p-2.5 hover:bg-[#EFF6FF] cursor-pointer border-b border-[#F1EFE9] flex items-center justify-between transition-colors"
                    >
                      <div>
                        <div className="text-sm font-bold text-[#0F172A]">{item.name}</div>
                        <div className="text-xs text-[#64748B] font-mono">
                          {item.state} {item.distance_km !== undefined && item.distance_km > 0 && `(Nearby: ${item.distance_km}km)`}
                        </div>
                      </div>
                      <span className="font-mono text-xs font-bold bg-[#E2DFD7] text-[#0F172A] px-2 py-1">
                        {item.code}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* SWAP BUTTON */}
            <div className="flex justify-center md:pt-5">
              <button
                type="button"
                onClick={handleSwap}
                className="w-9 h-9 border border-[#0F172A] bg-white hover:bg-[#0F172A] hover:text-white flex items-center justify-center transition-colors"
                title="Swap Stations"
              >
                <ArrowLeftRight className="w-4 h-4" />
              </button>
            </div>

            {/* TO FIELD */}
            <div className="relative">
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-[#475569] mb-1">
                To Station or City
              </label>
              <div className="border border-[#0F172A] bg-[#F8FAFC] flex items-center px-3 py-2.5 focus-within:border-[#1D4ED8] focus-within:bg-white transition-all">
                <MapPin className="w-4 h-4 text-[#DC2626] mr-2 shrink-0" />
                <input
                  type="text"
                  value={destQuery}
                  onChange={(e) => {
                    setDestQuery(e.target.value);
                    setShowDestMenu(true);
                  }}
                  onFocus={() => setShowDestMenu(true)}
                  placeholder="e.g. Pune or Mumbai"
                  className="w-full bg-transparent font-mono font-bold text-sm text-[#0F172A] outline-none"
                />
                {destSelected.code && (
                  <span className="ml-2 font-mono text-xs bg-[#0F172A] text-white px-2 py-0.5 font-bold shrink-0">
                    {destSelected.code}
                  </span>
                )}
              </div>

              {/* Destination Autocomplete Dropdown */}
              {showDestMenu && destSuggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-[#0F172A] shadow-lg z-50 max-h-60 overflow-y-auto">
                  <div className="p-1.5 bg-[#F1EFE9] border-b border-[#E2DFD7] text-[11px] font-mono font-bold text-[#64748B] uppercase">
                    Select Station / Nearby Hub
                  </div>
                  {destSuggestions.map((item) => (
                    <div
                      key={item.code}
                      onClick={() => {
                        setDestSelected(item);
                        setDestQuery(item.name);
                        setShowDestMenu(false);
                      }}
                      className="p-2.5 hover:bg-[#EFF6FF] cursor-pointer border-b border-[#F1EFE9] flex items-center justify-between transition-colors"
                    >
                      <div>
                        <div className="text-sm font-bold text-[#0F172A]">{item.name}</div>
                        <div className="text-xs text-[#64748B] font-mono">
                          {item.state} {item.distance_km !== undefined && item.distance_km > 0 && `(Nearby: ${item.distance_km}km)`}
                        </div>
                      </div>
                      <span className="font-mono text-xs font-bold bg-[#E2DFD7] text-[#0F172A] px-2 py-1">
                        {item.code}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Date & Preferences Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
            {/* Travel Date */}
            <div>
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-[#475569] mb-1">
                Travel Date
              </label>
              <div className="border border-[#0F172A] bg-[#F8FAFC] flex items-center px-3 py-2.5">
                <Calendar className="w-4 h-4 text-[#64748B] mr-2 shrink-0" />
                <input
                  type="date"
                  value={travelDate}
                  onChange={(e) => setTravelDate(e.target.value)}
                  className="w-full bg-transparent font-mono font-semibold text-sm text-[#0F172A] outline-none"
                />
              </div>
            </div>

            {/* Pareto Priority Selection */}
            <div>
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-[#475569] mb-1">
                Route Objective
              </label>
              <div className="border border-[#0F172A] bg-[#F8FAFC] flex items-center px-3 py-2.5">
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full bg-transparent font-mono font-semibold text-sm text-[#0F172A] outline-none"
                >
                  <option value="balanced">BALANCED (5-Criteria Pareto)</option>
                  <option value="fastest">FASTEST (Minimum Travel Time)</option>
                  <option value="cheapest">CHEAPEST (Maximum Fare Savings)</option>
                  <option value="reliable">MOST RELIABLE (Highest CDF Score)</option>
                </select>
              </div>
            </div>

            {/* Accessibility Checkbox */}
            <div className="flex items-center sm:col-span-2 lg:col-span-1 border border-[#0F172A] p-3 bg-[#F8FAFC]">
              <input
                type="checkbox"
                id="accessible_check"
                checked={accessibleOnly}
                onChange={(e) => setAccessibleOnly(e.target.checked)}
                className="w-4 h-4 border-[#0F172A] text-[#1D4ED8] rounded-none focus:ring-0 cursor-pointer"
              />
              <label htmlFor="accessible_check" className="ml-2.5 text-xs font-mono font-bold text-[#0F172A] cursor-pointer">
                STEP-FREE WHEELCHAIR RAMPS ONLY (PwD)
              </label>
            </div>
          </div>

          {/* SUBMIT BUTTON */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[#1D4ED8] hover:bg-[#1E40AF] text-white border border-[#0F172A] py-3.5 px-6 font-mono font-extrabold text-sm uppercase tracking-widest flex items-center justify-center space-x-2 shadow-[4px_4px_0px_0px_#0F172A] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer disabled:opacity-50"
            >
              <span>{isLoading ? 'CALCULATING RAPTOR GRAPH...' : 'FIND OPTIMAL ROUTES'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>

        {/* Natural Language Search Box (Bottom Section) */}
        <div className="mt-8 pt-5 border-t border-[#E2DFD7]">
          <div className="flex items-center space-x-2 text-xs font-mono text-[#64748B] mb-2 font-bold uppercase">
            <Sparkles className="w-3.5 h-3.5 text-[#D97706]" />
            <span>Natural Language Conversational Search (English / Hindi)</span>
          </div>
          <form onSubmit={handleNlpSubmit} className="flex gap-2">
            <input
              type="text"
              value={nlpInput}
              onChange={(e) => setNlpInput(e.target.value)}
              placeholder="e.g. 'Cheapest train from Gwalior to Pune next Friday' or 'पुणे से दिल्ली सबसे तेज़'"
              className="w-full border border-[#CBD5E1] px-3 py-2 text-xs font-mono text-[#0F172A] placeholder-[#94A3B8] outline-none focus:border-[#0F172A] bg-[#F8FAFC]"
            />
            <button
              type="submit"
              className="bg-[#0F172A] text-white px-4 py-2 text-xs font-mono font-bold uppercase hover:bg-[#1D4ED8] transition-colors shrink-0"
            >
              Parse & Search
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
