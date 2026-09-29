import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import RouteMap from '../components/RouteMap';
import RouteCard, { type RouteItem } from '../components/RouteCard';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface SearchResponse {
  search_id: string;
  origin: string;
  destination: string;
  travel_date: string;
  total_routes_found: number;
  routes: Array<{
    label: string;
    total_travel_time: string;
    total_fare: number | null;
    transfers: number;
    reliability_score: number;
    joint_reliability_percent?: string;
    legs: Array<any>;
    bus_legs?: Array<any>;
    transfers_info?: Array<any>;
    fare_arbitrage_tip?: string;
    accessibility_badge?: string;
    weather_advisory?: string;
    is_multimodal?: boolean;
    time_saved_vs_train_minutes?: number | null;
    comfort_score?: number | null;
  }>;
  computed_in_ms: number;
  nlp_query?: string | null;
  nlp_interpretation?: Record<string, any> | null;
  ai_summary?: string | null;
}

const POPULAR_SUGGESTIONS = [
  { label: 'New Delhi → Mumbai', query: 'Delhi to Mumbai tomorrow' },
  { label: 'Pune → Gwalior', query: 'Pune se Gwalior next week' },
  { label: 'Bengaluru → Chennai', query: 'Bangalore to Chennai morning' },
  { label: 'Howrah → Patna', query: 'Howrah to Patna superfast' },
  { label: 'Ahmedabad → Jaipur', query: 'Ahmedabad to Jaipur sleeper' },
];

export default function ResultsPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeRouteIdx, setActiveRouteIdx] = useState<number>(0);
  const [clarifyInput, setClarifyInput] = useState('');

  const fetchRoutes = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const nlp = searchParams.get('nlp');
      if (nlp) {
        const res = await fetch(`${API_BASE}/api/v1/search/nlp`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: nlp }),
        });
        if (!res.ok) throw new Error('Search failed. Please try a different query.');
        const data = await res.json();
        setResults(data);
        setActiveRouteIdx(0);
      } else {
        const origin = searchParams.get('origin') || 'PUNE';
        const destination = searchParams.get('destination') || 'GWL';
        const date = searchParams.get('date') || new Date().toISOString().split('T')[0];

        const res = await fetch(`${API_BASE}/api/v1/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            origin,
            destination,
            travel_date: date,
            max_transfers: 2,
            priority: 'balanced',
            accessible_only: false,
            include_buses: true,
          }),
        });
        if (!res.ok) throw new Error('Search failed. Please check station codes.');
        const data = await res.json();
        setResults(data);
        setActiveRouteIdx(0);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not fetch routes');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchRoutes();
  }, [fetchRoutes]);

  const activeRoute = results?.routes && results.routes.length > 0 ? results.routes[activeRouteIdx] : null;

  const routeCards: RouteItem[] = (results?.routes || []).map((r, i) => ({
    id: `route-${i}`,
    label: r.label,
    trainName: r.legs[0]?.train_name || 'Train Connection',
    trainNumber: r.legs.map((l) => l.train_number).join(' → '),
    departure: r.legs[0]?.departure_time?.slice(0, 5) || '--:--',
    arrival: (r.bus_legs && r.bus_legs.length > 0
      ? r.bus_legs[r.bus_legs.length - 1].arrival_time?.slice(0, 5)
      : r.legs[r.legs.length - 1]?.arrival_time?.slice(0, 5)) || '--:--',
    duration: r.total_travel_time,
    fare: r.total_fare ? `₹${r.total_fare}` : '--',
    transfers: r.transfers,
    reliability: r.joint_reliability_percent || `${Math.round(r.reliability_score * 100)}%`,
    hasBusLeg: Boolean(r.is_multimodal || (r.bus_legs && r.bus_legs.length > 0)),
    isComfortable: r.label === 'COMFORT_HOMESTAY',
    isMultimodal: r.is_multimodal,
    legs: r.legs,
    bus_legs: r.bus_legs,
    transfers_info: r.transfers_info,
    fare_arbitrage_tip: r.fare_arbitrage_tip,
    accessibility_badge: r.accessibility_badge,
    weather_advisory: r.weather_advisory,
    time_saved_vs_train_minutes: r.time_saved_vs_train_minutes,
    comfort_score: r.comfort_score,
  }));

  const nlpQuery = searchParams.get('nlp') || results?.nlp_query;
  const entities = results?.nlp_interpretation;
  const needsClarification = Boolean(entities?.needs_clarification);

  const handleClarifySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!clarifyInput.trim()) return;
    navigate(`/results?nlp=${encodeURIComponent(clarifyInput.trim())}`);
  };

  return (
    <div className="h-screen w-screen flex flex-col md:flex-row overflow-hidden bg-brand-cream">
      {/* Floating Brand Navigation Badge (rounded-2xl, no capsule) */}
      <div className="absolute top-4 left-4 z-[500] flex items-center gap-2">
        <Link
          to="/"
          className="group bg-white/95 backdrop-blur-md px-4 py-2.5 rounded-2xl shadow-md text-[#1A2766] text-base font-bold hover:scale-[1.02] transition-all flex items-center gap-2.5 border border-stone-200/90"
        >
          <span className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#1A2766] to-[#3B5BDB] flex items-center justify-center text-white font-serif font-black text-sm shadow-xs">
            M
          </span>
          <span style={{ fontFamily: "'DM Serif Display', Georgia, serif" }} className="text-lg">
            MargDarshak
          </span>
        </Link>
      </div>

      {/* Map Area: Shortened width (~35-38% on desktop) */}
      <div className="w-full md:w-[38%] lg:w-[35%] h-[40vh] md:h-full relative z-0 flex-shrink-0 border-r border-stone-200/70">
        <RouteMap
          legs={activeRoute?.legs}
          busLegs={activeRoute?.bus_legs}
        />
      </div>

      {/* Route & NLP Response Area: Widened width (~62-65% on desktop) */}
      <div className="w-full md:w-[62%] lg:w-[65%] h-[60vh] md:h-full overflow-y-auto bg-brand-periwinkle p-5 sm:p-7 md:p-8 flex flex-col shadow-inner">
        {/* Header with Title and Query Metrics */}
        <div className="mb-4 pt-1">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-serif text-[#1A2766] font-bold tracking-tight">
              {loading
                ? 'Planning Routes...'
                : needsClarification
                ? 'Journey Clarification Needed'
                : results && results.total_routes_found > 0
                ? `${results.total_routes_found} Optimal Routes`
                : 'No Direct Routes Found'}
            </h2>
            {results && !loading && (
              <span className="text-xs font-[var(--font-ui)] bg-white/95 text-[#1A2766] px-3 py-1 rounded-lg font-semibold border border-white/80 shadow-2xs">
                ⚡ {results.computed_in_ms} ms
              </span>
            )}
          </div>
          {results && !loading && !needsClarification && (
            <p className="text-xs font-[var(--font-ui)] text-[#1A2766]/70 mt-1 uppercase tracking-wider font-semibold">
              Corridor: {results.origin} → {results.destination} · {results.travel_date}
            </p>
          )}
        </div>

        {/* Ambiguous Clarification Card (shown for queries like 'ghar') */}
        {!loading && needsClarification && (
          <div className="bg-white/95 backdrop-blur-md rounded-2xl p-6 mb-5 border border-stone-200/80 shadow-sm animate-fadeIn">
            <div className="flex items-start gap-3.5 mb-4">
              <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700 text-lg shrink-0">
                🧭
              </div>
              <div>
                <h3 className="font-serif text-lg font-bold text-[#1A2766]">
                  Could you please specify your origin and destination?
                </h3>
                <p className="text-sm font-[var(--font-ui)] text-stone-600 mt-1 leading-relaxed">
                  {entities?.clarification_message ||
                    entities?.clarification_prompt ||
                    results?.ai_summary ||
                    `We couldn't clearly pinpoint where you are starting from and where you want to go. Please name both stations or cities.`}
                </p>
              </div>
            </div>

            {/* Quick Clarify Input */}
            <form onSubmit={handleClarifySubmit} className="flex gap-2 mb-4">
              <input
                type="text"
                value={clarifyInput}
                onChange={(e) => setClarifyInput(e.target.value)}
                placeholder="e.g. Pune to Gwalior next Friday, or Delhi to Mumbai before 8 PM"
                className="flex-1 bg-[#FAF8F5] border border-stone-300 rounded-xl px-4 py-3 font-[var(--font-ui)] text-stone-900 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-brand-blue/30 focus:border-brand-blue placeholder:text-stone-400"
              />
              <button
                type="submit"
                className="bg-[#1A2766] hover:bg-blue-900 text-white font-[var(--font-ui)] font-semibold text-xs uppercase tracking-wider px-5 py-3 rounded-xl transition-all shadow-xs cursor-pointer"
              >
                Search
              </button>
            </form>

            {/* Popular Route Suggestions */}
            <div>
              <p className="text-xs font-[var(--font-ui)] font-semibold text-stone-500 uppercase tracking-wider mb-2">
                Popular corridors to try:
              </p>
              <div className="flex flex-wrap gap-2">
                {POPULAR_SUGGESTIONS.map((s, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => navigate(`/results?nlp=${encodeURIComponent(s.query)}`)}
                    className="bg-stone-50 hover:bg-brand-periwinkle/30 border border-stone-200/90 text-stone-700 px-3 py-1.5 rounded-lg text-xs font-[var(--font-ui)] font-medium transition-all cursor-pointer"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* AI & NLP Understanding Area (When NOT needing clarification) */}
        {results && !loading && !needsClarification && (
          <div className="bg-white/85 backdrop-blur-md rounded-2xl p-4.5 mb-5 border border-white/80 shadow-xs">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2.5 h-2.5 rounded-xs bg-brand-blue animate-pulse" />
              <h3 className="font-serif text-sm font-bold text-[#1A2766] tracking-wide uppercase">
                AI Route Insights & NLP Parsing
              </h3>
            </div>

            {nlpQuery && (
              <div className="bg-brand-cream/60 px-3 py-2 rounded-xl border border-stone-200/60 mb-2.5 text-xs font-[var(--font-ui)] text-stone-700 italic">
                &ldquo;{nlpQuery}&rdquo;
              </div>
            )}

            <p className="text-xs font-[var(--font-ui)] text-stone-700 leading-relaxed">
              {results.ai_summary ||
                `Identified ${results.total_routes_found} multi-criteria Pareto trade-offs across train schedules and connecting bus lines.`}
            </p>

            {/* Extracted Entity Tags: rounded-md, no capsules */}
            <div className="flex flex-wrap gap-1.5 mt-3 pt-2.5 border-t border-stone-200/60 text-[11px] font-[var(--font-ui)]">
              <span className="bg-brand-blue/10 text-brand-blue px-2.5 py-1 rounded-md font-semibold border border-brand-blue/20">
                {results.origin} → {results.destination}
              </span>
              <span className="bg-[#5A6B3C]/15 text-[#4A5D30] px-2.5 py-1 rounded-md font-semibold border border-[#5A6B3C]/25">
                📅 {results.travel_date}
              </span>
              {entities?.arrive_before_time && (
                <span className="bg-amber-100 text-amber-900 px-2.5 py-1 rounded-md font-semibold border border-amber-200">
                  ⏰ Arrive before {entities.arrive_before_time}
                </span>
              )}
              {entities?.prefer_home_wait && (
                <span className="bg-emerald-100 text-emerald-900 px-2.5 py-1 rounded-md font-semibold border border-emerald-200">
                  🏠 Wait-at-Home Comfort Active
                </span>
              )}
              <span className="bg-stone-100 text-stone-700 px-2.5 py-1 rounded-md font-medium border border-stone-200/60">
                🚌 Bus Bridging Active
              </span>
            </div>
          </div>
        )}

        {/* Loading Spinner */}
        {loading && (
          <div className="flex-1 flex flex-col items-center justify-center py-20">
            <div className="w-10 h-10 border-3 border-brand-blue/30 border-t-brand-blue rounded-xl animate-spin" />
            <p className="mt-4 text-[#1A2766] font-[var(--font-ui)] text-sm font-semibold">
              Scanning 22,000 trains, P85 delay buffers & bus corridors...
            </p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 text-red-700 border border-red-200 rounded-2xl p-6 text-center font-[var(--font-ui)] my-auto">
            <p className="font-semibold mb-1">Search could not be completed</p>
            <p className="text-xs opacity-80 mb-4">{error}</p>
            <button
              onClick={() => fetchRoutes()}
              className="px-5 py-2.5 bg-[#1A2766] text-white rounded-xl text-xs font-semibold hover:bg-blue-900 transition-colors shadow-xs cursor-pointer"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Route Cards List */}
        {!loading && !error && !needsClarification && (
          <div className="flex flex-col gap-4 pb-8">
            {routeCards.map((route, i) => (
              <RouteCard
                key={route.id}
                route={route}
                index={i}
                isActive={activeRouteIdx === i}
                onSelect={() => setActiveRouteIdx(i)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
