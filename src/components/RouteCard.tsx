import { useState } from 'react';
import BusLegBadge from './BusLegBadge';
import ComfortBadge from './ComfortBadge';

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

const LABEL_STYLES: Record<string, string> = {
  FASTEST: 'bg-brand-blue/15 text-brand-blue border-brand-blue/30',
  CHEAPEST: 'bg-[#5A6B3C]/15 text-[#5A6B3C] border-[#5A6B3C]/30',
  BALANCED: 'bg-brand-periwinkle/60 text-brand-text-blue border-brand-blue/20',
  MOST_RELIABLE: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  COMFORT_HOMESTAY: 'bg-[#5A6B3C]/15 text-[#5A6B3C] border-[#5A6B3C]/30',
  MULTIMODAL_FASTEST: 'bg-[#D4A843]/15 text-[#B88728] border-[#D4A843]/30',
  ALTERNATIVE: 'bg-brand-cream text-brand-text-muted border-stone-200',
};

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
      className={`bg-brand-white rounded-[22px] p-6 shadow-[var(--shadow-soft)] transition-all cursor-pointer border-2 ${
        isActive
          ? 'border-brand-blue -translate-y-1 shadow-md'
          : 'border-white/80 hover:-translate-y-0.5 hover:shadow-md'
      }`}
    >
      {/* Top Bar: Editorial Index Number + Train Name + Fare & Pareto Label */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-start gap-3.5">
          <span className="font-serif text-3xl font-normal text-brand-text-muted/40 select-none">
            {formattedIndex}
          </span>
          <div>
            <h3 className="font-serif text-2xl text-brand-text font-semibold leading-tight">
              {route.trainName}
            </h3>
            <p className="text-brand-text-muted font-ui text-xs tracking-wide uppercase mt-0.5">
              {route.trainNumber}
            </p>
          </div>
        </div>

        <div className="text-right flex-shrink-0">
          <p className="font-serif text-2xl text-brand-text font-bold">{route.fare}</p>
          {route.label && (
            <span
              className={`inline-block text-[11px] px-2.5 py-0.5 rounded-md mt-1 font-ui font-semibold border ${
                LABEL_STYLES[route.label] || LABEL_STYLES.ALTERNATIVE
              }`}
            >
              {route.label.replace(/_/g, ' ')}
            </span>
          )}
        </div>
      </div>

      {/* Timeline: Departure → Duration → Arrival */}
      <div className="flex items-center justify-between font-ui text-sm mb-4 bg-brand-cream/40 px-4 py-3 rounded-xl border border-stone-100">
        <div className="text-left">
          <p className="font-bold text-brand-text text-base">{route.departure}</p>
          <span className="text-[11px] text-brand-text-muted">Departure</span>
        </div>
        <div className="flex-1 px-4 flex flex-col items-center">
          <span className="text-brand-text-blue font-ui text-xs font-semibold mb-1">
            {route.duration}
          </span>
          <div className="w-full flex items-center">
            <div className="w-2.5 h-2.5 rounded-xs bg-[#5A6B3C]" />
            <div className="h-0.5 bg-brand-text-muted/30 flex-1 mx-1" />
            <div className="w-2.5 h-2.5 rounded-xs bg-brand-blue" />
          </div>
        </div>
        <div className="text-right">
          <p className="font-bold text-brand-text text-base">{route.arrival}</p>
          <span className="text-[11px] text-brand-text-muted">Arrival</span>
        </div>
      </div>

      {/* Badges & Transfer Meta */}
      <div className="flex items-center justify-between gap-2 flex-wrap pt-1">
        <div className="flex items-center gap-2 flex-wrap">
          {route.hasBusLeg && <BusLegBadge />}
          {route.isComfortable && <ComfortBadge />}
          {route.transfers !== undefined && (
            <span className="text-xs font-ui bg-stone-100 text-stone-700 px-2.5 py-1 rounded-md border border-stone-200/60 font-medium">
              {route.transfers === 0 ? 'Direct Train' : `${route.transfers} Transfer`}
            </span>
          )}
          {route.reliability && (
            <span className="text-xs font-ui text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200/70 font-semibold">
              Reliability: {route.reliability}
            </span>
          )}
        </div>

        {/* Expand / Collapse Button */}
        <button
          onClick={toggleExpand}
          className="text-xs font-ui text-brand-blue font-medium flex items-center gap-1 hover:underline ml-auto py-1 px-2 rounded-md hover:bg-brand-blue/5 transition-colors"
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
        <div className="mt-5 pt-5 border-t border-stone-100 flex flex-col gap-4 text-xs font-ui animate-fadeIn">
          {/* Detailed Train Legs */}
          {route.legs && route.legs.length > 0 && (
            <div className="flex flex-col gap-3">
              <h4 className="font-serif text-sm font-bold text-brand-text tracking-wide uppercase text-stone-500">
                Train Journey Sequence
              </h4>
              {route.legs.map((leg, lIdx) => (
                <div key={lIdx} className="bg-stone-50/80 p-3.5 rounded-xl border border-stone-200/70">
                  <div className="flex justify-between items-start font-semibold text-brand-text mb-1.5">
                    <span className="text-brand-blue">
                      {leg.train_number} — {leg.train_name}
                    </span>
                    {leg.fare_estimate && <span>Est. ₹{leg.fare_estimate}</span>}
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-stone-600">
                    <div>
                      <p className="font-medium text-stone-800">
                        {leg.departure_time?.slice(0, 5)} · {leg.from_station_name} ({leg.from_station})
                      </p>
                      <p className="text-[11px] text-stone-500">
                        Boarding Platform: {leg.departure_platform || 'PF 1'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-stone-800">
                        {leg.arrival_time?.slice(0, 5)} · {leg.to_station_name} ({leg.to_station})
                      </p>
                      <p className="text-[11px] text-stone-500">
                        Arrival Platform: {leg.arrival_platform || 'PF 2'}
                      </p>
                    </div>
                  </div>
                  {leg.predicted_delay_min > 0 && (
                    <div className="mt-2 text-[11px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded inline-block">
                      Predicted Delay: +{leg.predicted_delay_min}m (P85 safety buffer included)
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Transfers & Platform Interchange Info */}
          {route.transfers_info && route.transfers_info.length > 0 && (
            <div className="flex flex-col gap-2">
              {route.transfers_info.map((t, tIdx) => (
                <div key={tIdx} className="bg-blue-50/70 p-3 rounded-xl border border-blue-100 text-blue-900">
                  <div className="flex items-center justify-between font-semibold mb-1">
                    <span>Transfer at {t.station_name} ({t.station_code})</span>
                    <span className="bg-blue-100 text-blue-800 border border-blue-200/60 px-2 py-0.5 rounded-md text-[11px]">
                      {t.wait_time_minutes} min layover
                    </span>
                  </div>
                  <p className="text-blue-800 text-[11px]">{t.interchange_guide}</p>
                  {t.bus_alternatives_count != null && t.bus_alternatives_count > 0 && (
                    <p className="mt-1 text-[11px] text-amber-800 font-semibold flex items-center gap-1">
                      🚌 {t.bus_alternatives_count} Connecting Buses Available from nearby terminal
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Multimodal Bus Alternative Legs */}
          {route.bus_legs && route.bus_legs.length > 0 && (
            <div className="flex flex-col gap-2">
              <h4 className="font-serif text-sm font-bold text-amber-800 tracking-wide uppercase">
                Connecting Bus Alternative
              </h4>
              {route.bus_legs.map((b, bIdx) => (
                <div key={bIdx} className="bg-amber-50/80 p-3.5 rounded-xl border border-amber-200 text-amber-950">
                  <div className="flex justify-between items-start font-semibold mb-1">
                    <span>
                      {b.operator_name} ({b.bus_type})
                    </span>
                    <span className="font-bold">₹{b.fare}</span>
                  </div>
                  <p className="text-amber-900">
                    {b.from_terminal} ({b.departure_time?.slice(0, 5)}) → {b.to_terminal} ({b.arrival_time?.slice(0, 5)})
                  </p>
                  <div className="flex gap-2 mt-2">
                    {b.is_ac && (
                      <span className="bg-amber-200/80 text-amber-900 px-2 py-0.5 rounded text-[10px] font-semibold">
                        A/C Electric/Volvo
                      </span>
                    )}
                    {b.walk_to_terminal_min && (
                      <span className="text-[10px] text-amber-800">
                        {b.walk_to_terminal_min} min walk from rail station
                      </span>
                    )}
                    {b.rating && (
                      <span className="text-[10px] text-amber-800 font-medium">★ {b.rating}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Upstream Quota Seat Arbitrage Tip */}
          {route.fare_arbitrage_tip && (
            <div className="bg-emerald-50/90 text-emerald-900 p-3 rounded-xl border border-emerald-200">
              <p className="font-semibold text-emerald-800 flex items-center gap-1.5 mb-0.5">
                <span>💡</span> Upstream Seat Quota Arbitrage
              </p>
              <p className="text-emerald-800 text-[11px] leading-relaxed">
                {route.fare_arbitrage_tip}
              </p>
            </div>
          )}

          {/* Weather Advisory */}
          {route.weather_advisory && (
            <div className="bg-amber-50 text-amber-900 p-3 rounded-xl border border-amber-200 text-[11px]">
              <span className="font-semibold">⛅ Weather Condition:</span> {route.weather_advisory}
            </div>
          )}

          {/* Accessibility Information */}
          {route.accessibility_badge && (
            <div className="bg-purple-50 text-purple-900 p-2.5 rounded-xl border border-purple-200 text-[11px] flex items-center gap-1.5">
              <span>♿</span>
              <span className="font-medium">{route.accessibility_badge}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
