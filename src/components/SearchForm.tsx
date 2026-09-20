import React, { useState } from 'react';
import { 
  ArrowRight, 
  ArrowLeftRight, 
  Calendar, 
  Sparkles,
  Sliders
} from 'lucide-react';
import { StationInput } from './StationInput';
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
  const [originSelected, setOriginSelected] = useState<StationItem>({
    code: 'GWL',
    name: 'GWALIOR JN',
    zone: 'NCR',
    state: 'Madhya Pradesh',
    is_hub: true,
  });

  const [destSelected, setDestSelected] = useState<StationItem>({
    code: 'PUNE',
    name: 'PUNE JN',
    zone: 'CR',
    state: 'Maharashtra',
    is_hub: true,
  });

  // Set default travel date to 7 days from now
  const defaultDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const [travelDate, setTravelDate] = useState(defaultDate);
  const [priority, setPriority] = useState('balanced');
  const [accessibleOnly, setAccessibleOnly] = useState(false);
  const [nlpInput, setNlpInput] = useState('');

  const handleSwap = () => {
    const temp = originSelected;
    setOriginSelected(destSelected);
    setDestSelected(temp);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!originSelected?.code || !destSelected?.code) return;
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
      setOriginSelected({ code: 'GWL', name: 'GWALIOR JN', state: 'Madhya Pradesh', zone: 'NCR' });
      setDestSelected({ code: 'PUNE', name: 'PUNE JN', state: 'Maharashtra', zone: 'CR' });
    } else if (lower.includes('delhi') && (lower.includes('mumbai') || lower.includes('bombay'))) {
      setOriginSelected({ code: 'NDLS', name: 'NEW DELHI', state: 'Delhi', zone: 'NR' });
      setDestSelected({ code: 'CSTM', name: 'MUMBAI CST', state: 'Maharashtra', zone: 'CR' });
    } else if (lower.includes('delhi') && lower.includes('kolkata')) {
      setOriginSelected({ code: 'NDLS', name: 'NEW DELHI', state: 'Delhi', zone: 'NR' });
      setDestSelected({ code: 'HWH', name: 'HOWRAH JN', state: 'West Bengal', zone: 'ER' });
    }

    let detectedPriority = priority;
    if (lower.includes('cheap') || lower.includes('sasta')) {
      detectedPriority = 'cheapest';
      setPriority('cheapest');
    } else if (lower.includes('fast') || lower.includes('jaldi')) {
      detectedPriority = 'fastest';
      setPriority('fastest');
    }

    onSearch({
      origin: originSelected.code,
      destination: destSelected.code,
      travelDate,
      priority: detectedPriority,
      accessibleOnly,
    });
  };

  return (
    <div className="w-full max-w-5xl mx-auto">
      {/* Bauhaus Framing Box */}
      <div className="border-2 border-[#0F172A] bg-white shadow-[6px_6px_0px_0px_#0F172A] p-6 sm:p-8 relative">
        {/* Top Architectural Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b-2 border-[#0F172A] pb-5 mb-6 gap-3">
          <div>
            <span className="font-mono text-xs uppercase tracking-widest text-[#1D4ED8] font-black">
              [ 01 ] // ROUTE INITIALIZATION
            </span>
            <h2 className="text-2xl font-black tracking-tight text-[#0F172A] uppercase">
              Plan Intercity Multi-Hop Journey
            </h2>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#64748B]">
            <span className="w-2.5 h-2.5 bg-[#D97706] inline-block border border-[#0F172A]"></span>
            <span className="font-bold">AGRD ELLIPSE FILTERING ACTIVE</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Origin & Destination Grid */}
          <div className="grid grid-cols-1 md:grid-cols-[1fr,auto,1fr] gap-4 items-center">
            {/* FROM FIELD */}
            <StationInput
              label="From Station or City"
              stepNumber="ORIGIN"
              selectedStation={originSelected}
              onSelectStation={(stn) => setOriginSelected(stn)}
              placeholder="e.g. GWL, Gwalior, New Delhi, Noida"
              accentColor="blue"
            />

            {/* SWAP BUTTON */}
            <div className="flex justify-center md:pt-6">
              <button
                type="button"
                onClick={handleSwap}
                className="w-11 h-11 border-2 border-[#0F172A] bg-[#F8FAFC] hover:bg-[#0F172A] hover:text-white flex items-center justify-center transition-colors shadow-[2px_2px_0px_0px_#0F172A] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer shrink-0"
                title="Swap Origin & Destination"
              >
                <ArrowLeftRight className="w-4 h-4" />
              </button>
            </div>

            {/* TO FIELD */}
            <StationInput
              label="To Station or City"
              stepNumber="DESTINATION"
              selectedStation={destSelected}
              onSelectStation={(stn) => setDestSelected(stn)}
              placeholder="e.g. PUNE, Pune, Mumbai, Howrah"
              accentColor="red"
            />
          </div>

          {/* Date & Preferences Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
            {/* Travel Date */}
            <div>
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-[#475569] mb-1.5">
                Travel Date
              </label>
              <div className="border-2 border-[#0F172A] bg-white flex items-center px-3.5 py-2.5 shadow-[2px_2px_0px_0px_#0F172A]">
                <Calendar className="w-4 h-4 text-[#64748B] mr-2.5 shrink-0" />
                <input
                  type="date"
                  value={travelDate}
                  onChange={(e) => setTravelDate(e.target.value)}
                  className="w-full bg-transparent font-mono font-bold text-sm text-[#0F172A] outline-none"
                />
              </div>
            </div>

            {/* Pareto Priority Selection */}
            <div>
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-[#475569] mb-1.5 flex items-center gap-1">
                <Sliders className="w-3.5 h-3.5 text-[#1D4ED8]" />
                <span>Optimization Goal</span>
              </label>
              <div className="border-2 border-[#0F172A] bg-white flex items-center px-3 py-2.5 shadow-[2px_2px_0px_0px_#0F172A]">
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full bg-transparent font-mono font-bold text-xs sm:text-sm text-[#0F172A] outline-none cursor-pointer"
                >
                  <option value="balanced">BALANCED (5-Criteria Pareto Front)</option>
                  <option value="fastest">FASTEST (Minimum Total Travel Time)</option>
                  <option value="cheapest">CHEAPEST (Maximum Fare Arbitrage)</option>
                  <option value="reliable">MOST RELIABLE (Gaussian P(Arrival))</option>
                </select>
              </div>
            </div>

            {/* Accessibility Checkbox */}
            <div className="flex items-center sm:col-span-2 lg:col-span-1 border-2 border-[#0F172A] p-3 bg-[#F8FAFC] shadow-[2px_2px_0px_0px_#0F172A]">
              <input
                type="checkbox"
                id="accessible_check"
                checked={accessibleOnly}
                onChange={(e) => setAccessibleOnly(e.target.checked)}
                className="w-4 h-4 border-2 border-[#0F172A] text-[#1D4ED8] rounded-none focus:ring-0 cursor-pointer"
              />
              <label htmlFor="accessible_check" className="ml-2.5 text-xs font-mono font-bold text-[#0F172A] cursor-pointer select-none">
                STEP-FREE WHEELCHAIR RAMPS ONLY (PwD)
              </label>
            </div>
          </div>

          {/* SUBMIT BUTTON */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[#1D4ED8] hover:bg-[#1E40AF] text-white border-2 border-[#0F172A] py-3.5 px-6 font-mono font-black text-sm uppercase tracking-widest flex items-center justify-center space-x-2 shadow-[4px_4px_0px_0px_#0F172A] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer disabled:opacity-50"
            >
              <span>{isLoading ? 'CALCULATING RAPTOR GRAPH & DELAY BUFFER...' : 'SEARCH OPTIMAL TRANSIT ROUTES'}</span>
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </button>
          </div>
        </form>

        {/* Natural Language Search Box (Bottom Section) */}
        <div className="mt-8 pt-5 border-t-2 border-[#E2DFD7]">
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
              className="w-full border-2 border-[#0F172A] px-3.5 py-2 text-xs font-mono text-[#0F172A] placeholder-[#94A3B8] outline-none focus:border-[#1D4ED8] bg-[#F8FAFC]"
            />
            <button
              type="submit"
              className="bg-[#0F172A] text-white px-5 py-2 text-xs font-mono font-bold uppercase hover:bg-[#1D4ED8] border-2 border-[#0F172A] transition-colors shrink-0 cursor-pointer shadow-[2px_2px_0px_0px_#0F172A]"
            >
              Parse & Search
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
