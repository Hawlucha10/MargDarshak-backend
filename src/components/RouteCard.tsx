import { useState, useEffect, useMemo } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface Leg {
  train_number: string;
  train_name: string;
  from_station: string;
  from_station_name: string;
  to_station: string;
  to_station_name: string;
  departure_time: string;
  arrival_time: string;
  day?: number;
  predicted_delay_min: number;
  fare_estimate: number | null;
  departure_platform?: string;
  arrival_platform?: string;
  mode?: string;
}

interface BusLeg {
  operator_name: string;
  operator_code: string;
  bus_type: string;
  from_terminal: string;
  to_terminal: string;
  from_station_code: string;
  to_station_code: string;
  departure_time: string;
  arrival_time: string;
  duration_minutes: number;
  fare: number;
  is_ac: boolean;
  rating?: number | null;
  walk_to_terminal_min?: number;
  walk_from_terminal_min?: number;
}

interface TransferInfo {
  station_code: string;
  station_name: string;
  wait_time_minutes: number;
  is_safe?: boolean;
  delay_risk_warning?: string;
  arrival_platform?: string;
  departure_platform?: string;
  interchange_guide?: string;
  bus_alternatives_count?: number;
}

export interface RouteItem {
  id: string;
  label?: string;
  trainName: string;
  trainNumber: string;
  departure: string;
  arrival: string;
  departureDate?: string;
  arrivalDate?: string;
  duration: string;
  fare: string;
  fareMin?: number;
  fareMax?: number;
  transfers?: number;
  reliability?: string;
  hasBusLeg?: boolean;
  isComfortable?: boolean;
  isMultimodal?: boolean;
  legs?: Leg[];
  bus_legs?: BusLeg[];
  transfers_info?: TransferInfo[];
  fare_arbitrage_tip?: string;
  accessibility_badge?: string;
  weather_advisory?: string;
  time_saved_vs_train_minutes?: number | null;
  comfort_score?: number | null;
}

interface RouteProps {
  route: RouteItem;
  index: number;
  isActive?: boolean;
  isExpanded?: boolean;
  onSelect?: () => void;
  onToggleExpand?: () => void;
}

interface ScheduleStop {
  station_code: string;
  station_name: string;
  arrival: string | null;
  departure: string | null;
  day: number;
  stop_sequence?: number;
}

export type UnifiedLeg = { type: 'train'; leg: Leg; index: number } | { type: 'bus'; leg: BusLeg; index: number };

function formatLayover(minutes: number): string {
  if (minutes < 60) return `${minutes} minutes`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h} hours`;
}

function getSimpleLabel(label?: string, hasBus?: boolean, isDirectBus?: boolean): string | null {
  if (isDirectBus) return 'Direct Express Bus';
  if (!label || label === 'ALTERNATIVE') {
    return hasBus ? 'Train + bus combo' : null;
  }
  switch (label) {
    case 'FASTEST':
      return 'Fastest route';
    case 'CHEAPEST':
      return 'Lowest fare';
    case 'BALANCED':
      return 'Recommended';
    case 'MOST_RELIABLE':
      return 'Most reliable';
    case 'COMFORT_HOMESTAY':
      return 'Less waiting time';
    case 'MULTIMODAL_FASTEST':
      return 'Fastest bus option';
    case 'MULTIMODAL':
      return 'Train + bus combo';
    case 'FEWEST_TRANSFERS':
      return 'Fewest changes';
    default:
      return hasBus ? 'Train + bus combo' : null;
  }
}

function cleanTipText(tip?: string, trainNumber?: string): string {
  if (!tip) return '';
  let clean = tip.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '').trim();
  clean = clean.replace(/^Upstream GNWL Quota:\s*/i, '');
  clean = clean.replace(/^Direct Origin Quota:\s*/i, '');

  const upstreamMatch = clean.match(
    /(?:Train\s+(\w+)\s+originates\s+at|This train starts\s+(?:at|from))\s+([^(.]+?(?:\s*\([^)]+\))?)\.\s*If\s+(?:waitlisted|tickets)\s+from\s+([^,]+?)(?:,\s*|\s+are\s+on\s+waiting\s+list,\s*)(?:booking|you can book)\s+from\s+([^(.]+?(?:\s*\([^)]+\))?)\s+with\s+boarding\s+at\s+([^.]+?)\s+(?:unlocks|helps(?: you get)?|to get)\s+a?\s*confirmed\s+(?:General Quota\s+)?seat[s]?(?:\s*\((\+?Rs\.?\s*\d+|extra\s+Rs\.?\s*\d+)\))?/i
  );

  if (upstreamMatch) {
    const tNum = upstreamMatch[1] || trainNumber || '';
    const startStation = upstreamMatch[2].trim();
    const boardStation = upstreamMatch[3].trim();
    const rawExtra = upstreamMatch[6] ? upstreamMatch[6].replace(/\+?Rs\.?\s*/i, '₹') : '';
    const extraFareText = rawExtra ? ` (extra ${rawExtra})` : '';
    const trainText = tNum ? `this train (${tNum})` : 'this train';
    return `If you want a confirmed seat, ${trainText} starts at ${startStation}. If tickets from ${boardStation} are on waiting list, you can book from ${startStation} with boarding at ${boardStation} to get a confirmed seat${extraFareText}.`;
  }

  if (/^If you want a confirmed? seat/i.test(clean)) {
    return clean;
  }

  if (/starts right (?:at|from)/i.test(clean) || /Boarding at starting terminal/i.test(clean)) {
    const trainText = trainNumber ? `this train (${trainNumber})` : 'this train';
    const stMatch = clean.match(/\(([^)]+)\)/);
    const stName = stMatch ? stMatch[1] : '';
    return `If you want a confirmed seat, ${trainText} starts right from ${stName || 'your boarding station'}, giving you the best chance of getting a confirmed ticket.`;
  }

  if (!clean.toLowerCase().includes('if you want a confirm')) {
    clean = clean.replace(/^Train\s+(\w+)\s+originates\s+at\s+/i, (_m, num) => `If you want a confirmed seat, this train (${num}) starts at `);
    clean = clean.replace(/^This train starts (?:at|from)\s+/i, 'If you want a confirmed seat, this train starts at ');
  }

  return clean.trim();
}

function cleanWeatherText(text?: string): string {
  if (!text) return '';
  let clean = text.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '').trim();
  clean = clean.replace(/^Weather Advisory:\s*/i, '');
  return clean.trim();
}

// Module-level global timetable cache & in-flight promise registry
const scheduleCache: Record<string, ScheduleStop[]> = {};
const pendingScheduleRequests: Record<string, Promise<ScheduleStop[]>> = {};

function parseMinutes(t?: string | null): number | null {
  if (!t || t === 'None' || t === 'null') return null;
  const parts = t.slice(0, 5).split(':');
  if (parts.length < 2) return null;
  const h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  return isNaN(h) || isNaN(m) ? null : h * 60 + m;
}

function getLegKey(leg: Leg): string {
  return `${(leg.train_number || '').trim()}_${(leg.from_station || '').trim()}_${(leg.to_station || '').trim()}`;
}

async function fetchTrainStops(trainNumber: string): Promise<ScheduleStop[]> {
  const clean = trainNumber.trim();
  if (clean in scheduleCache) return scheduleCache[clean];
  if (clean in pendingScheduleRequests) return pendingScheduleRequests[clean];

  const requestPromise = fetch(`${API_BASE}/api/v1/trains/${clean}/schedule`)
    .then((res) => (res.ok ? res.json() : null))
    .then((data) => {
      const stops: ScheduleStop[] = data && Array.isArray(data.stops) ? data.stops : [];
      scheduleCache[clean] = stops;
      delete pendingScheduleRequests[clean];
      return stops;
    })
    .catch((err) => {
      console.error(`Failed to fetch schedule for train ${clean}`, err);
      delete pendingScheduleRequests[clean];
      return [];
    });

  pendingScheduleRequests[clean] = requestPromise;
  return requestPromise;
}

function extractLegStops(allStops: ScheduleStop[], leg: Leg): ScheduleStop[] {
  if (!allStops || allStops.length === 0) {
    return [
      {
        station_code: leg.from_station,
        station_name: leg.from_station_name || leg.from_station,
        arrival: null,
        departure: leg.departure_time,
        day: 1,
        stop_sequence: 1,
      },
      {
        station_code: leg.to_station,
        station_name: leg.to_station_name || leg.to_station,
        arrival: leg.arrival_time,
        departure: null,
        day: leg.day || 1,
        stop_sequence: 2,
      },
    ];
  }

  const fromCode = (leg.from_station || '').trim().toUpperCase();
  const toCode = (leg.to_station || '').trim().toUpperCase();

  const fromIndices: number[] = [];
  const toIndices: number[] = [];

  for (let i = 0; i < allStops.length; i++) {
    const code = (allStops[i].station_code || '').trim().toUpperCase();
    if (code === fromCode) fromIndices.push(i);
    if (code === toCode) toIndices.push(i);
  }

  // Name matching fallback
  if (fromIndices.length === 0 && leg.from_station_name) {
    const fName = leg.from_station_name.trim().toLowerCase();
    for (let i = 0; i < allStops.length; i++) {
      const sName = (allStops[i].station_name || '').trim().toLowerCase();
      if (sName && (sName.includes(fName) || fName.includes(sName))) {
        fromIndices.push(i);
      }
    }
  }

  if (toIndices.length === 0 && leg.to_station_name) {
    const tName = leg.to_station_name.trim().toLowerCase();
    for (let i = 0; i < allStops.length; i++) {
      const sName = (allStops[i].station_name || '').trim().toLowerCase();
      if (sName && (sName.includes(tName) || tName.includes(sName))) {
        toIndices.push(i);
      }
    }
  }

  const legDepMin = parseMinutes(leg.departure_time);
  const legArrMin = parseMinutes(leg.arrival_time);

  type Candidate = { i: number; j: number; score: number };

  // 1. Forward candidates (destination after origin in stop sequence)
  const forwardCandidates: Candidate[] = [];
  for (const i of fromIndices) {
    for (const j of toIndices) {
      if (j > i) {
        let score = 0;
        const stDepMin = parseMinutes(allStops[i].departure || allStops[i].arrival);
        const stArrMin = parseMinutes(allStops[j].arrival || allStops[j].departure);

        if (legDepMin !== null && stDepMin !== null) {
          const diff = Math.abs(legDepMin - stDepMin);
          score += Math.min(diff, Math.abs(diff - 1440));
        }
        if (legArrMin !== null && stArrMin !== null) {
          const diff = Math.abs(legArrMin - stArrMin);
          score += Math.min(diff, Math.abs(diff - 1440));
        }

        forwardCandidates.push({ i, j, score });
      }
    }
  }

  if (forwardCandidates.length > 0) {
    forwardCandidates.sort((a, b) => a.score - b.score);
    const best = forwardCandidates[0];
    return allStops.slice(best.i, best.j + 1);
  }

  // 2. Reverse candidates (sequence inverted in database timetable)
  const reverseCandidates: Candidate[] = [];
  for (const i of fromIndices) {
    for (const j of toIndices) {
      if (i > j) {
        let score = 0;
        const stDepMin = parseMinutes(allStops[i].departure || allStops[i].arrival);
        const stArrMin = parseMinutes(allStops[j].arrival || allStops[j].departure);

        if (legDepMin !== null && stDepMin !== null) {
          const diff = Math.abs(legDepMin - stDepMin);
          score += Math.min(diff, Math.abs(diff - 1440));
        }
        if (legArrMin !== null && stArrMin !== null) {
          const diff = Math.abs(legArrMin - stArrMin);
          score += Math.min(diff, Math.abs(diff - 1440));
        }

        reverseCandidates.push({ i, j, score });
      }
    }
  }

  if (reverseCandidates.length > 0) {
    reverseCandidates.sort((a, b) => a.score - b.score);
    const best = reverseCandidates[0];
    return allStops.slice(best.j, best.i + 1).reverse();
  }

  // 3. Partial match anchoring
  if (fromIndices.length > 0) {
    const i = fromIndices[0];
    const sliced = allStops.slice(i);
    return [
      ...sliced,
      {
        station_code: leg.to_station,
        station_name: leg.to_station_name || leg.to_station,
        arrival: leg.arrival_time,
        departure: null,
        day: leg.day || 1,
        stop_sequence: sliced.length + 1,
      },
    ];
  }

  if (toIndices.length > 0) {
    const j = toIndices[toIndices.length - 1];
    const sliced = allStops.slice(0, j + 1);
    return [
      {
        station_code: leg.from_station,
        station_name: leg.from_station_name || leg.from_station,
        arrival: null,
        departure: leg.departure_time,
        day: 1,
        stop_sequence: 1,
      },
      ...sliced,
    ];
  }

  // 4. Fallback to leg endpoints
  return [
    {
      station_code: leg.from_station,
      station_name: leg.from_station_name || leg.from_station,
      arrival: null,
      departure: leg.departure_time,
      day: 1,
      stop_sequence: 1,
    },
    {
      station_code: leg.to_station,
      station_name: leg.to_station_name || leg.to_station,
      arrival: leg.arrival_time,
      departure: null,
      day: leg.day || 1,
      stop_sequence: 2,
    },
  ];
}

export default function RouteCard({
  route,
  index,
  isActive,
  isExpanded: controlledExpanded,
  onSelect,
  onToggleExpand,
}: RouteProps) {
  const [localExpanded, setLocalExpanded] = useState(false);
  const isExpanded = controlledExpanded !== undefined ? controlledExpanded : localExpanded;

  const [schedules, setSchedules] = useState<Record<string, ScheduleStop[]>>({});
  const [loadingSchedule, setLoadingSchedule] = useState<Record<string, boolean>>({});

  const formattedIndex = String(index + 1).padStart(2, '0');

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onToggleExpand) {
      onToggleExpand();
    } else {
      setLocalExpanded((prev) => !prev);
    }
  };

  // Fetch full station timetable stops with arrival and departure timings when card expands
  useEffect(() => {
    if (!isExpanded || !route.legs || route.legs.length === 0) return;

    let isMounted = true;

    for (const leg of route.legs) {
      const tNum = leg.train_number?.trim();
      const legKey = getLegKey(leg);

      if (!tNum) continue;

      if (scheduleCache[tNum]) {
        const stops = extractLegStops(scheduleCache[tNum], leg);
        setSchedules((prev) => ({ ...prev, [legKey]: stops }));
        continue;
      }

      setLoadingSchedule((prev) => ({ ...prev, [legKey]: true }));
      fetchTrainStops(tNum)
        .then((rawStops) => {
          if (!isMounted) return;
          const stops = extractLegStops(rawStops, leg);
          setSchedules((prev) => ({ ...prev, [legKey]: stops }));
        })
        .finally(() => {
          if (isMounted) {
            setLoadingSchedule((prev) => ({ ...prev, [legKey]: false }));
          }
        });
    }

    return () => {
      isMounted = false;
    };
  }, [isExpanded, route.legs]);

  const allLegs: UnifiedLeg[] = useMemo(() => {
    const list: UnifiedLeg[] = [];
    if (route.legs) {
      route.legs.forEach((leg, idx) => list.push({ type: 'train', leg, index: idx }));
    }
    if (route.bus_legs) {
      route.bus_legs.forEach((leg, idx) => list.push({ type: 'bus', leg, index: idx }));
    }
    list.sort((a, b) => {
      const aFrom = ((a.type === 'train' ? (a.leg as Leg).from_station : (a.leg as BusLeg).from_station_code) || '').trim().toUpperCase();
      const aTo = ((a.type === 'train' ? (a.leg as Leg).to_station : (a.leg as BusLeg).to_station_code) || '').trim().toUpperCase();
      const bFrom = ((b.type === 'train' ? (b.leg as Leg).from_station : (b.leg as BusLeg).from_station_code) || '').trim().toUpperCase();
      const bTo = ((b.type === 'train' ? (b.leg as Leg).to_station : (b.leg as BusLeg).to_station_code) || '').trim().toUpperCase();

      if (aTo === bFrom) return -1;
      if (bTo === aFrom) return 1;

      const depA = a.type === 'train' ? (a.leg as Leg).departure_time : (a.leg as BusLeg).departure_time;
      const depB = b.type === 'train' ? (b.leg as Leg).departure_time : (b.leg as BusLeg).departure_time;
      const mA = parseMinutes(depA) ?? 0;
      const mB = parseMinutes(depB) ?? 0;
      return mA - mB;
    });
    return list;
  }, [route.legs, route.bus_legs]);

  const [copied, setCopied] = useState(false);

  const minFare = route.fareMin || 345;
  const maxFare = route.fareMax || 1225;

  const totalWaitMinutes = (route.transfers_info && route.transfers_info.length > 0)
    ? route.transfers_info.reduce((acc, t) => acc + (t.wait_time_minutes || 0), 0)
    : 0;

  const isDirectBus = Boolean(route.hasBusLeg && (!route.legs || route.legs.length === 0));

  const handleShare = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const firstLeg = allLegs[0];
    const lastLeg = allLegs[allLegs.length - 1];
    const origCode = firstLeg
      ? (firstLeg.type === 'train' ? (firstLeg.leg as Leg).from_station : (firstLeg.leg as BusLeg).from_station_code)
      : '';
    const destCode = lastLeg
      ? (lastLeg.type === 'train' ? (lastLeg.leg as Leg).to_station : (lastLeg.leg as BusLeg).to_station_code)
      : '';

    const lines = [
      `🚆 *MargDarshak Journey: ${origCode || 'Origin'} ➔ ${destCode || 'Destination'}*`,
      `📅 Departure: ${route.departure} ${route.departureDate || ''} | Arrival: ${route.arrival} ${route.arrivalDate || ''}`,
      `⏱️ Total Duration: ${route.duration}${totalWaitMinutes > 0 ? ` (incl. ${formatLayover(totalWaitMinutes)} wait)` : ''}`,
      `💰 Approx. Fare: ₹${minFare}–₹${maxFare} (SL–3AC)`,
      '',
      '📍 *Journey Steps:*',
    ];

    allLegs.forEach((uLeg, idx) => {
      if (uLeg.type === 'train') {
        const leg = uLeg.leg as Leg;
        lines.push(
          `${idx + 1}. Train ${leg.train_number} (${leg.train_name || 'Express'}): ${leg.from_station_name || leg.from_station} [${leg.departure_time?.slice(0, 5)}] ➔ ${leg.to_station_name || leg.to_station} [${leg.arrival_time?.slice(0, 5)}] (Platform ${(leg.departure_platform || '1').replace(/PF\s*/i, '')})`
        );
      } else {
        const b = uLeg.leg as BusLeg;
        lines.push(
          `${idx + 1}. Bus (${b.operator_name || 'Direct Highway Bus'}): ${b.from_terminal || b.from_station_code} [${b.departure_time?.slice(0, 5)}] ➔ ${b.to_terminal || b.to_station_code} [${b.arrival_time?.slice(0, 5)}] (~₹${b.fare})`
        );
      }
    });

    lines.push('', '🔗 Planned via MargDarshak');

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(lines.join('\n'));
        setCopied(true);
        setTimeout(() => setCopied(false), 2200);
      }
    } catch (err) {
      console.error('Failed to copy journey', err);
    }
  };

  return (
    <div
      id={route.id}
      onClick={onSelect}
      className={`bg-brand-white rounded-[22px] p-6 shadow-[var(--shadow-soft)] transition-all cursor-pointer border-2 font-['Timeless'] ${
        isActive
          ? 'border-[#4A5D30] -translate-y-1 shadow-md'
          : 'border-white/80 hover:-translate-y-0.5 hover:shadow-md'
      }`}
    >
      {/* Top Bar: Editorial Index Number + Train Name + Tentative Fare Range & Simple Label */}
      <div className="flex justify-between items-start mb-4 font-['Timeless']">
        <div className="flex items-start gap-3.5 min-w-0 pr-2">
          <span className="font-['Timeless'] text-3xl font-normal text-stone-400/60 select-none">
            {formattedIndex}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-['Timeless'] text-2xl text-[#111111] font-semibold leading-tight truncate">
                {route.trainName}
              </h3>
              {route.hasBusLeg && (
                <span className="bg-[#FAF4E8] text-[#8A6318] border border-[#8A6318]/30 text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider shrink-0 flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                  {isDirectBus ? 'Bus Only' : 'Bus Leg'}
                </span>
              )}
            </div>
            <p className="text-stone-500 font-['Timeless'] text-xs tracking-wide uppercase mt-0.5">
              {route.trainNumber}
            </p>
          </div>
        </div>

        {/* Tentative Fare Range in Rupees: Sleeper to 3 AC (e.g. ₹345–₹1,225) */}
        <div className="text-right flex-shrink-0 font-['Timeless']">
          <p className="font-['Timeless'] text-xl sm:text-2xl text-[#111111] font-bold tracking-tight">
            ₹{minFare}–₹{maxFare}
          </p>
          <p className="text-[11px] text-stone-500 font-medium font-['Timeless'] leading-tight mt-0.5">
            Tentative approx. (SL – 3AC)
          </p>
          {getSimpleLabel(route.label, route.hasBusLeg, isDirectBus) && (
            <p className="text-xs text-[#4A5D30] font-semibold mt-1 font-['Timeless']">
              {getSimpleLabel(route.label, route.hasBusLeg, isDirectBus)}
            </p>
          )}
        </div>
      </div>

      {/* Timeline: Departure → Duration (Total Total Duration incl. halts) → Arrival */}
      <div className="flex items-center justify-between font-['Timeless'] text-sm mb-4 bg-[#FAF7F2] px-4 py-3 rounded-xl border border-stone-200/60">
        <div className="text-left font-['Timeless']">
          <p className="font-bold text-[#111111] text-base font-['Timeless']">{route.departure}</p>
          <span className="text-[11px] text-stone-500 font-['Timeless'] block mt-0.5">
            {route.departureDate ? `${route.departureDate} · Departure` : 'Departure'}
          </span>
        </div>
        <div className="flex-1 px-4 flex flex-col items-center font-['Timeless']">
          <span className="text-[#4A5D30] font-['Timeless'] text-xs font-semibold mb-1">
            {route.duration}
          </span>
          <div className="w-full flex items-center">
            <div className="w-2.5 h-2.5 rounded-xs bg-[#5A6B3C]" />
            <div className="h-0.5 bg-stone-300 flex-1 mx-1" />
            <div className="w-2.5 h-2.5 rounded-xs bg-[#4A5D30]" />
          </div>
          {totalWaitMinutes > 0 && (
            <span className="text-[10px] text-stone-500 font-['Timeless'] mt-1">
              incl. {formatLayover(totalWaitMinutes)} wait
            </span>
          )}
        </div>
        <div className="text-right font-['Timeless']">
          <p className="font-bold text-[#111111] text-base font-['Timeless']">{route.arrival}</p>
          <span className="text-[11px] text-stone-500 font-['Timeless'] block mt-0.5">
            {route.arrivalDate ? `${route.arrivalDate} · Arrival` : 'Arrival'}
          </span>
        </div>
      </div>

      {/* Journey Summary: Normal text formatting, no capsules, simple English */}
      <div className="flex items-center justify-between gap-2 flex-wrap pt-1 font-['Timeless']">
        <div className="flex items-center gap-2 text-xs text-stone-700 font-medium flex-wrap font-['Timeless']">
          <span>
            {route.transfers === 0
              ? (isDirectBus ? 'Direct bus (no changes)' : 'Direct train (no changes)')
              : `${route.transfers} ${route.transfers === 1 ? 'change' : 'changes along the way'}${totalWaitMinutes > 0 ? ` · ${formatLayover(totalWaitMinutes)} waiting halt` : ''}`}
          </span>
          {route.reliability && (
            <>
              <span className="text-stone-300">•</span>
              <span className="text-[#336633] font-semibold">
                {route.reliability} on-time record
              </span>
            </>
          )}
          {route.hasBusLeg && (
            <>
              <span className="text-stone-300">•</span>
              <span className="text-[#8A6318] font-semibold flex items-center gap-1">
                <svg className="w-3.5 h-3.5 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                {isDirectBus ? 'Direct Highway Express Bus' : 'Train + connecting bus'}
              </span>
            </>
          )}
          {route.isComfortable && (
            <>
              <span className="text-stone-300">•</span>
              <span className="text-[#4A5D30]">
                Less waiting time
              </span>
            </>
          )}
        </div>

        {/* Action Buttons: Copy / Share Journey + Expand / Collapse Details */}
        <div className="flex items-center gap-1.5 ml-auto">
          <button
            type="button"
            onClick={handleShare}
            title="Copy journey details to share on WhatsApp or SMS"
            className="text-xs font-['Timeless'] text-stone-600 hover:text-[#4A5D30] font-semibold flex items-center gap-1 py-1 px-2.5 rounded-lg hover:bg-stone-200/60 transition-colors cursor-pointer active:scale-95"
          >
            {copied ? (
              <>
                <svg className="w-3.5 h-3.5 text-[#4A5D30]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-[#4A5D30]">Copied!</span>
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5 text-stone-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
                <span>Share</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={toggleExpand}
            className="text-xs font-['Timeless'] text-[#4A5D30] font-semibold flex items-center gap-1 hover:underline py-1 px-2.5 rounded-lg hover:bg-[#4A5D30]/10 transition-colors cursor-pointer"
          >
            {isExpanded ? 'Hide Details' : 'View Details'}
            <svg
              className={`w-3.5 h-3.5 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Expanded Details Section */}
      {isExpanded && (
        <div className="mt-5 pt-5 border-t border-stone-200/80 flex flex-col gap-4 text-xs font-['Timeless'] animate-fadeIn">
          {/* Unified Chronological Journey Legs (Train + Bus interleaved by departure order) */}
          {allLegs.length > 0 && (
            <div className="flex flex-col gap-3 font-['Timeless']">
              <h4 className="font-['Timeless'] text-xs font-bold tracking-wide uppercase text-stone-600">
                {allLegs.some(l => l.type === 'bus') && allLegs.some(l => l.type === 'train')
                  ? 'Journey Steps (Train + Bus)'
                  : allLegs.every(l => l.type === 'bus')
                  ? 'Bus Journey & Station Timetable'
                    : 'Train Journey & Station Timetable'}
                </h4>
                {allLegs.map((uLeg, uIdx) => {
                  // Show transfer info between consecutive legs
                  const prevLeg = uIdx > 0 ? allLegs[uIdx - 1] : null;
                  const prevAlightCode = prevLeg
                    ? (prevLeg.type === 'train' ? (prevLeg.leg as Leg).to_station : (prevLeg.leg as BusLeg).to_station_code)
                    : '';
                  const prevAlightName = prevLeg
                    ? (prevLeg.type === 'train' ? ((prevLeg.leg as Leg).to_station_name || prevAlightCode) : ((prevLeg.leg as BusLeg).to_terminal || prevAlightCode))
                    : '';
                  const transferBefore = uIdx > 0
                    ? route.transfers_info?.find(t => t.station_code === prevAlightCode) || (route.transfers_info && route.transfers_info[uIdx - 1]) || null
                    : null;

                  // Calculate actual waiting halt minutes between legs
                  let waitMins = transferBefore?.wait_time_minutes;
                  if ((waitMins === undefined || waitMins === 0) && prevLeg) {
                    const prevArr = prevLeg.type === 'train' ? (prevLeg.leg as Leg).arrival_time : (prevLeg.leg as BusLeg).arrival_time;
                    const nextDep = uLeg.type === 'train' ? (uLeg.leg as Leg).departure_time : (uLeg.leg as BusLeg).departure_time;
                    const aM = parseMinutes(prevArr);
                    const dM = parseMinutes(nextDep);
                    if (aM !== null && dM !== null) {
                      let diff = dM - aM;
                      if (diff < 0) diff += 1440;
                      waitMins = diff;
                    }
                  }

                  return (
                    <div key={`uleg-${uIdx}`}>
                      {/* Transfer info between legs */}
                      {uIdx > 0 && (
                        <div className="bg-stone-50/90 p-3.5 rounded-xl border border-stone-200 text-stone-800 font-['Timeless'] mb-3">
                          <div className="flex items-center justify-between font-semibold mb-1">
                            <span className="text-[#4A5D30]">
                              Change at {transferBefore?.station_name || prevAlightName || prevAlightCode} ({prevAlightCode})
                            </span>
                            <span className="text-stone-600 font-medium text-xs">
                              Wait time: {formatLayover(waitMins || 30)}
                            </span>
                          </div>
                          <p className="text-stone-600 text-xs leading-relaxed">
                            {transferBefore?.interchange_guide || `Transfer connection: Arrive at ${prevAlightCode}. Proceed to board connecting ${uLeg.type === 'bus' ? 'bus' : 'train'}.`}
                          </p>
                        </div>
                      )}

                      {/* Train Leg */}
                      {uLeg.type === 'train' && (() => {
                        const leg = uLeg.leg as Leg;
                        const slFare = leg.fare_estimate || 345;
                        const ac3Fare = Math.round((slFare * 3.55) / 5) * 5;
                        const legKey = getLegKey(leg);
                        const legStops = schedules[legKey] || [];
                        const isLoading = loadingSchedule[legKey];
                        const intermediateCount = Math.max(0, legStops.length - 2);

                        const stopHeaderLabel = isLoading
                          ? 'Loading timetable...'
                          : legStops.length === 0
                          ? 'Scheduled route'
                          : legStops.length === 2
                          ? 'Direct non-stop run (2 stations)'
                          : `${legStops.length} stops (${intermediateCount} intermediate ${intermediateCount === 1 ? 'stop' : 'stops'})`;

                        return (
                          <div className="bg-stone-50/90 p-4 rounded-xl border border-stone-200 font-['Timeless']">
                            <div className="flex justify-between items-start font-semibold text-stone-900 mb-2 font-['Timeless']">
                              <span className="text-[#4A5D30] font-bold text-[13px]">
                                {leg.train_number} — {leg.train_name}
                              </span>
                              <span className="text-stone-700 font-medium">
                                ₹{slFare} (SL) · ₹{ac3Fare} (3A)
                              </span>
                            </div>

                            <div className="grid grid-cols-2 gap-2 text-stone-600 mb-2">
                              <div>
                                <p className="font-semibold text-stone-900">
                                  {leg.departure_time?.slice(0, 5)} · {leg.from_station_name} ({leg.from_station})
                                </p>
                                <p className="text-[11px] text-stone-500">
                                  Boarding: Platform {(leg.departure_platform || 'PF 1').replace(/PF\s*/i, '')}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="font-semibold text-stone-900">
                                  {leg.arrival_time?.slice(0, 5)} · {leg.to_station_name} ({leg.to_station})
                                </p>
                                <p className="text-[11px] text-stone-500">
                                  Arrival: Platform {(leg.arrival_platform || 'PF 2').replace(/PF\s*/i, '')}
                                </p>
                              </div>
                            </div>

                            {/* Complete Station List with Arrival & Leave Timings */}
                            <div className="mt-3 pt-3 border-t border-stone-200">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-bold text-xs text-stone-800 uppercase tracking-wide">
                                  Station List ({stopHeaderLabel})
                                </span>
                                <span className="text-[11px] text-stone-500 font-medium">
                                  Arrival · Leave
                                </span>
                              </div>

                              {isLoading ? (
                                <div className="py-4 text-center text-stone-500 text-xs italic flex items-center justify-center gap-2">
                                  <span className="w-2 h-2 rounded-full bg-[#4A5D30] animate-ping" />
                                  <span>Fetching station timetable & timings...</span>
                                </div>
                              ) : legStops.length > 0 ? (
                                <div className="flex flex-col gap-1 max-h-[260px] overflow-y-auto pr-1">
                                  {legStops.map((st, sIdx) => {
                                    const isOrigin = sIdx === 0;
                                    const isDest = sIdx === legStops.length - 1;
                                    const isIntermediate = !isOrigin && !isDest;

                                    let haltText = '';
                                    if (isIntermediate && st.arrival && st.departure && st.arrival !== 'None' && st.departure !== 'None') {
                                      const arrM = parseMinutes(st.arrival);
                                      const depM = parseMinutes(st.departure);
                                      if (arrM !== null && depM !== null) {
                                        let diff = depM - arrM;
                                        if (diff < 0) diff += 1440;
                                        if (diff > 0 && diff <= 120) {
                                          haltText = `${diff}m halt`;
                                        }
                                      }
                                    }

                                    const arrStr = isOrigin
                                      ? 'Starts'
                                      : st.arrival && st.arrival !== 'None'
                                      ? st.arrival.slice(0, 5)
                                      : 'Passing';

                                    const depStr = isDest
                                      ? 'Terminates'
                                      : st.departure && st.departure !== 'None'
                                      ? st.departure.slice(0, 5)
                                      : 'Passing';

                                    return (
                                      <div
                                        key={`${st.station_code}_${sIdx}`}
                                        className={`flex items-center justify-between py-1.5 px-2 rounded-lg text-xs transition-colors ${
                                          isOrigin
                                            ? 'bg-blue-50/80 border border-blue-200/80 font-semibold'
                                            : isDest
                                            ? 'bg-red-50/80 border border-red-200/80 font-semibold'
                                            : 'hover:bg-stone-100/80'
                                        }`}
                                      >
                                        <div className="flex items-center gap-2 min-w-0">
                                          <span
                                            className={`w-2 h-2 rounded-full shrink-0 ${
                                              isOrigin
                                                ? 'bg-[#1A73E8]'
                                                : isDest
                                                ? 'bg-[#EA4335]'
                                                : 'bg-stone-400'
                                            }`}
                                          />
                                          <span className="truncate text-stone-900 font-medium">
                                            {st.station_name || st.station_code}
                                          </span>
                                          <span className="text-[10px] text-stone-400 font-semibold shrink-0">
                                            ({st.station_code})
                                          </span>
                                          {isOrigin && (
                                            <span className="text-[9px] bg-blue-100 text-blue-700 px-1.5 py-0.2 rounded font-bold uppercase tracking-wider shrink-0">
                                              Boarding
                                            </span>
                                          )}
                                          {isDest && (
                                            <span className="text-[9px] bg-red-100 text-red-700 px-1.5 py-0.2 rounded font-bold uppercase tracking-wider shrink-0">
                                              Alighting
                                            </span>
                                          )}
                                          {haltText && (
                                            <span className="text-[10px] text-stone-500 bg-stone-200/60 px-1.5 py-0.2 rounded shrink-0">
                                              {haltText}
                                            </span>
                                          )}
                                        </div>

                                        <div className="text-right text-[11px] font-mono shrink-0 ml-2">
                                          <span className={isOrigin ? 'text-[#1A73E8] font-bold' : 'text-stone-600'}>
                                            {arrStr}
                                          </span>
                                          <span className="text-stone-300 mx-1.5">→</span>
                                          <span className={isDest ? 'text-[#EA4335] font-bold' : 'text-stone-900 font-semibold'}>
                                            {depStr}
                                          </span>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              ) : (
                                <div className="flex flex-col gap-1 text-xs text-stone-700 py-1">
                                  <div className="flex justify-between items-center py-1.5 px-2 bg-blue-50/80 rounded-lg">
                                    <span className="font-semibold text-stone-900">{leg.from_station_name} ({leg.from_station})</span>
                                    <span className="font-mono text-stone-800">Leaves {leg.departure_time?.slice(0, 5)}</span>
                                  </div>
                                  <div className="flex justify-between items-center py-1.5 px-2 bg-red-50/80 rounded-lg">
                                    <span className="font-semibold text-stone-900">{leg.to_station_name} ({leg.to_station})</span>
                                    <span className="font-mono text-stone-800">Arrives {leg.arrival_time?.slice(0, 5)}</span>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })()}

                      {/* Bus Leg */}
                      {uLeg.type === 'bus' && (() => {
                        const b = uLeg.leg as BusLeg;
                        return (
                          <div className="bg-stone-50/90 p-4 rounded-xl border border-stone-200 font-['Timeless']">
                            <div className="flex justify-between items-start font-semibold text-stone-900 mb-2 font-['Timeless']">
                              <span className="text-[#8A6318] font-bold text-[13px] flex items-center gap-1.5">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                                </svg>
                                {b.operator_name} ({b.bus_type})
                              </span>
                              <span className="text-stone-700 font-medium">
                                ₹{b.fare} {b.is_ac ? '· AC' : '· Non-AC'} {b.rating ? `· ★ ${b.rating}` : ''}
                              </span>
                            </div>

                            <div className="grid grid-cols-2 gap-2 text-stone-600 mb-2">
                              <div>
                                <p className="font-semibold text-stone-900">
                                  {b.departure_time?.slice(0, 5)} · {b.from_terminal} ({b.from_station_code})
                                </p>
                                <p className="text-[11px] text-stone-500">
                                  Boarding: Station Bus Bay · {b.walk_to_terminal_min || 15}m transfer walk
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="font-semibold text-stone-900">
                                  {b.arrival_time?.slice(0, 5)} · {b.to_terminal} ({b.to_station_code})
                                </p>
                                <p className="text-[11px] text-stone-500">
                                  Arrival: Destination Terminal · {b.walk_from_terminal_min || 15}m walk
                                </p>
                              </div>
                            </div>

                            {/* Bus Stoppage Timetable */}
                            <div className="mt-3 pt-3 border-t border-stone-200">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-bold text-xs text-stone-800 uppercase tracking-wide">
                                  Station List (Direct Highway Route · ~{b.duration_minutes} min)
                                </span>
                                <span className="text-[11px] text-stone-500 font-medium">
                                  Arrival · Leave
                                </span>
                              </div>

                              <div className="flex flex-col gap-1 pr-1">
                                <div className="flex items-center justify-between py-1.5 px-2 rounded-lg text-xs bg-blue-50/80 border border-blue-200/80 font-semibold">
                                  <div className="flex items-center gap-2 min-w-0">
                                    <span className="w-2 h-2 rounded-full shrink-0 bg-[#1A73E8]" />
                                    <span className="truncate text-stone-900 font-medium">{b.from_terminal}</span>
                                    <span className="text-[10px] text-stone-400 font-semibold shrink-0">({b.from_station_code})</span>
                                    <span className="text-[9px] bg-blue-100 text-blue-700 px-1.5 py-0.2 rounded font-bold uppercase tracking-wider shrink-0">
                                      Boarding
                                    </span>
                                  </div>
                                  <div className="text-right text-[11px] font-mono shrink-0 ml-2">
                                    <span className="text-[#1A73E8] font-bold">Starts</span>
                                    <span className="text-stone-300 mx-1.5">→</span>
                                    <span className="text-stone-900 font-semibold">{b.departure_time?.slice(0, 5)}</span>
                                  </div>
                                </div>

                                <div className="flex items-center justify-between py-1 px-2 rounded-lg text-xs bg-stone-100/50 text-stone-600">
                                  <div className="flex items-center gap-2 min-w-0">
                                    <span className="w-2 h-2 rounded-full shrink-0 bg-amber-500" />
                                    <span className="truncate text-stone-700 italic">Expressway Non-Stop Corridor ({Math.round(b.duration_minutes / 60)}h travel time)</span>
                                  </div>
                                  <span className="text-[10px] text-stone-500 font-medium">Non-stop</span>
                                </div>

                                <div className="flex items-center justify-between py-1.5 px-2 rounded-lg text-xs bg-red-50/80 border border-red-200/80 font-semibold">
                                  <div className="flex items-center gap-2 min-w-0">
                                    <span className="w-2 h-2 rounded-full shrink-0 bg-[#EA4335]" />
                                    <span className="truncate text-stone-900 font-medium">{b.to_terminal}</span>
                                    <span className="text-[10px] text-stone-400 font-semibold shrink-0">({b.to_station_code})</span>
                                    <span className="text-[9px] bg-red-100 text-red-700 px-1.5 py-0.2 rounded font-bold uppercase tracking-wider shrink-0">
                                      Alighting
                                    </span>
                                  </div>
                                  <div className="text-right text-[11px] font-mono shrink-0 ml-2">
                                    <span className="text-[#EA4335] font-bold">{b.arrival_time?.slice(0, 5)}</span>
                                    <span className="text-stone-300 mx-1.5">→</span>
                                    <span className="text-stone-900 font-semibold">Terminates</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  );
                })}
              </div>
            )}

          {/* Helpful Journey Notes */}
          {(route.fare_arbitrage_tip || route.weather_advisory || (route.accessibility_badge && route.accessibility_badge !== 'Standard Route')) && (
            <div className="mt-2 pt-3 border-t border-stone-200/80 flex flex-col gap-3 font-['Timeless'] text-xs text-stone-700">
              {route.fare_arbitrage_tip && (
                <div>
                  <p className="font-semibold text-stone-900 mb-0.5">
                    Tip to get a confirmed seat:
                  </p>
                  <p className="text-stone-600 leading-relaxed">
                    {cleanTipText(route.fare_arbitrage_tip, route.trainNumber)}
                  </p>
                </div>
              )}

              {route.weather_advisory && (
                <div>
                  <p className="font-semibold text-stone-900 mb-0.5">
                    Weather update:
                  </p>
                  <p className="text-stone-600 leading-relaxed">
                    {cleanWeatherText(route.weather_advisory)}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
