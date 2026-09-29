import React from 'react';
import { X, ExternalLink, AlertTriangle, Sparkles } from 'lucide-react';
import type { TrainAvailabilityResponse, RouteAvailabilityResponse } from '../api/types';

interface AvailabilityModalProps {
  isOpen: boolean;
  onClose: () => void;
  trainData?: TrainAvailabilityResponse | null;
  routeData?: RouteAvailabilityResponse | null;
  isLoading: boolean;
  selectedTrainContext?: {
    trainNumber: string;
    trainName?: string;
    fromStation: string;
    toStation: string;
    travelDate?: string;
  } | null;
}

export const AvailabilityModal: React.FC<AvailabilityModalProps> = ({
  isOpen,
  onClose,
  trainData,
  routeData,
  isLoading,
  selectedTrainContext,
}) => {
  if (!isOpen) return null;

  const isRouteMode = !!routeData && !trainData;
  const displayTrainNumber = trainData?.train_number || selectedTrainContext?.trainNumber || '';
  const displayTrainName = trainData?.train_name || selectedTrainContext?.trainName || '';
  const displayFrom = trainData?.from_station || selectedTrainContext?.fromStation || '';
  const displayTo = trainData?.to_station || selectedTrainContext?.toStation || '';
  const displayDate = trainData?.travel_date || selectedTrainContext?.travelDate || '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
      <div className="border-2 border-[#0F172A] bg-white w-full max-w-3xl shadow-[8px_8px_0px_0px_#0F172A] p-6 relative max-h-[90vh] overflow-y-auto">
        {/* MODAL HEADER */}
        <div className="flex items-center justify-between pb-4 border-b border-[#0F172A] mb-5">
          <div>
            <span className="font-mono text-xs uppercase tracking-widest text-[#1D4ED8] font-bold">
              {isRouteMode ? '[ TIER-2 MULTI-LEG JOURNEY VERIFICATION ]' : '[ TIER-2 REAL-TIME SEAT VERIFICATION ]'}
            </span>
            <h3 className="text-xl font-black text-[#0F172A] uppercase tracking-tight">
              {isRouteMode
                ? `Journey Seat Availability (${routeData?.legs.length || 0} Legs)`
                : `Seat Availability // ${displayTrainNumber} ${displayTrainName}`.trim()}
            </h3>
            {!isRouteMode && displayFrom && displayTo && (
              <div className="text-xs font-mono text-[#64748B] mt-0.5">
                {displayFrom} ➔ {displayTo} {displayDate ? `• Date: ${displayDate}` : ''}
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 border border-[#0F172A] bg-white hover:bg-[#0F172A] hover:text-white flex items-center justify-center transition-colors cursor-pointer"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {isLoading ? (
          <div className="py-14 flex flex-col items-center justify-center space-y-4">
            <div className="w-10 h-10 border-4 border-[#1D4ED8] border-t-transparent rounded-full animate-spin"></div>
            <div className="text-center space-y-1">
              <p className="font-mono text-xs uppercase font-bold text-[#0F172A] tracking-wider">
                Connecting to Indian Railways PRS API...
              </p>
              {displayTrainNumber && (
                <p className="font-mono text-xs text-[#64748B]">
                  Querying Train {displayTrainNumber} {displayTrainName ? `(${displayTrainName})` : ''} • {displayFrom} ➔ {displayTo}
                </p>
              )}
            </div>
          </div>
        ) : isRouteMode && routeData ? (
          /* ======================================================== */
          /* MODE 2: MULTI-TRANSFER ROUTE AVAILABILITY                */
          /* ======================================================== */
          <div className="space-y-6">
            {/* ROUTE SUMMARY HEADER */}
            <div className="bg-[#F8FAFC] border border-[#CBD5E1] p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div>
                <span className="text-[#64748B] block">ROUTE STRUCTURE</span>
                <span className="font-bold text-[#0F172A]">
                  {routeData.legs.length} Legs ({routeData.legs.length - 1} Transfers)
                </span>
              </div>
              <div>
                <span className="text-[#64748B] block">CORRIDOR</span>
                <span className="font-bold text-[#0F172A]">
                  {routeData.legs[0]?.from_station} ➔ {routeData.legs[routeData.legs.length - 1]?.to_station}
                </span>
              </div>
              <div>
                <span className="text-[#64748B] block">OVERALL STATUS</span>
                <span className="font-bold text-[#D97706]">{routeData.overall_confirmation_risk}</span>
              </div>
              <div>
                <span className="text-[#64748B] block">TOTAL EST. FARE</span>
                <span className="font-bold text-[#1D4ED8]">
                  {routeData.total_fare_inr > 0 ? `₹${routeData.total_fare_inr}` : 'Check on IRCTC'}
                </span>
              </div>
            </div>

            {/* OFFICIAL IRCTC NOTICE CARD */}
            {routeData.api_status === 'unavailable' && (
              <div className="border-2 border-[#D97706] bg-[#FFFBEB] p-5 font-mono text-xs space-y-3">
                <div className="flex items-center space-x-2 text-[#B45309] font-black uppercase text-sm">
                  <AlertTriangle className="w-5 h-5 shrink-0" />
                  <span>Real-Time API Limit Reached / IRCTC Notice</span>
                </div>
                <p className="text-[#0F172A] leading-relaxed">
                  Real-time seat availability via third-party API is currently unavailable (RapidAPI monthly request quota reached or service offline).
                  To view live berth status and confirm tickets, please check directly on the official Indian Railways IRCTC website.
                </p>
                <div className="pt-2">
                  <a
                    href={routeData.irctc_url || 'https://www.irctc.co.in/nget/train-search'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-2 bg-[#0F172A] hover:bg-[#1D4ED8] text-white px-4 py-2 font-bold uppercase tracking-wider text-xs transition-colors cursor-pointer shadow-[3px_3px_0px_0px_#1D4ED8]"
                  >
                    <span>Check on Official IRCTC Website</span>
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            )}

            {/* INDIVIDUAL TRAIN LEGS BREAKDOWN */}
            <div className="space-y-4">
              <div className="text-xs font-mono font-bold uppercase tracking-wider text-[#64748B]">
                Leg-by-Leg Train Availability & Interchanges
              </div>

              {routeData.legs.map((leg, idx) => {
                const hasClasses = leg.classes && leg.classes.length > 0;

                return (
                  <div key={leg.train_number + idx} className="border border-[#0F172A] bg-white p-4 space-y-3">
                    <div className="flex flex-wrap items-center justify-between pb-2 border-b border-[#E2DFD7] gap-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-black bg-[#0F172A] text-white px-2 py-0.5">
                          LEG {idx + 1}
                        </span>
                        <span className="font-mono text-sm font-bold text-[#0F172A]">
                          Train {leg.train_number} // {leg.train_name}
                        </span>
                      </div>
                      <div className="text-xs font-mono font-bold text-[#1D4ED8]">
                        {leg.from_station} ➔ {leg.to_station}
                      </div>
                    </div>

                    {hasClasses ? (
                      /* If live classes returned for this leg */
                      <div className="overflow-x-auto">
                        <table className="w-full text-left font-mono text-xs">
                          <thead className="bg-[#F1EFE9] text-[#0F172A] uppercase text-[10px]">
                            <tr>
                              <th className="p-2">Class</th>
                              <th className="p-2">Live Status</th>
                              <th className="p-2">Fare</th>
                              <th className="p-2 text-right">Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#E2DFD7]">
                            {leg.classes.map((c) => (
                              <tr key={c.class_code}>
                                <td className="p-2 font-bold text-[#0F172A]">{c.class_code}</td>
                                <td className="p-2">
                                  <span
                                    className={`px-1.5 py-0.5 font-extrabold text-[10px] border ${
                                      c.is_available
                                        ? 'bg-[#DCFCE7] text-[#15803D] border-[#86EFAC]'
                                        : 'bg-[#FEE2E2] text-[#B91C1C] border-[#FCA5A5]'
                                    }`}
                                  >
                                    {c.status}
                                  </span>
                                </td>
                                <td className="p-2 font-bold">₹{c.fare_inr}</td>
                                <td className="p-2 text-right">
                                  <a
                                    href="https://www.irctc.co.in/nget/train-search"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="bg-[#0F172A] hover:bg-[#1D4ED8] text-white text-[10px] font-bold px-2 py-1 transition-colors inline-flex items-center gap-1 uppercase"
                                  >
                                    <span>Book</span>
                                    <ExternalLink className="w-3 h-3" />
                                  </a>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      /* When API is unavailable for this leg: show clear IRCTC official link */
                      <div className="bg-[#F8FAFC] border border-[#CBD5E1] p-3 text-xs font-mono flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <span className="text-[#64748B] block">AVAILABILITY STATUS</span>
                          <span className="font-bold text-[#D97706]">Unavailable via API</span>
                        </div>
                        <a
                          href="https://www.irctc.co.in/nget/train-search"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-[#1D4ED8] hover:bg-[#1E40AF] text-white text-xs font-bold px-3 py-1.5 transition-colors inline-flex items-center gap-1.5 uppercase cursor-pointer"
                        >
                          <span>Check on IRCTC</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* ADVISORIES */}
            {routeData.advisories && routeData.advisories.length > 0 && (
              <div className="bg-[#F1EFE9] border border-[#CBD5E1] p-3 text-xs font-mono space-y-1">
                <div className="font-bold uppercase text-[#0F172A]">Route Advisories:</div>
                <ul className="list-disc list-inside space-y-1 text-[#64748B]">
                  {routeData.advisories.map((adv, aIdx) => (
                    <li key={aIdx}>{adv}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : trainData ? (
          /* ======================================================== */
          /* MODE 1: SINGLE TRAIN DIRECT AVAILABILITY                 */
          /* ======================================================== */
          <div className="space-y-6">
            {/* TRAIN SUMMARY METRICS */}
            <div className="bg-[#F8FAFC] border border-[#CBD5E1] p-3.5 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div>
                <span className="text-[#64748B] block">TRAIN</span>
                <span className="font-bold text-[#0F172A]">{trainData.train_number} // {trainData.train_name}</span>
              </div>
              <div>
                <span className="text-[#64748B] block">CORRIDOR</span>
                <span className="font-bold text-[#0F172A]">{trainData.from_station} ➔ {trainData.to_station}</span>
              </div>
              <div>
                <span className="text-[#64748B] block">DATE</span>
                <span className="font-bold text-[#0F172A]">{trainData.travel_date}</span>
              </div>
              <div>
                <span className="text-[#64748B] block">BOOKING QUOTA</span>
                <span className="font-bold text-[#1D4ED8]">{trainData.quota} (GENERAL)</span>
              </div>
            </div>

            {/* WHEN LIVE CLASSES ARE EMPTY / API UNAVAILABLE: OFFICIAL IRCTC CARD */}
            {(!trainData.classes || trainData.classes.length === 0 || trainData.api_status === 'unavailable') ? (
              <div className="border-2 border-[#D97706] bg-[#FFFBEB] p-6 font-mono text-xs space-y-4">
                <div className="flex items-center space-x-2 text-[#B45309] font-black uppercase text-sm">
                  <AlertTriangle className="w-5 h-5 shrink-0" />
                  <span>Real-Time API Limit Reached / IRCTC Notice</span>
                </div>
                <div className="text-[#0F172A] leading-relaxed text-xs">
                  {trainData.message || 'Live seat availability via API is currently unavailable. You can check real-time availability and book directly on the official IRCTC website.'}
                </div>

                <div className="bg-white border border-[#FDE68A] p-3 rounded-none space-y-1.5 text-xs text-[#0F172A]">
                  <div className="font-bold text-[#0F172A] uppercase">IRCTC Train Query Details:</div>
                  <div className="flex flex-wrap gap-4 text-[#64748B]">
                    <span>Train: <strong className="text-[#0F172A]">{trainData.train_number} ({trainData.train_name})</strong></span>
                    <span>Route: <strong className="text-[#0F172A]">{trainData.from_station} ➔ {trainData.to_station}</strong></span>
                    <span>Date: <strong className="text-[#0F172A]">{trainData.travel_date}</strong></span>
                  </div>
                </div>

                <div className="pt-2">
                  <a
                    href={trainData.irctc_url || 'https://www.irctc.co.in/nget/train-search'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-2 bg-[#1D4ED8] hover:bg-[#1E40AF] text-white px-5 py-2.5 font-bold uppercase tracking-wider text-xs transition-colors cursor-pointer shadow-[3px_3px_0px_0px_#0F172A]"
                  >
                    <span>Check & Book on Official IRCTC Website</span>
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            ) : (
              /* WHEN CLASSES ARE AVAILABLE */
              <div>
                {/* CONFIRMTKT UPSTREAM QUOTA ARBITRAGE CARD */}
                {trainData.arbitrage_recommendation && (
                  <div className="bg-[#EFF6FF] border-2 border-[#1D4ED8] p-4 font-mono text-xs space-y-2 mb-5 shadow-[4px_4px_0px_0px_#1D4ED8]">
                    <div className="flex items-center space-x-2 text-[#1D4ED8] font-black uppercase text-xs">
                      <Sparkles className="w-4 h-4 shrink-0 text-[#1D4ED8]" />
                      <span>💡 ConfirmTkt Upstream Quota Arbitrage Found</span>
                    </div>
                    <div className="text-[#0F172A] leading-relaxed text-xs">
                      {trainData.arbitrage_recommendation.instruction}
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-[#BFDBFE] text-[11px]">
                      <div>
                        <span className="text-[#64748B] block">BOOK FROM</span>
                        <span className="font-bold text-[#0F172A]">
                          {trainData.arbitrage_recommendation.upstream_station_code} ({trainData.arbitrage_recommendation.upstream_station_name})
                        </span>
                      </div>
                      <div>
                        <span className="text-[#64748B] block">CONFIRMED BERTHS</span>
                        <span className="font-bold text-[#15803D]">
                          {trainData.arbitrage_recommendation.available_seats} Seats ({trainData.arbitrage_recommendation.quota_type})
                        </span>
                      </div>
                      <div>
                        <span className="text-[#64748B] block">UPSTREAM FARE</span>
                        <span className="font-bold text-[#0F172A]">₹{trainData.arbitrage_recommendation.ticket_fare}</span>
                      </div>
                      <div>
                        <span className="text-[#64748B] block">BOARDING POINT</span>
                        <span className="font-bold text-[#1D4ED8]">{trainData.from_station}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="text-xs font-mono font-bold uppercase tracking-wider text-[#64748B] mb-2">
                  Class-Wise Availability
                </div>
                <div className="border border-[#0F172A] overflow-hidden">
                  <table className="w-full text-left font-mono text-xs">
                    <thead className="bg-[#0F172A] text-white uppercase text-[11px]">
                      <tr>
                        <th className="p-2.5">Class</th>
                        <th className="p-2.5">Live Status</th>
                        <th className="p-2.5">Fare</th>
                        <th className="p-2.5">Confirmation Odds</th>
                        <th className="p-2.5 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E2DFD7]">
                      {trainData.classes.map((cls) => {
                        const isAvbl = cls.is_available;
                        const isRac = cls.status.includes('RAC');

                        return (
                          <tr key={cls.class_code} className="hover:bg-[#FAF9F5] transition-colors">
                            <td className="p-2.5 font-bold text-[#0F172A]">
                              {cls.class_code}
                              <span className="block text-[10px] text-[#64748B] font-normal">
                                {cls.class_name}
                              </span>
                            </td>
                            <td className="p-2.5">
                              <span
                                className={`px-2 py-0.5 font-extrabold text-[11px] border ${
                                  isAvbl
                                    ? 'bg-[#DCFCE7] text-[#15803D] border-[#86EFAC]'
                                    : isRac
                                    ? 'bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]'
                                    : 'bg-[#FEE2E2] text-[#B91C1C] border-[#FCA5A5]'
                                }`}
                              >
                                {cls.status}
                              </span>
                            </td>
                            <td className="p-2.5 font-extrabold text-[#0F172A]">
                              ₹{cls.fare_inr}
                            </td>
                            <td className="p-2.5">
                              {cls.confirmation_probability_pct ? (
                                <div>
                                  <span className="font-bold text-[#0F172A]">
                                    {cls.confirmation_probability_pct}
                                  </span>
                                </div>
                              ) : (
                                <span className="text-[#64748B]">—</span>
                              )}
                            </td>
                            <td className="p-2.5 text-right">
                              <a
                                href="https://www.irctc.co.in/nget/train-search"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="bg-[#0F172A] hover:bg-[#1D4ED8] text-white text-[11px] font-bold px-2.5 py-1 transition-colors inline-flex items-center gap-1 uppercase"
                              >
                                <span>Book</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : selectedTrainContext ? (
          <div className="space-y-6">
            <div className="bg-[#F8FAFC] border border-[#CBD5E1] p-3.5 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div>
                <span className="text-[#64748B] block">TRAIN</span>
                <span className="font-bold text-[#0F172A]">{displayTrainNumber} // {displayTrainName || 'Express'}</span>
              </div>
              <div>
                <span className="text-[#64748B] block">CORRIDOR</span>
                <span className="font-bold text-[#0F172A]">{displayFrom} ➔ {displayTo}</span>
              </div>
              <div>
                <span className="text-[#64748B] block">DATE</span>
                <span className="font-bold text-[#0F172A]">{displayDate || 'Upcoming'}</span>
              </div>
              <div>
                <span className="text-[#64748B] block">BOOKING QUOTA</span>
                <span className="font-bold text-[#1D4ED8]">GN (GENERAL)</span>
              </div>
            </div>

            <div className="border-2 border-[#D97706] bg-[#FFFBEB] p-6 font-mono text-xs space-y-4">
              <div className="flex items-center space-x-2 text-[#B45309] font-black uppercase text-sm">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <span>Real-Time API Limit Reached / IRCTC Notice</span>
              </div>
              <div className="text-[#0F172A] leading-relaxed text-xs">
                Real-time seat availability via third-party API is currently unavailable (RapidAPI monthly request quota reached or service offline).
                To view live berth status and book tickets, please check directly on the official Indian Railways IRCTC website.
              </div>

              <div className="bg-white border border-[#FDE68A] p-3 rounded-none space-y-1.5 text-xs text-[#0F172A]">
                <div className="font-bold text-[#0F172A] uppercase">IRCTC Train Query Details:</div>
                <div className="flex flex-wrap gap-4 text-[#64748B]">
                  <span>Train: <strong className="text-[#0F172A]">{displayTrainNumber} ({displayTrainName || 'Express'})</strong></span>
                  <span>Route: <strong className="text-[#0F172A]">{displayFrom} ➔ {displayTo}</strong></span>
                  {displayDate && <span>Date: <strong className="text-[#0F172A]">{displayDate}</strong></span>}
                </div>
              </div>

              <div className="pt-2">
                <a
                  href="https://www.irctc.co.in/nget/train-search"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 bg-[#1D4ED8] hover:bg-[#1E40AF] text-white px-5 py-2.5 font-bold uppercase tracking-wider text-xs transition-colors cursor-pointer shadow-[3px_3px_0px_0px_#0F172A]"
                >
                  <span>Check & Book on Official IRCTC Website</span>
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>
        ) : (
          <div className="py-8 text-center font-mono text-xs text-[#64748B]">
            No live availability data retrieved.
          </div>
        )}

        {/* MODAL FOOTER */}
        <div className="mt-6 pt-4 border-t border-[#E2DFD7] flex items-center justify-between">
          <a
            href="https://www.irctc.co.in/nget/train-search"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-mono text-[#1D4ED8] hover:underline flex items-center gap-1 font-bold"
          >
            <span>Visit IRCTC eTicketing Portal</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          <button
            onClick={onClose}
            className="bg-[#E2DFD7] hover:bg-[#CBD5E1] text-[#0F172A] font-mono text-xs font-bold uppercase px-4 py-2 cursor-pointer transition-colors"
          >
            Close Panel
          </button>
        </div>
      </div>
    </div>
  );
};
