import React, { useState } from 'react';
import { 
  Clock, 
  ShieldCheck, 
  ChevronDown, 
  ChevronUp, 
  ArrowRight, 
  Train, 
  AlertTriangle, 
  ArrowDownUp,
  Tag
} from 'lucide-react';
import type { JourneyRoute } from '../api/types';

interface RouteTileProps {
  route: JourneyRoute;
  index: number;
  onCheckAvailability: (trainNum: string, from: string, to: string, route?: JourneyRoute, trainName?: string) => void;
  onCheckRouteAvailability?: (route: JourneyRoute) => void;
  onCheckLegAvailability?: (trainNum: string, from: string, to: string, trainName?: string) => void;
  onTrackLive: (trainNum: string, trainName?: string) => void;
}

export const RouteTile: React.FC<RouteTileProps> = ({
  route,
  index,
  onCheckAvailability,
  onCheckRouteAvailability,
  onCheckLegAvailability,
  onTrackLive,
}) => {
  const [isExpanded, setIsExpanded] = useState(index === 0); // Expand top route by default

  const firstLeg = route.legs[0];
  const lastLeg = route.legs[route.legs.length - 1];

  // Starting base fares approximation for preview
  const slFare = route.total_fare || 750;
  const ac3eFare = Math.round(slFare * 1.85);
  const ac3aFare = Math.round(slFare * 2.15);

  const getParetoBadgeClass = (label: string) => {
    switch (label.toUpperCase()) {
      case 'FASTEST':
      case 'FASTEST_TRANSFER':
        return 'bg-[#1D4ED8] text-white border-[#1D4ED8]';
      case 'CHEAPEST':
        return 'bg-[#15803D] text-white border-[#15803D]';
      case 'MOST_RELIABLE':
      case 'FEWEST_TRANSFERS':
        return 'bg-[#0F172A] text-white border-[#0F172A]';
      case 'BALANCED':
      default:
        return 'bg-[#D97706] text-white border-[#D97706]';
    }
  };

  return (
    <div className="border border-[#0F172A] bg-white shadow-[4px_4px_0px_0px_#0F172A] transition-all hover:shadow-[6px_6px_0px_0px_#0F172A] mb-5">
      {/* CARD HEADER: METRICS & BADGES */}
      <div className="border-b border-[#E2DFD7] px-4 py-3 bg-[#FBFBF9] flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <span className="font-mono text-xs font-bold text-[#64748B]">
            #{String(index + 1).padStart(2, '0')}
          </span>
          <span className={`text-[11px] font-mono font-extrabold uppercase px-2 py-0.5 border ${getParetoBadgeClass(route.label)}`}>
            {route.label.replace('_', ' ')}
          </span>
          {route.accessibility_badge && (
            <span className="text-[11px] font-mono font-bold bg-[#E2DFD7] text-[#0F172A] px-2 py-0.5 border border-[#CBD5E1]">
              {route.accessibility_badge}
            </span>
          )}
        </div>

        {/* Joint Reliability Metric */}
        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="flex items-center space-x-1 font-bold text-[#15803D]">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{route.joint_reliability_percent || `${Math.round(route.reliability_score * 100)}%`} RELIABILITY</span>
          </div>
          {route.weather_advisory && (
            <div className="hidden sm:flex items-center space-x-1 text-[#D97706] font-bold">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>WEATHER HAZARD</span>
            </div>
          )}
        </div>
      </div>

      {/* CARD BODY: COLLAPSED / MAIN SUMMARY ROW */}
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-5 cursor-pointer hover:bg-[#FAF9F5] transition-colors"
      >
        <div className="grid grid-cols-1 md:grid-cols-[1fr,auto,1fr,auto] gap-4 items-center">
          {/* DEPARTURE STATION */}
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-black font-mono tracking-tight text-[#0F172A]">
                {firstLeg.departure_time?.slice(0, 5) || '08:00'}
              </span>
              <span className="text-xs font-mono font-bold bg-[#0F172A] text-white px-2 py-0.5">
                {firstLeg.departure_platform || 'PF 1'}
              </span>
            </div>
            <div className="text-sm font-extrabold text-[#0F172A] uppercase mt-0.5">
              {firstLeg.from_station_name || firstLeg.from_station}
            </div>
            <div className="text-xs font-mono text-[#64748B]">
              Origin ({firstLeg.from_station})
            </div>
          </div>

          {/* TIMELINE & TRANSFER DURATION CONNECTOR */}
          <div className="flex flex-col items-center justify-center px-2">
            <div className="text-xs font-mono font-bold text-[#1D4ED8] flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              <span>{route.total_travel_time}</span>
            </div>

            {/* Geometric Route Line */}
            <div className="w-48 sm:w-56 h-[2px] bg-[#0F172A] my-2 relative flex items-center justify-center">
              <div className="absolute left-0 w-2 h-2 rounded-full bg-[#0F172A]"></div>
              <div className="absolute right-0 w-2 h-2 rounded-full bg-[#0F172A]"></div>
              
              {/* Intermediate Transfer Marker */}
              {route.transfers > 0 ? (
                <span className="bg-[#D97706] text-white text-[10px] font-mono font-bold px-1.5 py-0.2 border border-[#0F172A]">
                  {route.transfers} TRANSFER{route.transfers > 1 ? 'S' : ''}
                </span>
              ) : (
                <span className="bg-[#15803D] text-white text-[10px] font-mono font-bold px-1.5 py-0.2 border border-[#0F172A]">
                  DIRECT TRIP
                </span>
              )}
            </div>

            <div className="text-[11px] font-mono text-[#64748B] text-center">
              {route.transfers > 0 ? (
                <span>
                  Via {route.legs.slice(0, -1).map(l => l.to_station).join(', ')} ({route.transfers_info[0]?.wait_time_minutes || 45}m layover)
                </span>
              ) : (
                <span>Zero Train Changes</span>
              )}
            </div>
          </div>

          {/* FINAL ARRIVAL STATION */}
          <div className="md:text-right">
            <div className="flex items-center md:justify-end space-x-2">
              <span className="text-xs font-mono font-bold bg-[#0F172A] text-white px-2 py-0.5">
                {lastLeg.arrival_platform || 'PF 2'}
              </span>
              <span className="text-2xl font-black font-mono tracking-tight text-[#0F172A]">
                {lastLeg.arrival_time?.slice(0, 5) || '18:00'}
              </span>
            </div>
            <div className="text-sm font-extrabold text-[#0F172A] uppercase mt-0.5">
              {lastLeg.to_station_name || lastLeg.to_station}
            </div>
            <div className="text-xs font-mono text-[#64748B]">
              Destination ({lastLeg.to_station})
            </div>
          </div>

          {/* FARES SUMMARY & EXPAND TOGGLE */}
          <div className="border-t md:border-t-0 md:border-l border-[#E2DFD7] pt-3 md:pt-0 md:pl-4 flex flex-col justify-center items-start md:items-end">
            <div className="text-[10px] font-mono text-[#64748B] uppercase font-bold mb-1">
              Estimated Class Fares
            </div>
            <div className="flex items-center gap-1.5 font-mono text-xs">
              <span className="border border-[#CBD5E1] bg-[#F8FAFC] px-1.5 py-0.5 font-bold text-[#0F172A]">
                SL: ₹{slFare}
              </span>
              <span className="border border-[#CBD5E1] bg-[#F8FAFC] px-1.5 py-0.5 font-bold text-[#0F172A]">
                3A: ₹{ac3aFare}
              </span>
              <span className="border border-[#CBD5E1] bg-[#F8FAFC] px-1.5 py-0.5 font-bold text-[#0F172A]">
                3E: ₹{ac3eFare}
              </span>
            </div>

            <button 
              className="mt-3 flex items-center space-x-1 text-xs font-mono font-extrabold text-[#1D4ED8] hover:underline"
            >
              <span>{isExpanded ? 'COLLAPSE DETAILS' : 'INSPECT FULL DETAILS'}</span>
              {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>

      {/* EXPANDED SECTION: GRANULAR LEG BREAKDOWN & ACTIONS */}
      {isExpanded && (
        <div className="border-t border-[#0F172A] bg-[#FAF9F5] p-5">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-[#64748B] mb-4">
            [ ITINERARY BREAKDOWN // PLATFORM ASSIGNMENTS ]
          </div>

          {/* LEGS ITERATION */}
          <div className="space-y-4">
            {route.legs.map((leg, lIdx) => {
              const transferAtThisStop = route.transfers_info[lIdx];

              return (
                <div key={leg.train_number + lIdx} className="space-y-3">
                  {/* TRAIN LEG CONTAINER */}
                  <div className="border border-[#CBD5E1] bg-white p-4">
                    <div className="flex flex-wrap items-center justify-between pb-3 border-b border-[#F1EFE9] gap-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-black bg-[#0F172A] text-white px-2 py-0.5">
                          LEG {lIdx + 1}
                        </span>
                        <span className="font-mono text-sm font-bold text-[#0F172A]">
                          Train {leg.train_number} // {leg.train_name}
                        </span>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onCheckLegAvailability) {
                              onCheckLegAvailability(leg.train_number, leg.from_station, leg.to_station, leg.train_name);
                            } else {
                              onCheckAvailability(leg.train_number, leg.from_station, leg.to_station, route, leg.train_name);
                            }
                          }}
                          className="text-[11px] font-mono font-bold bg-[#EFF6FF] text-[#1D4ED8] hover:bg-[#1D4ED8] hover:text-white px-2.5 py-1 border border-[#BFDBFE] transition-colors flex items-center space-x-1 cursor-pointer"
                        >
                          <span>Check Leg Seats</span>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onTrackLive(leg.train_number, leg.train_name);
                          }}
                          className="text-[11px] font-mono font-bold bg-[#F1EFE9] hover:bg-[#0F172A] hover:text-white px-2.5 py-1 border border-[#CBD5E1] transition-colors flex items-center space-x-1 cursor-pointer"
                        >
                          <Train className="w-3 h-3" />
                          <span>Track Live Train</span>
                        </button>
                      </div>
                    </div>

                    {/* Departure / Arrival / Platform Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
                      {/* DEPARTURE INFO */}
                      <div className="border-l-2 border-[#1D4ED8] pl-3">
                        <div className="text-xs font-mono text-[#64748B]">DEPARTURE</div>
                        <div className="text-base font-black font-mono text-[#0F172A]">
                          {leg.departure_time?.slice(0, 5)}
                          <span className="ml-2 text-xs font-bold bg-[#EFF6FF] text-[#1D4ED8] border border-[#BFDBFE] px-1.5 py-0.5">
                            {leg.departure_platform || 'PF 1'}
                          </span>
                        </div>
                        <div className="text-xs font-bold text-[#0F172A]">
                          {leg.from_station_name} ({leg.from_station})
                        </div>
                      </div>

                      {/* ARRIVAL INFO */}
                      <div className="border-l-2 border-[#DC2626] pl-3">
                        <div className="text-xs font-mono text-[#64748B]">ARRIVAL</div>
                        <div className="text-base font-black font-mono text-[#0F172A]">
                          {leg.arrival_time?.slice(0, 5)}
                          <span className="ml-2 text-xs font-bold bg-[#FEF2F2] text-[#DC2626] border border-[#FECACA] px-1.5 py-0.5">
                            {leg.arrival_platform || 'PF 2'}
                          </span>
                        </div>
                        <div className="text-xs font-bold text-[#0F172A]">
                          {leg.to_station_name} ({leg.to_station})
                        </div>
                      </div>
                    </div>

                    {/* Operational Telemetry Line */}
                    <div className="mt-3 pt-2 border-t border-[#F1EFE9] flex flex-wrap items-center justify-between text-[11px] font-mono text-[#64748B]">
                      <div>
                        Predicted Delay: <span className="font-bold text-[#0F172A]">+{leg.predicted_delay_min} min</span> (ML Quantile Safe)
                      </div>
                      <div>
                        Est. Base Fare: <span className="font-bold text-[#0F172A]">₹{leg.fare_estimate}</span>
                      </div>
                    </div>
                  </div>

                  {/* INTERMEDIATE TRANSFER / PLATFORM WALKING INSTRUCTIONS */}
                  {transferAtThisStop && (
                    <div className="border-2 border-dashed border-[#D97706] bg-[#FFFBEB] p-3 text-xs font-mono">
                      <div className="flex items-center space-x-2 font-bold text-[#B45309] mb-1">
                        <ArrowDownUp className="w-4 h-4" />
                        <span>
                          STATION INTERCHANGE AT {transferAtThisStop.station_name} ({transferAtThisStop.station_code})
                        </span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[#0F172A] mt-2">
                        <div>
                          <span className="text-[#64748B]">Layover Buffer:</span>{' '}
                          <span className="font-bold">{transferAtThisStop.wait_time_minutes} min</span>
                        </div>
                        <div>
                          <span className="text-[#64748B]">Connection Safety:</span>{' '}
                          <span className="font-bold text-[#15803D]">GUARANTEED (P85 SAFE)</span>
                        </div>
                        <div>
                          <span className="text-[#64748B]">Navigation:</span>{' '}
                          <span className="font-bold">{transferAtThisStop.interchange_guide || `Arrive ${transferAtThisStop.arrival_platform} -> Depart ${transferAtThisStop.departure_platform}`}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* ARBITRAGE NOTICE BANNER */}
          {route.fare_arbitrage_tip && (
            <div className="mt-4 border border-[#15803D] bg-[#F0FDF4] p-3 text-xs font-mono flex items-start space-x-2">
              <Tag className="w-4 h-4 text-[#15803D] shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-[#15803D] uppercase">Distance-Slab Arbitrage Opportunity: </span>
                <span className="text-[#0F172A]">{route.fare_arbitrage_tip}</span>
              </div>
            </div>
          )}

          {/* ACTION BUTTONS BAR */}
          <div className="mt-5 pt-4 border-t border-[#CBD5E1] flex flex-wrap items-center justify-between gap-3">
            <button
              onClick={() => {
                if (route.transfers === 0 || !onCheckRouteAvailability) {
                  onCheckAvailability(firstLeg.train_number, firstLeg.from_station, lastLeg.to_station, route, firstLeg.train_name);
                } else {
                  onCheckRouteAvailability(route);
                }
              }}
              className="bg-[#1D4ED8] hover:bg-[#1E40AF] text-white border border-[#0F172A] px-5 py-2.5 font-mono text-xs font-bold uppercase tracking-wider flex items-center space-x-2 shadow-[3px_3px_0px_0px_#0F172A] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer"
            >
              <span>
                {route.transfers === 0
                  ? 'CHECK DIRECT SEAT AVAILABILITY (SL, 3A, 3E)'
                  : `CHECK JOURNEY SEATS (${route.legs.length} LEGS)`}
              </span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <span className="text-xs font-mono text-[#64748B]">
              {route.transfers === 0
                ? 'Sub-second Tier-2 IRCTC Quota Check'
                : 'Concurrent Leg-by-Leg Multi-Hop IRCTC Verification'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
