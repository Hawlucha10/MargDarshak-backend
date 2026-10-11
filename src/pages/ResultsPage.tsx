import { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import RouteMap from '../components/RouteMap';
import RouteCard, { type RouteItem } from '../components/RouteCard';
import ParetoFilterBar, { type ParetoFilterKey, type ParetoFilterCounts } from '../components/ParetoFilterBar';
import { useChat } from '../context/ChatContext';
import { getRecentSearches, saveRecentSearch, type RecentSearchItem } from '../utils/recentSearches';

const API_BASE = import.meta.env.VITE_API_URL || '';

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
  const { toggleChat } = useChat();
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);
  const [error, setError] = useState('');
  const [selectedRouteId, setSelectedRouteId] = useState<string>('route-0');
  const [expandedRouteId, setExpandedRouteId] = useState<string | null>(null);
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
  const [recentSearches, setRecentSearches] = useState<RecentSearchItem[]>(() => getRecentSearches());
  const [mobileTab, setMobileTab] = useState<'list' | 'map'>('list');

  useEffect(() => {
    const handleUpdate = () => setRecentSearches(getRecentSearches());
    window.addEventListener('recentSearchesUpdated', handleUpdate);
    return () => window.removeEventListener('recentSearchesUpdated', handleUpdate);
  }, []);

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

        if (data.origin && data.destination && data.total_routes_found > 0) {
          saveRecentSearch({
            type: 'nlp',
            query: nlp,
            originCode: data.origin,
            destCode: data.destination,
            label: `${data.origin} → ${data.destination}`,
            date: data.travel_date,
          });
        }

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

        if (data.origin && data.destination && data.total_routes_found > 0) {
          saveRecentSearch({
            type: 'station',
            originCode: data.origin,
            destCode: data.destination,
            label: `${data.origin} → ${data.destination}`,
            date: date,
          });
        }
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
    // Unified chronological legs list:
    type RouteLegSummary = {
      type: 'train' | 'bus';
      fromStation: string;
      toStation: string;
      departureTime: string;
      arrivalTime: string;
      durationMinutes: number;
      name: string;
      identifier: string;
      operatorOrNumber: string;
    };

    const orderedLegs: RouteLegSummary[] = [];
    if (r.legs) {
      r.legs.forEach((l) => {
        const dM = timeStrToMinutes(l.departure_time);
        const aM = timeStrToMinutes(l.arrival_time);
        let diff = aM - dM;
        if (diff < 0) diff += 1440;
        orderedLegs.push({
          type: 'train',
          fromStation: (l.from_station || '').trim().toUpperCase(),
          toStation: (l.to_station || '').trim().toUpperCase(),
          departureTime: l.departure_time || '08:00',
          arrivalTime: l.arrival_time || '18:00',
          durationMinutes: Math.max(15, diff),
          name: l.train_name || `Train ${l.train_number}`,
          identifier: l.train_number || 'Train',
          operatorOrNumber: l.train_number,
        });
      });
    }
    if (r.bus_legs) {
      r.bus_legs.forEach((b) => {
        orderedLegs.push({
          type: 'bus',
          fromStation: (b.from_station_code || '').trim().toUpperCase(),
          toStation: (b.to_station_code || '').trim().toUpperCase(),
          departureTime: b.departure_time || '08:00',
          arrivalTime: b.arrival_time || '12:00',
          durationMinutes: b.duration_minutes || 180,
          name: `${b.operator_name} (${b.bus_type})`,
          identifier: `BUS (${b.operator_code || 'EXPR'})`,
          operatorOrNumber: `BUS // ${b.operator_code || 'EXPR'}`,
        });
      });
    }

    // Sequence chaining: Sort legs so the initial boarding leg comes first (matching origin or chaining aTo -> bFrom)
    if (orderedLegs.length > 1) {
      const origCode = (results?.origin || '').trim().toUpperCase();
      orderedLegs.sort((a, b) => {
        if (origCode && a.fromStation === origCode && b.fromStation !== origCode) return -1;
        if (origCode && b.fromStation === origCode && a.fromStation !== origCode) return 1;
        if (a.toStation === b.fromStation) return -1;
        if (b.toStation === a.fromStation) return 1;
        const mA = timeStrToMinutes(a.departureTime);
        const mB = timeStrToMinutes(b.departureTime);
        return mA - mB;
      });
    }

    // Display title & train/bus identifiers respecting first leg first
    let computedName = 'Train Connection';
    let computedNumber = '';
    if (orderedLegs.length > 0) {
      if (orderedLegs.length === 1) {
        computedName = orderedLegs[0].name;
        computedNumber = orderedLegs[0].identifier;
      } else {
        // First leg first, then second leg (e.g. Bus first if bus starts the journey)
        computedName = `${orderedLegs[0].name} + ${orderedLegs[1].name}`;
        computedNumber = orderedLegs.map((l) => l.identifier).join(' → ');
      }
    }

    // Departure is strictly the first leg's departure; Arrival is strictly the final leg's arrival
    const computedDeparture = (
      orderedLegs.length > 0
        ? orderedLegs[0].departureTime
        : (r.departure_time || '--:--')
    ).slice(0, 5);

    const computedArrival = (
      orderedLegs.length > 0
        ? orderedLegs[orderedLegs.length - 1].arrivalTime
        : (r.arrival_time || '--:--')
    ).slice(0, 5);

    // Accurate total duration calculation:
    // Total total duration = Sum of all leg travel times + all waiting halt / layover times between consecutive legs
    let totalMins = 0;
    for (let idx = 0; idx < orderedLegs.length; idx++) {
      totalMins += orderedLegs[idx].durationMinutes;

      // Add waiting halt time before the next connecting leg
      if (idx < orderedLegs.length - 1) {
        const curArrM = timeStrToMinutes(orderedLegs[idx].arrivalTime);
        const nextDepM = timeStrToMinutes(orderedLegs[idx + 1].departureTime);
        let haltM = nextDepM - curArrM;
        if (haltM < 0) haltM += 1440;

        // Ensure we respect transfer buffer if transfers_info specifies a larger safety buffer
        const matchingTransfer = r.transfers_info?.find(
          (t) => t.station_code === orderedLegs[idx].toStation
        ) || (r.transfers_info && r.transfers_info[idx]);
        if (matchingTransfer && matchingTransfer.wait_time_minutes > haltM) {
          haltM = matchingTransfer.wait_time_minutes;
        }

        totalMins += haltM;
      }
    }

    // If backend provided a total_travel_minutes that is larger (e.g. multi-day long distance runs), respect it
    if (r.total_travel_minutes && r.total_travel_minutes > totalMins) {
      totalMins = r.total_travel_minutes;
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

    // Calculate tentative fare range in rupees (Sleeper to 3 AC across all train legs + bus legs)
    let minFare = 0;
    let maxFare = 0;

    if (r.legs && r.legs.length > 0) {
      r.legs.forEach((leg) => {
        let legSl = leg.fare_estimate || 0;
        if (!legSl && r.total_fare) {
          legSl = Math.round(r.total_fare / r.legs.length);
        }
        if (!legSl) legSl = 345;
        const leg3Ac = Math.round((legSl * 3.55) / 5) * 5;
        minFare += legSl;
        maxFare += leg3Ac;
      });
    }

    if (r.bus_legs && r.bus_legs.length > 0) {
      r.bus_legs.forEach((b) => {
        const bFare = b.fare || 150;
        minFare += bFare;
        maxFare += bFare;
      });
    }

    if (minFare === 0) {
      minFare = r.total_fare || 345;
      maxFare = Math.round((minFare * 3.55) / 5) * 5;
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
      fare: `₹${minFare}–₹${maxFare}`,
      fareMin: minFare,
      fareMax: maxFare,
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
    MULTIMODAL: routeCards.filter((r) => r.isMultimodal || r.hasBusLeg || r.label === 'MULTIMODAL_FASTEST' || r.label === 'MULTIMODAL' || (r.bus_legs && r.bus_legs.length > 0)).length,
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
      if (selectedFilter === 'MULTIMODAL') return r.isMultimodal || r.hasBusLeg || r.label === 'MULTIMODAL_FASTEST' || r.label === 'MULTIMODAL' || (r.bus_legs && r.bus_legs.length > 0);
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
        return (a.fareMin || 0) - (b.fareMin || 0);
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
        {/* Map Area: 40% Width on desktop, responsive full-height tab on mobile */}
        <div className={`w-full md:w-[40%] md:h-full relative z-0 flex-shrink-0 border-r border-[#4A5D30]/20 ${
          mobileTab === 'map' ? 'h-full flex-1' : 'hidden md:block'
        }`}>
          <RouteMap
            legs={activeRoute?.legs}
            busLegs={activeRoute?.bus_legs}
            onOpenRouteDetails={() => {
              if (selectedRouteId) {
                setExpandedRouteId(selectedRouteId);
                setMobileTab('list');
                const el = document.getElementById(selectedRouteId);
                if (el) {
                  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
              }
            }}
          />
        </div>

        {/* Route & NLP Response Area: 60% Width on desktop, responsive full-height tab on mobile */}
        <div className={`w-full md:w-[60%] md:h-full overflow-y-auto bg-[#E5D5BF] p-5 sm:p-7 md:p-8 flex flex-col shadow-inner font-['Timeless'] ${
          mobileTab === 'list' ? 'h-full flex-1' : 'hidden md:flex'
        }`}>
          {/* Header with Title and Query Metrics */}
          <div className="mb-4 pt-1 font-['Timeless']">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-['Timeless'] text-[#4A5D30] font-bold tracking-tight">
                {loading
                  ? 'Planning Routes...'
                  : needsClarification
                  ? 'Journey Clarification Needed'
                  : results && results.total_routes_found > 0
                  ? `${results.total_routes_found} Optimal Routes`
                  : 'No Direct Routes Found'}
              </h2>

              {/* Quick switch to recent searches */}
              {recentSearches.length > 0 && !loading && (
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-stone-600 text-xs font-semibold uppercase tracking-wider">Recent:</span>
                  {recentSearches.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => {
                        if (s.type === 'station' && s.originCode && s.destCode) {
                          navigate(`/results?origin=${encodeURIComponent(s.originCode)}&destination=${encodeURIComponent(s.destCode)}&date=${encodeURIComponent(s.date || '')}`);
                        } else if (s.query) {
                          navigate(`/results?nlp=${encodeURIComponent(s.query)}`);
                        } else {
                          navigate(`/results?nlp=${encodeURIComponent(s.label)}`);
                        }
                      }}
                      className="bg-[#F6F0E6] hover:bg-[#E5D5BF] border border-[#4A5D30]/25 text-[#4A5D30] px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1 active:scale-95 shadow-2xs"
                      title={`Switch to ${s.label}`}
                    >
                      <span>{s.label}</span>
                    </button>
                  ))}
                </div>
              )}
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
                <div className="w-10 h-10 rounded-xl bg-[#E5D5BF] border border-[#4A5D30]/25 flex items-center justify-center text-[#4A5D30] shrink-0">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" strokeWidth="2" />
                    <polygon points="12 8 16 16 12 14 8 16" fill="currentColor" />
                  </svg>
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

              {/* Recent searches in clarification card */}
              {recentSearches.length > 0 && (
                <div className="font-['Timeless'] mb-3">
                  <p className="text-xs font-['Timeless'] font-semibold text-[#4A5D30] uppercase tracking-wider mb-2">
                    Recent searches:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {recentSearches.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => {
                          if (s.type === 'station' && s.originCode && s.destCode) {
                            navigate(`/results?origin=${encodeURIComponent(s.originCode)}&destination=${encodeURIComponent(s.destCode)}&date=${encodeURIComponent(s.date || '')}`);
                          } else if (s.query) {
                            navigate(`/results?nlp=${encodeURIComponent(s.query)}`);
                          } else {
                            navigate(`/results?nlp=${encodeURIComponent(s.label)}`);
                          }
                        }}
                        className="bg-[#FAF7F2] hover:bg-[#E5D5BF] border border-[#4A5D30]/30 text-[#4A5D30] px-3 py-1.5 rounded-lg text-xs font-['Timeless'] font-bold transition-all cursor-pointer flex items-center gap-1"
                      >
                        <span>{s.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

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
                    isExpanded={expandedRouteId === route.id}
                    onSelect={() => setSelectedRouteId(route.id)}
                    onToggleExpand={() => {
                      setSelectedRouteId(route.id);
                      setExpandedRouteId((prev) => (prev === route.id ? null : route.id));
                    }}
                  />
                ))
              ) : routeCards.length > 0 ? (
                <>
                  <div className="bg-[#F6F0E6] rounded-2xl p-5 text-center border border-[#4A5D30]/20 shadow-xs font-['Timeless'] mb-2">
                    <p className="font-['Timeless'] text-sm sm:text-base font-bold text-[#4A5D30] mb-1">
                      No routes match the &ldquo;{selectedFilter.replace(/_/g, ' ')}&rdquo; filter on this corridor.
                    </p>
                    <p className="text-xs text-stone-600 mb-3 font-['Timeless']">
                      Showing all {routeCards.length} available direct & connecting options below:
                    </p>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedFilter('ALL');
                        if (routeCards.length > 0) setSelectedRouteId(routeCards[0].id);
                      }}
                      className="bg-[#4A5D30] hover:bg-[#3D4C27] text-[#F6F0E6] font-['Timeless'] px-4 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
                    >
                      Reset Filter to All Routes
                    </button>
                  </div>
                  {routeCards.map((route, i) => (
                    <RouteCard
                      key={route.id}
                      route={route}
                      index={i}
                      isActive={selectedRouteId === route.id}
                      isExpanded={expandedRouteId === route.id}
                      onSelect={() => setSelectedRouteId(route.id)}
                      onToggleExpand={() => {
                        setSelectedRouteId(route.id);
                        setExpandedRouteId((prev) => (prev === route.id ? null : route.id));
                      }}
                    />
                  ))}
                </>
              ) : (
                /* Total 0 routes found for corridor on this date: Intelligent suggestion card */
                <div className="bg-[#F6F0E6] rounded-2xl p-6 sm:p-7 border border-[#4A5D30]/20 shadow-sm font-['Timeless'] animate-fadeIn">
                  <div className="flex items-start gap-3.5 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-[#E5D5BF] border border-[#4A5D30]/25 flex items-center justify-center text-[#4A5D30] shrink-0">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-[#4A5D30]">
                        No direct or 2-hop routes found for this corridor on {results?.travel_date || 'this date'}
                      </h3>
                      <p className="text-xs sm:text-sm text-stone-600 mt-1 leading-relaxed">
                        Many Indian Railways trains run on tri-weekly or alternate day schedules. Try checking tomorrow, or connect via a major junction hub below.
                      </p>
                    </div>
                  </div>

                  {/* Quick Action: Search Next Day or Ask AI */}
                  <div className="flex flex-wrap items-center gap-3 pt-2 pb-4 border-b border-[#4A5D30]/15">
                    <button
                      type="button"
                      onClick={() => {
                        const curDate = results?.travel_date || new Date().toISOString().split('T')[0];
                        const d = new Date(curDate);
                        d.setDate(d.getDate() + 1);
                        const nextDateStr = d.toISOString().split('T')[0];
                        const orig = results?.origin || searchParams.get('origin') || '';
                        const dest = results?.destination || searchParams.get('destination') || '';
                        navigate(`/results?origin=${encodeURIComponent(orig)}&destination=${encodeURIComponent(dest)}&date=${encodeURIComponent(nextDateStr)}`);
                      }}
                      className="bg-[#4A5D30] hover:bg-[#3D4C27] text-[#FAF7F2] px-4 py-2.5 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all shadow-xs flex items-center gap-1.5 cursor-pointer active:scale-95"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span>Check Next Day (+1 Day)</span>
                    </button>

                    <button
                      type="button"
                      onClick={toggleChat}
                      className="bg-[#FAF7F2] hover:bg-[#E5D5BF] border border-[#4A5D30]/30 text-[#4A5D30] px-4 py-2.5 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer active:scale-95"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                      </svg>
                      <span>Ask MargDarshak AI</span>
                    </button>
                  </div>

                  {/* Major Connecting Railway Hubs */}
                  <div className="pt-4">
                    <p className="text-xs font-bold uppercase tracking-wider text-[#4A5D30] mb-2.5">
                      Suggested Major Interchange Hubs
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                      {[
                        { code: 'BPL', name: 'Bhopal Jn' },
                        { code: 'ET', name: 'Itarsi Jn' },
                        { code: 'NDLS', name: 'New Delhi' },
                        { code: 'BRC', name: 'Vadodara Jn' },
                        { code: 'PUNE', name: 'Pune Jn' },
                        { code: 'JHS', name: 'VGL Jhansi' },
                        { code: 'CNB', name: 'Kanpur Central' },
                      ]
                        .filter(
                          (h) =>
                            h.code !== (results?.origin || '').toUpperCase() &&
                            h.code !== (results?.destination || '').toUpperCase()
                        )
                        .slice(0, 4)
                        .map((hub) => {
                          const orig = results?.origin || searchParams.get('origin') || '';
                          const dest = results?.destination || searchParams.get('destination') || '';
                          const curDate = results?.travel_date || '';
                          return (
                            <div
                              key={hub.code}
                              className="bg-[#FAF7F2] p-3 rounded-xl border border-[#4A5D30]/20 flex flex-col justify-between gap-2"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-stone-900 text-xs truncate">{hub.name}</span>
                                <span className="text-[#4A5D30] font-bold text-xs shrink-0">({hub.code})</span>
                              </div>
                              <div className="flex gap-1.5 text-[11px]">
                                <button
                                  type="button"
                                  onClick={() =>
                                    navigate(
                                      `/results?origin=${encodeURIComponent(orig)}&destination=${encodeURIComponent(hub.code)}&date=${encodeURIComponent(curDate)}`
                                    )
                                  }
                                  className="flex-1 bg-[#E5D5BF]/50 hover:bg-[#E5D5BF] text-[#4A5D30] py-1 px-1.5 rounded-md text-center font-medium transition-colors truncate cursor-pointer"
                                  title={`Search ${orig} to ${hub.code}`}
                                >
                                  {orig} → {hub.code}
                                </button>
                                <button
                                  type="button"
                                  onClick={() =>
                                    navigate(
                                      `/results?origin=${encodeURIComponent(hub.code)}&destination=${encodeURIComponent(dest)}&date=${encodeURIComponent(curDate)}`
                                    )
                                  }
                                  className="flex-1 bg-[#E5D5BF]/50 hover:bg-[#E5D5BF] text-[#4A5D30] py-1 px-1.5 rounded-md text-center font-medium transition-colors truncate cursor-pointer"
                                  title={`Search ${hub.code} to ${dest}`}
                                >
                                  {hub.code} → {dest}
                                </button>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Mobile Floating Pill Toggle (Map / List) - Only visible on small screens (< md) */}
      {!loading && !error && (
        <div className="md:hidden fixed bottom-18 left-1/2 -translate-x-1/2 z-30 pointer-events-auto">
          <button
            type="button"
            onClick={() => setMobileTab((prev) => (prev === 'list' ? 'map' : 'list'))}
            className="bg-[#111111] hover:bg-[#222222] text-[#FAF7F2] px-5 py-2.5 rounded-full shadow-2xl flex items-center gap-2 text-xs font-semibold uppercase tracking-wider border border-white/20 active:scale-95 transition-all cursor-pointer"
          >
            {mobileTab === 'list' ? (
              <>
                <svg className="w-4 h-4 text-[#E5D5BF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
                <span>View Map</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4 text-[#E5D5BF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                <span>View Routes ({displayedRouteCards.length})</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Inverted Architectural Bottom Strip (Page 1 footer with inverted colors: light cream bg, dark green text & logo) */}
      <footer className="w-full bg-[#F6F0E6] border-t border-[#4A5D30]/25 py-3.5 px-6 sm:px-10 flex items-center justify-between shrink-0 z-20 shadow-md">
        {/* Logo: MargDarshak in ROSSTEN font - dark green! */}
        <div className="flex-1 flex justify-start items-center">
          <Link
            to="/"
            className="text-[#4A5D30] text-[26px] sm:text-[32px] tracking-wider select-none font-normal hover:opacity-85 transition-opacity"
            style={{ fontFamily: "'ROSSTEN', sans-serif" }}
          >
            MargDarshak
          </Link>
        </div>

        {/* Center: MargDarshak AI text button directly on the strip itself */}
        <div className="flex-1 flex justify-center items-center">
          <button
            type="button"
            onClick={toggleChat}
            className="text-[#4A5D30] hover:text-[#3D4C27] text-[16px] sm:text-[18px] tracking-wide font-semibold select-none cursor-pointer hover:opacity-85 transition-opacity"
            style={{ fontFamily: "'Timeless', sans-serif" }}
          >
            MargDarshak AI
          </button>
        </div>

        {/* Slogan naturally positioned at bottom right - hidden on phone screens to avoid congestion */}
        <div className="hidden md:flex flex-1 justify-end items-center">
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
