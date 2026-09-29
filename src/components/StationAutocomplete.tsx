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
}

export default function StationAutocomplete({ value, onChange, placeholder }: Props) {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<StationSuggestion[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedName, setSelectedName] = useState('');
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSuggestions([]);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/stations/autocomplete?q=${encodeURIComponent(q)}`);
      if (res.ok) {
        const data = await res.json();
        setSuggestions(Array.isArray(data) ? data.slice(0, 8) : []);
        setIsOpen(true);
      }
    } catch {
      setSuggestions([]);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query !== selectedName) {
      debounceRef.current = setTimeout(() => fetchSuggestions(query), 250);
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

  const handleSelect = (s: StationSuggestion) => {
    const display = `${s.name} (${s.code})`;
    setQuery(display);
    setSelectedName(display);
    onChange(s.code, s.name);
    setIsOpen(false);
    setSuggestions([]);
  };

  return (
    <div ref={wrapperRef} className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => { setQuery(e.target.value); setSelectedName(''); }}
        onFocus={() => suggestions.length > 0 && setIsOpen(true)}
        placeholder={placeholder}
        className="w-full bg-[#FAF8F5] border border-stone-200 rounded-xl px-4 py-3 font-[var(--font-ui)] text-stone-900 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-brand-blue/30 focus:border-brand-blue placeholder:text-stone-400 transition-all shadow-2xs"
      />
      {isOpen && suggestions.length > 0 && (
        <div className="absolute z-50 top-full mt-1.5 w-full bg-white rounded-2xl shadow-xl border border-stone-200 overflow-hidden max-h-64 overflow-y-auto">
          {suggestions.map((s) => (
            <button
              key={s.code}
              type="button"
              onClick={() => handleSelect(s)}
              className="w-full text-left px-4 py-3 hover:bg-brand-periwinkle/30 transition-colors font-[var(--font-ui)] text-sm border-b border-stone-100 last:border-b-0 cursor-pointer"
            >
              <span className="font-semibold text-stone-900">{s.name}</span>
              <span className="text-brand-blue font-bold ml-2">({s.code})</span>
              {s.state && <span className="text-stone-400 ml-1 text-xs font-normal">· {s.state}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
