import { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import RouteMap from '../components/RouteMap';
import RouteCard, { type RouteItem } from '../components/RouteCard';
import ParetoFilterBar, { type ParetoFilterKey, type ParetoFilterCounts } from '../components/ParetoFilterBar';

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
  const [selectedRouteId, setSelectedRouteId] = useState<string>('route-0');
  const [selectedFilter, setSelectedFilter] = useState<ParetoFilterKey>(() => {
    const p = searchParams.get('priority') || searchParams.get('filter') || 'ALL';
    const upper = p.toUpperCase();
    if (upper === 'FASTEST') return 'FASTEST';
    if (upper === 'CHEAPEST') return 'CHEAPEST';
    if (upper === 'BALANCED') return 'BALANCED';
    if (upper === 'RELIABLE' || upper === 'MOST_RELIABLE') return 'MOST_RELIABLE';
    if (upper === 'COMFORT' || upper === 'COMFORT_HOMESTAY') return 'COMFORT_HOMESTAY';
    if (upper === 'MULTIMODAL' || upper === 'MULTIMODAL_FASTEST') return 'MULTIMODAL';
    if (upper === 'PARETO' || upper === 'PARETO_FRONTIER') return 'PARETO_FRONTIER';
    return 'ALL';
  });
  const [sortBy, setSortBy] = useState<string>('pareto');
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
        setSelectedRouteId('route-0');
        if (data.nlp_interpretation?.priority) {
          const p = data.nlp_interpretation.priority.toUpperCase();
          if (p === 'MULTIMODAL' || data.nlp_interpretation?.bus_only || nlp.toLowerCase().includes('bus')) {
            setSelectedFilter('MULTIMODAL');
          } else if (p === 'FASTEST') {
            setSelectedFilter('FASTEST');
          } else if (p === 'CHEAPEST') {
            setSelectedFilter('CHEAPEST');
          } else if (p === 'COMFORT') {
            setSelectedFilter('COMFORT_HOMESTAY');
          } else if (p === 'RELIABLE') {
            setSelectedFilter('MOST_RELIABLE');
          }
        }
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
        setSelectedRouteId('route-0');
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

  const activeRoute = useMemo(() => {
    if (!results?.routes || results.routes.length === 0) return null;
    const matchIndex = results.routes.findIndex((_, idx) => `route-${idx}` === selectedRouteId);
    return matchIndex >= 0 ? results.routes[matchIndex] : results.routes[0];
  }, [results, selectedRouteId]);

  const routeCards: RouteItem[] = (results?.routes || []).map((r, i) => {
    const hasTrains = Boolean(r.legs && r.legs.length > 0);
    const hasBuses = Boolean(r.bus_legs && r.bus_legs.length > 0);
    const firstLeg = hasTrains ? r.legs[0] : null;
    const lastLeg = hasTrains ? r.legs[r.legs.length - 1] : null;
    const firstBus = hasBuses ? r.bus_legs[0] : null;
    const lastBus = hasBuses ? r.bus_legs[r.bus_legs.length - 1] : null;

    let computedName = 'Train Connection';
    if (hasTrains && hasBuses) {
      computedName = `${firstLeg?.train_name || 'Express Train'} + Express Bus`;
    } else if (hasTrains) {
      computedName = firstLeg?.train_name || 'Train Connection';
    } else if (hasBuses) {
      computedName = `${firstBus?.operator_name || 'State Highway'} (${firstBus?.bus_type || 'Bus'})`;
    }

    let computedNumber = '';
    if (hasTrains && hasBuses) {
      computedNumber = `${r.legs.map((l) => l.train_number).join(' → ')} + BUS (${firstBus?.operator_code || 'EXPR'})`;
    } else if (hasTrains) {
      computedNumber = r.legs.map((l) => l.train_number).join(' → ');
    } else if (hasBuses) {
      computedNumber = `BUS // ${firstBus?.operator_code || 'HIGHWAY'}`;
    }

    const computedDeparture = (firstLeg?.departure_time || firstBus?.departure_time || '--:--').slice(0, 5);
    const computedArrival = (lastBus && (!lastLeg || r.is_multimodal)
      ? lastBus.arrival_time
      : (lastLeg?.arrival_time || lastBus?.arrival_time || '--:--')
    ).slice(0, 5);

    return {
      id: `route-${i}`,
      label: r.label,
      trainName: computedName,
      trainNumber: computedNumber,
      departure: computedDeparture,
      arrival: computedArrival,
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
    };
  });

  const paretoCounts: ParetoFilterCounts = useMemo(() => ({
    ALL: routeCards.length,
    PARETO_FRONTIER: routeCards.filter((r) => r.label && r.label !== 'ALTERNATIVE').length,
    FASTEST: routeCards.filter((r) => r.label === 'FASTEST').length,
    CHEAPEST: routeCards.filter((r) => r.label === 'CHEAPEST').length,
    BALANCED: routeCards.filter((r) => r.label === 'BALANCED').length,
    MOST_RELIABLE: routeCards.filter((r) => r.label === 'MOST_RELIABLE').length,
    COMFORT_HOMESTAY: routeCards.filter((r) => r.label === 'COMFORT_HOMESTAY').length,
    MULTIMODAL: routeCards.filter((r) => r.isMultimodal || r.hasBusLeg || r.label === 'MULTIMODAL_FASTEST').length,
  }), [routeCards]);

  const displayedRouteCards = useMemo(() => {
    const filtered = routeCards.filter((r) => {
      if (selectedFilter === 'ALL') return true;
      if (selectedFilter === 'PARETO_FRONTIER') return r.label && r.label !== 'ALTERNATIVE';
      if (selectedFilter === 'FASTEST') return r.label === 'FASTEST';
      if (selectedFilter === 'CHEAPEST') return r.label === 'CHEAPEST';
      if (selectedFilter === 'BALANCED') return r.label === 'BALANCED';
      if (selectedFilter === 'MOST_RELIABLE') return r.label === 'MOST_RELIABLE';
      if (selectedFilter === 'COMFORT_HOMESTAY') return r.label === 'COMFORT_HOMESTAY';
      if (selectedFilter === 'MULTIMODAL') return r.isMultimodal || r.hasBusLeg || r.label === 'MULTIMODAL_FASTEST';
      return true;
    });

    return [...filtered].sort((a, b) => {
      if (sortBy === 'duration') {
        const getMin = (s: string) => {
          const parts = s.split('h');
          return (parseInt(parts[0]) || 0) * 60 + (parseInt(parts[1]?.replace('m', '')) || 0);
        };
        return getMin(a.duration) - getMin(b.duration);
      }
      if (sortBy === 'fare') {
        const parseFare = (f: string) => parseInt(f.replace('₹', '')) || 9999;
        return parseFare(a.fare) - parseFare(b.fare);
      }
      if (sortBy === 'reliability') {
        const parseRel = (rel?: string) => parseInt(rel?.replace('%', '') || '0');
        return parseRel(b.reliability) - parseRel(a.reliability);
      }
      if (sortBy === 'comfort') {
        return (a.comfort_score || 9999) - (b.comfort_score || 9999);
      }
      return 0; // Default: Pareto rank
    });
  }, [routeCards, selectedFilter, sortBy]);

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

        {/* Pareto Multi-Criteria Filter Bar */}
        {!loading && !error && !needsClarification && results && results.total_routes_found > 0 && (
          <ParetoFilterBar
            selectedFilter={selectedFilter}
            onSelectFilter={(key) => {
              setSelectedFilter(key);
              const matching = routeCards.find((r) => {
                if (key === 'ALL') return true;
                if (key === 'PARETO_FRONTIER') return r.label && r.label !== 'ALTERNATIVE';
                if (key === 'FASTEST') return r.label === 'FASTEST';
                if (key === 'CHEAPEST') return r.label === 'CHEAPEST';
                if (key === 'BALANCED') return r.label === 'BALANCED';
                if (key === 'MOST_RELIABLE') return r.label === 'MOST_RELIABLE';
                if (key === 'COMFORT_HOMESTAY') return r.label === 'COMFORT_HOMESTAY';
                if (key === 'MULTIMODAL') return r.isMultimodal || r.hasBusLeg || r.label === 'MULTIMODAL_FASTEST';
                return true;
              });
              if (matching) setSelectedRouteId(matching.id);
            }}
            sortBy={sortBy}
            onSelectSort={setSortBy}
            counts={paretoCounts}
          />
        )}

        {/* Route Cards List */}
        {!loading && !error && !needsClarification && (
          <div className="flex flex-col gap-4 pb-8">
            {displayedRouteCards.length > 0 ? (
              displayedRouteCards.map((route, i) => (
                <RouteCard
                  key={route.id}
                  route={route}
                  index={i}
                  isActive={selectedRouteId === route.id}
                  onSelect={() => setSelectedRouteId(route.id)}
                />
              ))
            ) : (
              <div className="bg-white/95 backdrop-blur-md rounded-2xl p-6 text-center border border-stone-200/80 shadow-xs">
                <p className="font-serif text-base font-bold text-[#1A2766] mb-1">
                  No routes found matching filter &ldquo;{selectedFilter.replace(/_/g, ' ')}&rdquo;
                </p>
                <p className="text-xs text-stone-600 mb-4 font-[var(--font-ui)]">
                  Try switching back to All Routes or another Pareto trade-off criterion.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFilter('ALL');
                    if (routeCards.length > 0) setSelectedRouteId(routeCards[0].id);
                  }}
                  className="bg-[#1A2766] hover:bg-blue-900 text-white font-[var(--font-ui)] px-4 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
                >
                  View All {routeCards.length} Available Routes
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
