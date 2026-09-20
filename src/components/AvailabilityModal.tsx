import React from 'react';
import { X, Tag } from 'lucide-react';
import type { TrainAvailabilityResponse } from '../api/types';

interface AvailabilityModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: TrainAvailabilityResponse | null;
  isLoading: boolean;
}

export const AvailabilityModal: React.FC<AvailabilityModalProps> = ({
  isOpen,
  onClose,
  data,
  isLoading,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
      <div className="border-2 border-[#0F172A] bg-white w-full max-w-2xl shadow-[8px_8px_0px_0px_#0F172A] p-6 relative max-h-[90vh] overflow-y-auto">
        {/* MODAL HEADER */}
        <div className="flex items-center justify-between pb-4 border-b border-[#0F172A] mb-5">
          <div>
            <span className="font-mono text-xs uppercase tracking-widest text-[#1D4ED8] font-bold">
              [ TIER-2 REAL-TIME VERIFICATION ]
            </span>
            <h3 className="text-xl font-black text-[#0F172A] uppercase tracking-tight">
              Seat Availability & Quota Arbitrage
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
              Polling IRCTC Quota Berths & Computing Bayesian Odds...
            </p>
          </div>
        ) : data ? (
          <div className="space-y-6">
            {/* TRAIN SUMMARY METRICS */}
            <div className="bg-[#F8FAFC] border border-[#CBD5E1] p-3.5 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div>
                <span className="text-[#64748B] block">TRAIN</span>
                <span className="font-bold text-[#0F172A]">{data.train_number} // {data.train_name}</span>
              </div>
              <div>
                <span className="text-[#64748B] block">CORRIDOR</span>
                <span className="font-bold text-[#0F172A]">{data.from_station} ➔ {data.to_station}</span>
              </div>
              <div>
                <span className="text-[#64748B] block">DATE</span>
                <span className="font-bold text-[#0F172A]">{data.travel_date}</span>
              </div>
              <div>
                <span className="text-[#64748B] block">BOOKING QUOTA</span>
                <span className="font-bold text-[#1D4ED8]">{data.quota} (GENERAL)</span>
              </div>
            </div>

            {/* CLASS BREAKDOWN TABLE */}
            <div>
              <div className="text-xs font-mono font-bold uppercase tracking-wider text-[#64748B] mb-2">
                Class-Wise Availability & Bayesian Confirmation Probability
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
                    {data.classes.map((cls) => {
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
                                <div className="w-24 h-1.5 bg-[#E2DFD7] mt-1 overflow-hidden">
                                  <div
                                    className={`h-full ${
                                      (cls.confirmation_probability || 0) >= 0.8
                                        ? 'bg-[#15803D]'
                                        : (cls.confirmation_probability || 0) >= 0.5
                                        ? 'bg-[#D97706]'
                                        : 'bg-[#DC2626]'
                                    }`}
                                    style={{
                                      width: `${(cls.confirmation_probability || 0) * 100}%`,
                                    }}
                                  ></div>
                                </div>
                              </div>
                            ) : (
                              <span className="text-[#64748B]">—</span>
                            )}
                          </td>
                          <td className="p-2.5 text-right">
                            <button className="bg-[#0F172A] hover:bg-[#1D4ED8] text-white text-[11px] font-bold px-2.5 py-1 transition-colors cursor-pointer uppercase">
                              Book
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* UPSTREAM QUOTA ARBITRAGE CARD */}
            {data.arbitrage_recommendation && (
              <div className="border-2 border-[#15803D] bg-[#F0FDF4] p-4 text-xs font-mono">
                <div className="flex items-center space-x-2 font-bold text-[#15803D] uppercase text-sm mb-2">
                  <Tag className="w-4 h-4" />
                  <span>Upstream Quota Arbitrage Discovered</span>
                </div>
                <div className="text-[#0F172A] leading-relaxed">
                  {data.arbitrage_recommendation.instruction}
                </div>
                <div className="mt-3 pt-2 border-t border-[#BBF7D0] flex flex-wrap items-center justify-between text-[#15803D] font-bold">
                  <span>Upstream Station: {data.arbitrage_recommendation.upstream_station_name} ({data.arbitrage_recommendation.upstream_station_code})</span>
                  <span>Available Berths: {data.arbitrage_recommendation.available_seats} ({data.arbitrage_recommendation.quota_type})</span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="py-8 text-center font-mono text-xs text-[#64748B]">
            No live availability data retrieved.
          </div>
        )}

        {/* MODAL FOOTER */}
        <div className="mt-6 pt-4 border-t border-[#E2DFD7] flex justify-end">
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
