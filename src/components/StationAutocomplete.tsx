import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface StationSuggestion {
  code: string;
  name: string;
  state?: string;
}

interface Props {
  value: string;
  onChange: (code: string, name: string) => void;
  placeholder: string;
  disabled?: boolean;
}

export default function StationAutocomplete({ value, onChange, placeholder, disabled = false }: Props) {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<StationSuggestion[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [selectedName, setSelectedName] = useState('');
  const wrapperRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setQuery(value);
    setSelectedName(value);
  }, [value]);

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSuggestions([]);
      setActiveIndex(-1);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/stations/autocomplete?q=${encodeURIComponent(q)}`);
      if (res.ok) {
        const data = await res.json();
        const list = Array.isArray(data) ? data.slice(0, 8) : [];
        setSuggestions(list);
        setActiveIndex(-1);
        setIsOpen(list.length > 0);

        // Auto-match if user typed exact station code
        const exact = list.find((s: StationSuggestion) => s.code.toUpperCase() === q.trim().toUpperCase());
        if (exact) {
          onChange(exact.code, exact.name);
        }
      }
    } catch {
      setSuggestions([]);
      setActiveIndex(-1);
    }
  }, [onChange]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query !== selectedName) {
      debounceRef.current = setTimeout(() => fetchSuggestions(query), 200);
    }
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, selectedName, fetchSuggestions]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll active item into view when navigating with keys
  useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const itemEl = listRef.current.children[activeIndex] as HTMLElement;
      if (itemEl) {
        itemEl.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [activeIndex]);

  const handleSelect = (s: StationSuggestion) => {
    const display = `${s.name} (${s.code})`;
    setQuery(display);
    setSelectedName(display);
    onChange(s.code, s.name);
    setIsOpen(false);
    setSuggestions([]);
    setActiveIndex(-1);
  };

  const handleBlur = () => {
    // If user clicked or typed a station and moved focus, auto-resolve if unconfirmed
    setTimeout(() => {
      if (!selectedName && suggestions.length > 0 && query.trim()) {
        const qUpper = query.trim().toUpperCase();
        const match = suggestions.find((s) => s.code.toUpperCase() === qUpper || s.name.toUpperCase() === qUpper) || suggestions[0];
        handleSelect(match);
      }
    }, 200);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || suggestions.length === 0) {
      if (e.key === 'ArrowDown' && suggestions.length > 0) {
        setIsOpen(true);
        setActiveIndex(0);
        e.preventDefault();
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === 'Enter') {
      if (suggestions.length > 0) {
        e.preventDefault();
        const pickIdx = activeIndex >= 0 && activeIndex < suggestions.length ? activeIndex : 0;
        handleSelect(suggestions[pickIdx]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setActiveIndex(-1);
    }
  };

  return (
    <div ref={wrapperRef} className="relative w-full">
      <input
        type="text"
        disabled={disabled}
        value={query}
        onChange={(e) => { setQuery(e.target.value); setSelectedName(''); }}
        onFocus={() => !disabled && suggestions.length > 0 && setIsOpen(true)}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="w-full bg-[#FAF7F2] border border-[#4A5D30]/25 rounded-xl px-4 py-2 font-['Timeless'] text-[#111111] text-[16px] sm:text-[17px] outline-none focus:bg-white focus:ring-2 focus:ring-[#4A5D30]/30 focus:border-[#4A5D30] placeholder:text-stone-400 transition-all shadow-2xs disabled:opacity-60 disabled:cursor-not-allowed"
      />
      {isOpen && suggestions.length > 0 && (
        <div
          ref={listRef}
          className="absolute z-50 top-full mt-1.5 w-full bg-[#F6F0E6] rounded-2xl shadow-xl border border-[#4A5D30]/20 overflow-hidden max-h-60 overflow-y-auto font-['Timeless']"
        >
          {suggestions.map((s, idx) => {
            const isHighlighted = idx === activeIndex;
            return (
              <button
                key={s.code}
                type="button"
                onMouseEnter={() => setActiveIndex(idx)}
                onClick={() => handleSelect(s)}
                className={`w-full text-left px-4 py-2.5 transition-colors text-[15px] sm:text-[16px] border-b border-[#4A5D30]/10 last:border-b-0 cursor-pointer flex items-center justify-between ${
                  isHighlighted ? 'bg-[#E5D5BF] font-semibold' : 'hover:bg-[#E5D5BF]/60'
                }`}
              >
                <div className="truncate flex items-center gap-2">
                  <svg className="w-4 h-4 text-[#4A5D30] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" />
                    <circle cx="12" cy="9" r="2.5" />
                  </svg>
                  <span className="font-semibold text-[#111111]">{s.name}</span>
                  {s.state && <span className="text-stone-500 ml-1 text-[13px] sm:text-[14px] font-normal">· {s.state}</span>}
                </div>
                <span className="text-[#4A5D30] font-bold text-[14px] sm:text-[15px] shrink-0 ml-2">({s.code})</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
