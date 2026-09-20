import React from 'react';
import { X, Train, CheckCircle, Circle } from 'lucide-react';
import type { TrainLiveStatus } from '../api/types';

interface LiveTrainModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: TrainLiveStatus | null;
  isLoading: boolean;
}

export const LiveTrainModal: React.FC<LiveTrainModalProps> = ({
  isOpen,
  onClose,
  data,
  isLoading,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
      <div className="border-2 border-[#0F172A] bg-white w-full max-w-2xl shadow-[8px_8px_0px_0px_#0F172A] p-6 relative max-h-[90vh] overflow-y-auto">
        {/* HEADER */}
        <div className="flex items-center justify-between pb-4 border-b border-[#0F172A] mb-5">
          <div>
            <span className="font-mono text-xs uppercase tracking-widest text-[#15803D] font-bold">
              [ REAL-TIME GPS & ML DELAY TELEMETRY ]
            </span>
            <h3 className="text-xl font-black text-[#0F172A] uppercase tracking-tight flex items-center gap-2">
              <Train className="w-5 h-5 text-[#1D4ED8]" />
              <span>Live Running Status</span>
            </h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 border border-[#0F172A] bg-white hover:bg-[#0F172A] hover:text-white flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {isLoading ? (
          <div className="py-12 flex flex-col items-center justify-center space-y-3">
            <div className="w-8 h-8 border-4 border-[#1D4ED8] border-t-transparent rounded-full animate-spin"></div>
            <p className="font-mono text-xs uppercase font-bold text-[#64748B]">
              Synchronizing Live Train Telemetry & GPS Tracking...
            </p>
          </div>
        ) : data ? (
          <div className="space-y-6">
            {/* TRAIN HERO STATS */}
            <div className="border border-[#0F172A] bg-[#0F172A] text-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#334155] pb-3 mb-3 font-mono">
                <div>
                  <span className="text-xs text-[#94A3B8]">TRAIN NUMBER & NAME</span>
                  <div className="text-lg font-bold">{data.train_number} // {data.train_name}</div>
                </div>
                <div className="text-right">
                  <span className="text-xs text-[#94A3B8]">OPERATIONAL DELAY</span>
                  <div className="text-lg font-bold text-[#F59E0B]">
                    +{data.delay_minutes} min ({data.delay_status})
                  </div>
                </div>
              </div>

              {/* Grid Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                <div>
                  <span className="text-[#94A3B8] block">CURRENT POSITION</span>
                  <span className="font-bold text-white">{data.current_station} ({data.current_station_name})</span>
                </div>
                <div>
                  <span className="text-[#94A3B8] block">NEXT STOP & ETA</span>
                  <span className="font-bold text-[#38BDF8]">{data.next_stop} ({data.next_stop_name}) @ {data.eta}</span>
                </div>
                <div>
                  <span className="text-[#94A3B8] block">PROGRESS</span>
                  <span className="font-bold text-white">{data.journey_percent}% Completed</span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-1.5 bg-[#334155] mt-3 overflow-hidden">
                <div
                  className="h-full bg-[#1D4ED8] transition-all"
                  style={{ width: `${data.journey_percent}%` }}
                ></div>
              </div>
            </div>

            {/* STATION TIMELINE */}
            <div>
              <div className="text-xs font-mono font-bold uppercase tracking-wider text-[#64748B] mb-2">
                Station Timeline & Platform Tracker
              </div>
              <div className="border border-[#CBD5E1] bg-[#F8FAFC] p-3 max-h-64 overflow-y-auto font-mono text-xs divide-y divide-[#E2DFD7]">
                {data.station_timeline.map((stop, sIdx) => {
                  const hasPassed = stop.has_passed;

                  return (
                    <div
                      key={stop.station_code + sIdx}
                      className={`py-2 px-2 flex items-center justify-between ${
                        hasPassed ? 'text-[#64748B]' : 'text-[#0F172A] font-bold bg-white'
                      }`}
                    >
                      <div className="flex items-center space-x-2.5">
                        {hasPassed ? (
                          <CheckCircle className="w-3.5 h-3.5 text-[#15803D] shrink-0" />
                        ) : (
                          <Circle className="w-3.5 h-3.5 text-[#1D4ED8] shrink-0" />
                        )}
                        <div>
                          <span className="font-bold">{stop.station_name} ({stop.station_code})</span>
                          {stop.distance_km !== undefined && (
                            <span className="ml-2 text-[10px] text-[#94A3B8]">
                              {stop.distance_km} km
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="text-right">
                        <span className="font-mono">
                          {stop.actual_departure || stop.departure || stop.actual_arrival || stop.arrival || '--:--'}
                        </span>
                        {stop.delay_minutes > 0 && hasPassed && (
                          <span className="ml-2 text-[10px] text-[#D97706] font-bold">
                            +{stop.delay_minutes}m
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="py-8 text-center font-mono text-xs text-[#64748B]">
            No live telemetry received.
          </div>
        )}

        {/* FOOTER */}
        <div className="mt-6 pt-4 border-t border-[#E2DFD7] flex justify-end">
          <button
            onClick={onClose}
            className="bg-[#E2DFD7] hover:bg-[#CBD5E1] text-[#0F172A] font-mono text-xs font-bold uppercase px-4 py-2 cursor-pointer transition-colors"
          >
            Close Telemetry
          </button>
        </div>
      </div>
    </div>
  );
};
