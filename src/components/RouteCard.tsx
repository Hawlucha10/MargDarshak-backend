import { useState } from 'react';

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
  onSelect?: () => void;
}

function formatLayover(minutes: number): string {
  if (minutes < 60) return `${minutes} minutes`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h} hours`;
}

function getSimpleLabel(label?: string): string | null {
  if (!label || label === 'ALTERNATIVE') return null;
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
    case 'MULTIMODAL':
      return 'Train + bus combo';
    case 'FEWEST_TRANSFERS':
      return 'Fewest changes';
    default:
      return null;
  }
}

function cleanTipText(tip?: string, trainNumber?: string): string {
  if (!tip) return '';
  let clean = tip.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '').trim();
  clean = clean.replace(/^Upstream GNWL Quota:\s*/i, '');
  clean = clean.replace(/^Direct Origin Quota:\s*/i, '');

  // Extract components if matching upstream pattern:
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

  // If already formatted, return cleaned string
  if (/^If you want a confirmed? seat/i.test(clean)) {
    return clean;
  }

  // If direct origin starting train:
  if (/starts right (?:at|from)/i.test(clean) || /Boarding at starting terminal/i.test(clean)) {
    const trainText = trainNumber ? `this train (${trainNumber})` : 'this train';
    const stMatch = clean.match(/\(([^)]+)\)/);
    const stName = stMatch ? stMatch[1] : '';
    return `If you want a confirmed seat, ${trainText} starts right from ${stName || 'your boarding station'}, giving you the best chance of getting a confirmed ticket.`;
  }

  // General fallback:
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
  clean = clean.replace(/^Weather Condition:\s*/i, '');
  clean = clean.replace(/^Weather Advisory:\s*/i, '');
  return clean.trim();
}

export default function RouteCard({ route, index, isActive, onSelect }: RouteProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formattedIndex = String(index + 1).padStart(2, '0');

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded((prev) => !prev);
  };

  return (
    <div
      onClick={onSelect}
      className={`bg-brand-white rounded-[22px] p-6 shadow-[var(--shadow-soft)] transition-all cursor-pointer border-2 font-['Timeless'] ${
        isActive
          ? 'border-[#4A5D30] -translate-y-1 shadow-md'
          : 'border-white/80 hover:-translate-y-0.5 hover:shadow-md'
      }`}
    >
      {/* Top Bar: Editorial Index Number + Train Name + Fare & Simple Label */}
      <div className="flex justify-between items-start mb-4 font-['Timeless']">
        <div className="flex items-start gap-3.5">
          <span className="font-['Timeless'] text-3xl font-normal text-stone-400/60 select-none">
            {formattedIndex}
          </span>
          <div>
            <h3 className="font-['Timeless'] text-2xl text-[#111111] font-semibold leading-tight">
              {route.trainName}
            </h3>
            <p className="text-stone-500 font-['Timeless'] text-xs tracking-wide uppercase mt-0.5">
              {route.trainNumber}
            </p>
          </div>
        </div>

        <div className="text-right flex-shrink-0 font-['Timeless']">
          <p className="font-['Timeless'] text-2xl text-[#111111] font-bold">{route.fare}</p>
          {getSimpleLabel(route.label) && (
            <p className="text-xs text-[#4A5D30] font-semibold mt-0.5 font-['Timeless']">
              {getSimpleLabel(route.label)}
            </p>
          )}
        </div>
      </div>

      {/* Timeline: Departure → Duration → Arrival */}
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
              ? (route.hasBusLeg && (!route.legs || route.legs.length === 0) ? 'Direct bus (no changes)' : 'Direct train (no changes)')
              : `${route.transfers} ${route.transfers === 1 ? 'train change' : 'changes along the way'}`}
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
              <span className="text-[#8A6318]">
                Train + connecting bus
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

        {/* Expand / Collapse Button */}
        <button
          onClick={toggleExpand}
          className="text-xs font-['Timeless'] text-[#4A5D30] font-medium flex items-center gap-1 hover:underline ml-auto py-1 px-2 rounded-md hover:bg-[#4A5D30]/10 transition-colors cursor-pointer"
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

      {/* Expanded Details Section */}
      {isExpanded && (
        <div className="mt-5 pt-5 border-t border-stone-100 flex flex-col gap-4 text-xs font-['Timeless'] animate-fadeIn">
          {/* Detailed Train Legs */}
          {route.legs && route.legs.length > 0 && (
            <div className="flex flex-col gap-3 font-['Timeless']">
              <h4 className="font-['Timeless'] text-xs font-bold tracking-wide uppercase text-stone-500">
                Train Journey Steps
              </h4>
              {route.legs.map((leg, lIdx) => (
                <div key={lIdx} className="bg-stone-50/80 p-3.5 rounded-xl border border-stone-200/70 font-['Timeless']">
                  <div className="flex justify-between items-start font-semibold text-stone-900 mb-1.5 font-['Timeless']">
                    <span className="text-[#4A5D30] font-['Timeless']">
                      {leg.train_number} — {leg.train_name}
                    </span>
                    {leg.fare_estimate && <span>Ticket: ₹{leg.fare_estimate}</span>}
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-stone-600">
                    <div>
                      <p className="font-medium text-stone-800">
                        {leg.departure_time?.slice(0, 5)} · {leg.from_station_name} ({leg.from_station})
                      </p>
                      <p className="text-[11px] text-stone-500">
                        Boarding: Platform {(leg.departure_platform || 'PF 1').replace(/PF\s*/i, '')}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-stone-800">
                        {leg.arrival_time?.slice(0, 5)} · {leg.to_station_name} ({leg.to_station})
                      </p>
                      <p className="text-[11px] text-stone-500">
                        Arrival: Platform {(leg.arrival_platform || 'PF 2').replace(/PF\s*/i, '')}
                      </p>
                    </div>
                  </div>
                  {leg.predicted_delay_min > 0 ? (
                    <p className="mt-2 text-xs text-amber-800 font-medium">
                      Expected delay: about {leg.predicted_delay_min} minutes
                    </p>
                  ) : (
                    <p className="mt-2 text-xs text-emerald-800 font-medium">
                      Usually arrives on time
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Transfers & Platform Interchange Info */}
          {route.transfers_info && route.transfers_info.length > 0 && (
            <div className="flex flex-col gap-2">
              {route.transfers_info.map((t, tIdx) => (
                <div key={tIdx} className="bg-stone-50/80 p-3.5 rounded-xl border border-stone-200/70 text-stone-800 font-['Timeless']">
                  <div className="flex items-center justify-between font-semibold mb-1">
                    <span className="text-[#4A5D30]">Change at {t.station_name} ({t.station_code})</span>
                    <span className="text-stone-600 font-medium text-xs">
                      Wait time: {formatLayover(t.wait_time_minutes)}
                    </span>
                  </div>
                  <p className="text-stone-600 text-xs leading-relaxed">{t.interchange_guide}</p>
                  {t.bus_alternatives_count != null && t.bus_alternatives_count > 0 && (
                    <p className="mt-1 text-xs text-stone-700">
                      Note: {t.bus_alternatives_count} connecting buses are also available from nearby bus stand
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Multimodal Bus Alternative Legs */}
          {route.bus_legs && route.bus_legs.length > 0 && (
            <div className="flex flex-col gap-2 font-['Timeless']">
              <h4 className="font-['Timeless'] text-xs font-bold text-stone-500 tracking-wide uppercase">
                {route.legs && route.legs.length > 0 ? 'Connecting Bus Steps' : 'Direct Bus Journey'}
              </h4>
              {route.bus_legs.map((b, bIdx) => (
                <div key={bIdx} className="bg-stone-50/80 p-3.5 rounded-xl border border-stone-200/70 text-stone-900 font-['Timeless']">
                  <div className="flex justify-between items-start font-semibold mb-1">
                    <span>
                      {b.operator_name} ({b.bus_type})
                    </span>
                    <span className="font-bold">₹{b.fare}</span>
                  </div>
                  <p className="text-stone-600 text-xs">
                    {b.from_terminal} ({b.departure_time?.slice(0, 5)}) → {b.to_terminal} ({b.arrival_time?.slice(0, 5)})
                  </p>
                  <div className="flex items-center gap-2 text-xs text-stone-500 mt-1.5 flex-wrap">
                    <span>{b.is_ac ? 'Air conditioned bus' : 'Regular bus'}</span>
                    {b.walk_to_terminal_min && (
                      <>
                        <span className="text-stone-300">•</span>
                        <span>{b.walk_to_terminal_min} min walk from train station</span>
                      </>
                    )}
                    {b.rating && (
                      <>
                        <span className="text-stone-300">•</span>
                        <span>Rating: {b.rating} out of 5</span>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Helpful Journey Notes: Clean, normal formatting without capsules or emojis */}
          {(route.fare_arbitrage_tip || route.weather_advisory || (route.accessibility_badge && route.accessibility_badge !== 'Standard Route')) && (
            <div className="mt-2 pt-3 border-t border-stone-200/60 flex flex-col gap-3 font-['Timeless'] text-xs text-stone-700">
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

              {route.accessibility_badge && route.accessibility_badge !== 'Standard Route' && (
                <div>
                  <p className="font-semibold text-stone-900 mb-0.5">
                    Station facilities:
                  </p>
                  <p className="text-stone-600 leading-relaxed">
                    {route.accessibility_badge}
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
