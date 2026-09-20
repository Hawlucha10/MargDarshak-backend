import React, { useState, useEffect, useRef, useId } from 'react';
import { MapPin, X, Train, Check, Sparkles } from 'lucide-react';
import { searchStations, getPopularStations } from '../api/client';
import type { StationItem } from '../api/types';

interface StationInputProps {
  label: string;
  stepNumber: string;
  selectedStation: StationItem | null;
  onSelectStation: (station: StationItem) => void;
  placeholder?: string;
  accentColor?: 'blue' | 'red';
  autoFocusNext?: () => void;
}

export const StationInput: React.FC<StationInputProps> = ({
  label,
  stepNumber,
  selectedStation,
  onSelectStation,
  placeholder = 'Station name or code (e.g. NDLS, Gwalior)',
  accentColor = 'blue',
  autoFocusNext,
}) => {
  const [inputValue, setInputValue] = useState(
    selectedStation ? `${selectedStation.name} - ${selectedStation.code}` : ''
  );
  const [suggestions, setSuggestions] = useState<StationItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const [isPopularMode, setIsPopularMode] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const listId = useId();

  // Sync internal input value if external selectedStation changes (e.g. on Swap button click)
  useEffect(() => {
    if (selectedStation) {
      setInputValue(`${selectedStation.name} - ${selectedStation.code}`);
    } else {
      setInputValue('');
    }
  }, [selectedStation]);

  // Click outside listener to dismiss dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setActiveIndex(-1);
        // If user typed something but didn't pick, restore selected station name
        if (selectedStation) {
          setInputValue(`${selectedStation.name} - ${selectedStation.code}`);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [selectedStation]);

  // Handle station query search with fast 60ms debounce
  useEffect(() => {
    if (!isOpen) return;

    // Extract raw text before any trailing hyphen
    const queryPart = inputValue.includes(' - ')
      ? inputValue.split(' - ')[0].trim()
      : inputValue.trim();

    if (!queryPart) {
      // Empty input -> show popular hub stations
      setIsPopularMode(true);
      setIsLoading(true);
      getPopularStations().then((items) => {
        setSuggestions(items);
        setIsLoading(false);
        setActiveIndex(-1);
      });
      return;
    }

    setIsPopularMode(false);
    setIsLoading(true);
    const timer = setTimeout(async () => {
      try {
        const results = await searchStations(queryPart);
        setSuggestions(results);
      } catch (err) {
        console.error('Station search failure:', err);
      } finally {
        setIsLoading(false);
        setActiveIndex(-1);
      }
    }, 60);

    return () => clearTimeout(timer);
  }, [inputValue, isOpen]);

  // Scroll active item into view when navigating with arrow keys
  useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const activeEl = listRef.current.children[activeIndex] as HTMLElement;
      if (activeEl) {
        activeEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [activeIndex]);

  const handleSelect = (station: StationItem) => {
    onSelectStation(station);
    setInputValue(`${station.name} - ${station.code}`);
    setIsOpen(false);
    setActiveIndex(-1);
    if (autoFocusNext) {
      autoFocusNext();
    }
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setInputValue('');
    setActiveIndex(-1);
    inputRef.current?.focus();
    setIsOpen(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
        return;
      }
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev + 1 < suggestions.length ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => (prev - 1 >= 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && suggestions[activeIndex]) {
        handleSelect(suggestions[activeIndex]);
      } else if (suggestions.length > 0) {
        handleSelect(suggestions[0]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setActiveIndex(-1);
    }
  };

  const isBlue = accentColor === 'blue';
  const pinColor = isBlue ? 'text-[#1D4ED8]' : 'text-[#DC2626]';
  const borderFocusColor = isBlue ? 'focus-within:border-[#1D4ED8]' : 'focus-within:border-[#DC2626]';

  return (
    <div ref={containerRef} className="relative w-full">
      {/* Label and Step Tag */}
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-xs font-mono font-bold uppercase tracking-wider text-[#475569] flex items-center gap-1.5">
          <span className="text-[10px] bg-[#0F172A] text-white px-1.5 py-0.2 font-mono">
            {stepNumber}
          </span>
          <span>{label}</span>
        </label>
        {selectedStation && (
          <span className="font-mono text-[11px] font-bold text-[#64748B] uppercase">
            IRCTC: <span className="text-[#0F172A] font-black">{selectedStation.code}</span>
          </span>
        )}
      </div>

      {/* Input Box */}
      <div
        className={`border-2 border-[#0F172A] bg-white flex items-center px-3.5 py-2.5 transition-all shadow-[2px_2px_0px_0px_#0F172A] ${borderFocusColor}`}
      >
        <MapPin className={`w-4 h-4 ${pinColor} mr-2.5 shrink-0`} />

        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => {
            setIsOpen(true);
            // Select text on focus so user can immediately type over
            inputRef.current?.select();
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          aria-autocomplete="list"
          aria-controls={listId}
          aria-expanded={isOpen}
          className="w-full bg-transparent font-mono font-bold text-sm text-[#0F172A] uppercase placeholder:normal-case placeholder:font-sans placeholder:font-normal placeholder:text-[#94A3B8] outline-none"
        />

        {/* Clear Button */}
        {inputValue && (
          <button
            type="button"
            onClick={handleClear}
            className="p-1 hover:bg-[#F1EFE9] text-[#64748B] hover:text-[#0F172A] transition-colors shrink-0 mr-1.5 cursor-pointer"
            title="Clear station"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}

        {/* Station Code Badge */}
        {selectedStation?.code && (
          <div className="bg-[#0F172A] text-white font-mono text-xs font-black px-2.5 py-1 tracking-wider shrink-0 select-none">
            {selectedStation.code}
          </div>
        )}
      </div>

      {/* IRCTC-Style Autocomplete Dropdown */}
      {isOpen && (
        <div
          id={listId}
          className="absolute top-full left-0 right-0 mt-1.5 bg-white border-2 border-[#0F172A] shadow-[6px_6px_0px_0px_#0F172A] z-50 max-h-72 overflow-y-auto"
        >
          {/* Header Bar */}
          <div className="p-2 bg-[#F1EFE9] border-b border-[#E2DFD7] flex items-center justify-between text-[11px] font-mono font-bold text-[#475569] uppercase tracking-wide sticky top-0 z-10">
            <div className="flex items-center gap-1.5">
              {isPopularMode ? (
                <>
                  <Sparkles className="w-3.5 h-3.5 text-[#D97706]" />
                  <span>Popular Railway Hubs (1-Click Select)</span>
                </>
              ) : (
                <>
                  <Train className="w-3.5 h-3.5 text-[#1D4ED8]" />
                  <span>Real-Time Station Matches ({suggestions.length})</span>
                </>
              )}
            </div>
            <span className="text-[10px] text-[#94A3B8]">▲▼ navigate • ↵ select</span>
          </div>

          {/* Loading Indicator */}
          {isLoading && (
            <div className="p-4 text-center text-xs font-mono text-[#64748B] bg-[#FAFAF9]">
              <span className="inline-block animate-pulse font-bold">
                Searching 8,989 Indian Railway stations...
              </span>
            </div>
          )}

          {/* Empty Suggestions State */}
          {!isLoading && suggestions.length === 0 && (
            <div className="p-5 text-center bg-[#FAFAF9]">
              <div className="text-xs font-mono font-bold text-[#DC2626] uppercase mb-1">
                No matching railway station found
              </div>
              <div className="text-[11px] text-[#64748B] font-sans">
                Try typing city name (e.g. "Delhi", "Mumbai", "Noida") or station code (e.g. "GWL", "PUNE").
              </div>
            </div>
          )}

          {/* List of Stations */}
          {!isLoading && (
            <div ref={listRef} className="divide-y divide-[#F1EFE9]">
              {suggestions.map((item, idx) => {
                const isActive = idx === activeIndex;
                const isSelected = selectedStation?.code === item.code;

                return (
                  <div
                    key={`${item.code}-${idx}`}
                    onMouseEnter={() => setActiveIndex(idx)}
                    onClick={() => handleSelect(item)}
                    className={`p-3 cursor-pointer transition-colors flex items-center justify-between group ${
                      isActive
                        ? 'bg-[#1D4ED8] text-white'
                        : isSelected
                        ? 'bg-[#EFF6FF] text-[#0F172A]'
                        : 'hover:bg-[#F8FAFC] text-[#0F172A]'
                    }`}
                  >
                    <div className="min-w-0 pr-3">
                      {/* Line 1: Station Name + Match Info */}
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-mono font-bold text-sm tracking-tight uppercase truncate ${
                            isActive ? 'text-white' : 'text-[#0F172A]'
                          }`}
                        >
                          {item.name}
                        </span>

                        {isSelected && (
                          <Check
                            className={`w-3.5 h-3.5 shrink-0 ${
                              isActive ? 'text-white' : 'text-[#1D4ED8]'
                            }`}
                          />
                        )}
                      </div>

                      {/* Line 2: Zone & State / Satellite Distance */}
                      <div
                        className={`text-xs font-mono mt-0.5 flex flex-wrap items-center gap-2 ${
                          isActive ? 'text-[#BFDBFE]' : 'text-[#64748B]'
                        }`}
                      >
                        {item.zone && <span>Zone: {item.zone}</span>}
                        {item.zone && item.state && <span>•</span>}
                        {item.state && <span>{item.state}</span>}

                        {item.distance_km !== undefined && item.distance_km > 0 && (
                          <span
                            className={`px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                              isActive
                                ? 'bg-white/20 text-white'
                                : 'bg-[#FEF3C7] text-[#92400E] border border-[#F59E0B]'
                            }`}
                          >
                            Nearby Hub: {item.distance_km} km away
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Right: Station Code Badge */}
                    <div className="shrink-0 flex items-center">
                      <span
                        className={`font-mono text-xs font-black px-2.5 py-1 uppercase tracking-widest border ${
                          isActive
                            ? 'bg-white text-[#1D4ED8] border-white'
                            : 'bg-[#0F172A] text-white border-[#0F172A]'
                        }`}
                      >
                        {item.code}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Footer Bar */}
          <div className="p-2 bg-[#F8FAFC] border-t border-[#E2DFD7] text-[10px] font-mono text-[#64748B] flex items-center justify-between">
            <span>MARGDARSHAK SPATIAL DIRECTORY</span>
            <span>8,989 STATIONS INDEXED</span>
          </div>
        </div>
      )}
    </div>
  );
};
