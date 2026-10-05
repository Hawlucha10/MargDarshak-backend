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
    departure_time?: string;
    arrival_time?: string;
    departure_date?: string;
    arrival_date?: string;
    total_travel_minutes?: number;
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

const LOADING_MESSAGES = [
  'Optimizing your route...',
  'Searching optimal rail & bus routes...',
  'Evaluating fastest transfer combinations...',
  'Calculating best connection schedules...',
];

function timeStrToMinutes(t?: string): number {
  if (!t) return 0;
  const parts = t.split(':');
  return (parseInt(parts[0]) || 0) * 60 + (parseInt(parts[1]) || 0);
}

function formatDateBadge(dateStr?: string, daysToAdd: number = 0): string {
  if (!dateStr) return '';
  try {
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0]);
      const monthIdx = parseInt(parts[1]) - 1;
      const day = parseInt(parts[2]);
      const d = new Date(year, monthIdx, day);
      if (daysToAdd > 0) {
        d.setDate(d.getDate() + daysToAdd);
      }
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const mName = months[d.getMonth()];
      const dNum = d.getDate();
      return daysToAdd > 0 ? `${dNum} ${mName} (+${daysToAdd}d)` : `${dNum} ${mName}`;
    }
    return dateStr;
  } catch {
    return dateStr;
  }
}

export default function ResultsPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);
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
  const [sortBy, setSortBy] = useState<string>('best_match');
  const [clarifyInput, setClarifyInput] = useState('');

  useEffect(() => {
    if (!loading) return;
    const interval = setInterval(() => {
      setLoadingMsgIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 1800);
    return () => clearInterval(interval);
  }, [loading]);

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
    const firstBus = (r.bus_legs && r.bus_legs.length > 0) ? r.bus_legs[0] : null;
    const lastBus = (r.bus_legs && r.bus_legs.length > 0) ? r.bus_legs[r.bus_legs.length - 1] : null;

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

    const computedDeparture = (r.departure_time || firstLeg?.departure_time || firstBus?.departure_time || '--:--').slice(0, 5);

    // Accurate arrival time resolution:
    let computedArrival: string = r.arrival_time?.slice(0, 5) || '';
    if (!computedArrival) {
      if (hasTrains && hasBuses) {
        if (results?.destination && lastLeg?.to_station === results.destination) {
          computedArrival = (lastLeg?.arrival_time || '--:--').slice(0, 5);
        } else if (results?.destination && lastBus?.to_station_code === results.destination) {
          computedArrival = (lastBus?.arrival_time || '--:--').slice(0, 5);
        } else {
          const lastTransfer = r.transfers_info && r.transfers_info[r.transfers_info.length - 1];
          if (lastTransfer && lastTransfer.interchange_guide?.includes('Board Train')) {
            computedArrival = (lastLeg?.arrival_time || lastBus?.arrival_time || '--:--').slice(0, 5);
          } else {
            computedArrival = (lastBus?.arrival_time || lastLeg?.arrival_time || '--:--').slice(0, 5);
          }
        }
      } else if (hasTrains) {
        computedArrival = (lastLeg?.arrival_time || '--:--').slice(0, 5);
      } else if (hasBuses) {
        computedArrival = (lastBus?.arrival_time || '--:--').slice(0, 5);
      } else {
        computedArrival = '--:--';
      }
    }
    if (!computedArrival) {
      computedArrival = '--:--';
    }

    // Accurate total duration calculation:
    // Sum of all train leg durations + bus leg durations + transfer layovers
    let totalMins = 0;
    if (r.legs) {
      for (const leg of r.legs) {
        const dM = timeStrToMinutes(leg.departure_time);
        const aM = timeStrToMinutes(leg.arrival_time);
        const diff = aM >= dM ? aM - dM : aM - dM + 1440;
        totalMins += Math.max(10, diff);
      }
    }
    if (r.bus_legs) {
      for (const b of r.bus_legs) {
        totalMins += b.duration_minutes || 180;
      }
    }
    if (r.transfers_info) {
      for (const t of r.transfers_info) {
        totalMins += t.wait_time_minutes || 0;
      }
    }

    const computedDuration = totalMins > 0
      ? `${Math.floor(totalMins / 60)}h ${String(totalMins % 60).padStart(2, '0')}m`
      : r.total_travel_time;

    const departureDate = r.departure_date || formatDateBadge(results?.travel_date, 0);

    let arrivalDate = r.arrival_date;
    if (!arrivalDate && results?.travel_date && computedDeparture !== '--:--' && totalMins > 0) {
      const depMins = timeStrToMinutes(computedDeparture);
      const totalArrivalMins = depMins + totalMins;
      const daysDiff = Math.floor(totalArrivalMins / 1440);
      arrivalDate = formatDateBadge(results.travel_date, daysDiff);
    } else if (!arrivalDate) {
      arrivalDate = departureDate;
    }

    return {
      id: `route-${i}`,
      label: r.label,
      trainName: computedName,
      trainNumber: computedNumber,
      departure: computedDeparture,
      arrival: computedArrival,
      departureDate,
      arrivalDate,
      duration: computedDuration,
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
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[#E5D5BF] font-['Timeless']">
      {/* Main Content Area: 40% Map / 60% Details Split */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden min-h-0">
        {/* Map Area: 40% Width on desktop */}
        <div className="w-full md:w-[40%] h-[40vh] md:h-full relative z-0 flex-shrink-0 border-r border-[#4A5D30]/20">
          <RouteMap
            legs={activeRoute?.legs}
            busLegs={activeRoute?.bus_legs}
          />
        </div>

        {/* Route & NLP Response Area: 60% Width on desktop */}
        <div className="w-full md:w-[60%] h-[60vh] md:h-full overflow-y-auto bg-[#E5D5BF] p-5 sm:p-7 md:p-8 flex flex-col shadow-inner font-['Timeless']">
          {/* Header with Title and Query Metrics */}
          <div className="mb-4 pt-1 font-['Timeless']">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-['Timeless'] text-[#4A5D30] font-bold tracking-tight">
                {loading
                  ? 'Planning Routes...'
                  : needsClarification
                  ? 'Journey Clarification Needed'
                  : results && results.total_routes_found > 0
                  ? `${results.total_routes_found} Optimal Routes`
                  : 'No Direct Routes Found'}
              </h2>
            </div>
            {results && !loading && !needsClarification && (
              <p className="text-xs font-['Timeless'] text-stone-700 mt-1 uppercase tracking-wider font-semibold">
                Corridor: {results.origin} → {results.destination} · {results.travel_date}
              </p>
            )}
          </div>

          {/* Ambiguous Clarification Card (shown for queries like 'ghar') */}
          {!loading && needsClarification && (
            <div className="bg-[#F6F0E6] rounded-2xl p-6 mb-5 border border-[#4A5D30]/20 shadow-sm animate-fadeIn font-['Timeless']">
              <div className="flex items-start gap-3.5 mb-4">
                <div className="w-10 h-10 rounded-xl bg-[#E5D5BF] border border-[#4A5D30]/25 flex items-center justify-center text-[#4A5D30] text-lg shrink-0">
                  🧭
                </div>
                <div>
                  <h3 className="font-['Timeless'] text-lg font-bold text-[#4A5D30]">
                    Could you please specify your origin and destination?
                  </h3>
                  <p className="text-sm font-['Timeless'] text-stone-600 mt-1 leading-relaxed">
                    {entities?.clarification_message ||
                      entities?.clarification_prompt ||
                      results?.ai_summary ||
                      `We couldn't clearly pinpoint where you are starting from and where you want to go. Please name both stations or cities.`}
                  </p>
                </div>
              </div>

              {/* Quick Clarify Input */}
              <form onSubmit={handleClarifySubmit} className="flex gap-2 mb-4 font-['Timeless']">
                <input
                  type="text"
                  value={clarifyInput}
                  onChange={(e) => setClarifyInput(e.target.value)}
                  placeholder="e.g. Pune to Gwalior next Friday, or Delhi to Mumbai before 8 PM"
                  className="flex-1 bg-[#FAF7F2] border border-[#4A5D30]/25 rounded-xl px-4 py-3 font-['Timeless'] text-stone-900 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-[#4A5D30]/30 focus:border-[#4A5D30] placeholder:text-stone-400"
                />
                <button
                  type="submit"
                  className="bg-[#4A5D30] hover:bg-[#3D4C27] text-[#F6F0E6] font-['Timeless'] font-semibold text-xs uppercase tracking-wider px-5 py-3 rounded-xl transition-all shadow-xs cursor-pointer"
                >
                  Search
                </button>
              </form>

              {/* Popular Route Suggestions */}
              <div className="font-['Timeless']">
                <p className="text-xs font-['Timeless'] font-semibold text-stone-600 uppercase tracking-wider mb-2">
                  Popular corridors to try:
                </p>
                <div className="flex flex-wrap gap-2">
                  {POPULAR_SUGGESTIONS.map((s, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => navigate(`/results?nlp=${encodeURIComponent(s.query)}`)}
                      className="bg-[#FAF7F2] hover:bg-[#E5D5BF] border border-[#4A5D30]/20 text-stone-700 px-3 py-1.5 rounded-lg text-xs font-['Timeless'] font-medium transition-all cursor-pointer"
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Route Insights Header */}
          {results && !loading && !needsClarification && nlpQuery && (
            <div className="flex items-center gap-2 mb-3.5 font-['Timeless']">
              <h3 className="font-['Timeless'] text-sm font-bold text-[#4A5D30] tracking-wide">
                Route Insights
              </h3>
              <span className="bg-[#F6F0E6] text-stone-700 text-xs px-2.5 py-1 rounded-md border border-[#4A5D30]/20 italic font-medium">
                &ldquo;{nlpQuery}&rdquo;
              </span>
            </div>
          )}

          {/* Loading Spinner */}
          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center py-20 font-['Timeless']">
              <div className="w-10 h-10 border-3 border-[#4A5D30]/30 border-t-[#4A5D30] rounded-xl animate-spin" />
              <p className="mt-4 text-[#4A5D30] font-['Timeless'] text-sm font-semibold transition-all duration-300">
                {LOADING_MESSAGES[loadingMsgIndex]}
              </p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-red-50 text-red-700 border border-red-200 rounded-2xl p-6 text-center font-['Timeless'] my-auto">
              <p className="font-semibold mb-1">Search could not be completed</p>
              <p className="text-xs opacity-80 mb-4">{error}</p>
              <button
                onClick={() => fetchRoutes()}
                className="px-5 py-2.5 bg-[#4A5D30] text-[#F6F0E6] rounded-xl text-xs font-semibold hover:bg-[#3D4C27] transition-colors shadow-xs cursor-pointer font-['Timeless']"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Filter Bar */}
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
            <div className="flex flex-col gap-4 pb-8 font-['Timeless']">
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
                <div className="bg-[#F6F0E6] rounded-2xl p-6 text-center border border-[#4A5D30]/20 shadow-xs font-['Timeless']">
                  <p className="font-['Timeless'] text-base font-bold text-[#4A5D30] mb-1">
                    No routes found matching filter &ldquo;{selectedFilter.replace(/_/g, ' ')}&rdquo;
                  </p>
                  <p className="text-xs text-stone-600 mb-4 font-['Timeless']">
                    Try switching back to All Routes or another filter.
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFilter('ALL');
                      if (routeCards.length > 0) setSelectedRouteId(routeCards[0].id);
                    }}
                    className="bg-[#4A5D30] hover:bg-[#3D4C27] text-[#F6F0E6] font-['Timeless'] px-4 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
                  >
                    View All {routeCards.length} Available Routes
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Inverted Architectural Bottom Strip (Page 1 footer with inverted colors: light cream bg, dark green text & logo) */}
      <footer className="w-full bg-[#F6F0E6] border-t border-[#4A5D30]/25 py-3.5 px-6 sm:px-10 flex items-center justify-between shrink-0 z-20 shadow-md">
        {/* Logo: MargDarshak in ROSSTEN font - dark green! */}
        <div className="flex items-center">
          <Link
            to="/"
            className="text-[#4A5D30] text-[26px] sm:text-[32px] tracking-wider select-none font-normal hover:opacity-85 transition-opacity"
            style={{ fontFamily: "'ROSSTEN', sans-serif" }}
          >
            MargDarshak
          </Link>
        </div>

        {/* Slogan naturally positioned at bottom right */}
        <div className="flex items-center">
          <p
            className="text-[#4A5D30]/90 text-[16px] sm:text-[18px] tracking-wide font-normal select-none"
            style={{ fontFamily: "'OFLGoudyStM', Georgia, serif" }}
          >
            Less rush. More wonder.
          </p>
        </div>
      </footer>
    </div>
  );
}
