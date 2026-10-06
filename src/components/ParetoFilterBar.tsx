import React from 'react';
import { 
  Zap, 
  Coins, 
  Scale, 
  ShieldCheck, 
  Home, 
  Bus, 
  Layers, 
  Sparkles,
  ArrowUpDown
} from 'lucide-react';

export type ParetoFilterKey = 
  | 'ALL' 
  | 'PARETO_FRONTIER' 
  | 'FASTEST' 
  | 'CHEAPEST' 
  | 'BALANCED' 
  | 'MOST_RELIABLE' 
  | 'COMFORT_HOMESTAY' 
  | 'MULTIMODAL';

export interface ParetoFilterCounts {
  ALL: number;
  PARETO_FRONTIER: number;
  FASTEST: number;
  CHEAPEST: number;
  BALANCED: number;
  MOST_RELIABLE: number;
  COMFORT_HOMESTAY: number;
  MULTIMODAL: number;
}

interface ParetoFilterBarProps {
  selectedFilter: ParetoFilterKey;
  onSelectFilter: (filterKey: ParetoFilterKey) => void;
  sortBy: string;
  onSelectSort: (sortKey: string) => void;
  counts: ParetoFilterCounts;
}

const FILTER_ITEMS: Array<{
  key: ParetoFilterKey;
  label: string;
  icon: React.ElementType;
}> = [
  { key: 'ALL', label: 'All routes', icon: Layers },
  { key: 'PARETO_FRONTIER', label: 'Recommended', icon: Sparkles },
  { key: 'FASTEST', label: 'Fastest', icon: Zap },
  { key: 'CHEAPEST', label: 'Cheapest', icon: Coins },
  { key: 'BALANCED', label: 'Best balance', icon: Scale },
  { key: 'MOST_RELIABLE', label: 'Most reliable', icon: ShieldCheck },
  { key: 'COMFORT_HOMESTAY', label: 'Less waiting', icon: Home },
  { key: 'MULTIMODAL', label: 'Train + bus', icon: Bus },
];

export const ParetoFilterBar: React.FC<ParetoFilterBarProps> = ({
  selectedFilter,
  onSelectFilter,
  sortBy,
  onSelectSort,
  counts,
}) => {
  return (
    <div className="bg-white/90 backdrop-blur-md rounded-2xl p-4 mb-5 border border-white/80 shadow-xs flex flex-col gap-3 font-['Timeless']">
      {/* Top Header: Title + Sort Dropdown */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-stone-100">
        <div className="flex items-center gap-2">
          <h3 className="font-['Timeless'] text-sm font-bold text-[#4A5D30] tracking-tight">
            Filter
          </h3>
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-1.5 text-xs font-['Timeless'] ml-auto">
          <span className="text-stone-500 font-medium flex items-center gap-1">
            <ArrowUpDown className="w-3 h-3 text-stone-400" />
            Sort:
          </span>
          <select
            value={sortBy}
            onChange={(e) => onSelectSort(e.target.value)}
            className="bg-stone-50 hover:bg-stone-100 text-[#4A5D30] font-semibold py-1 px-2.5 rounded-lg border border-stone-200 outline-none text-xs transition-colors cursor-pointer font-['Timeless']"
          >
            <option value="best_match">Best Match</option>
            <option value="duration">Fastest First</option>
            <option value="fare">Cheapest First</option>
            <option value="reliability">Most Reliable</option>
            <option value="comfort">Less Waiting</option>
          </select>
        </div>
      </div>

      {/* Filter Chips Horizontal Scroller */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none font-['Timeless']">
        {FILTER_ITEMS.map((item) => {
          const count = counts[item.key] || 0;
          const isSelected = selectedFilter === item.key;
          const Icon = item.icon;

          // Don't show specific filter chips if count is 0 and it's not the active one
          if (count === 0 && !isSelected && item.key !== 'ALL') {
            return null;
          }

          return (
            <button
              key={item.key}
              type="button"
              onClick={() => onSelectFilter(item.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-['Timeless'] text-xs font-semibold whitespace-nowrap transition-all border cursor-pointer ${
                isSelected
                  ? 'bg-[#4A5D30] text-[#F6F0E6] border-[#4A5D30] shadow-xs scale-[1.02]'
                  : 'bg-stone-50 hover:bg-white text-stone-700 hover:text-[#4A5D30] border-stone-200/90'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-[#E5D5BF]' : 'text-stone-500'}`} />
              <span>{item.label}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ml-0.5 font-['Timeless'] ${
                  isSelected
                    ? 'bg-white/20 text-white'
                    : 'bg-stone-200 text-stone-600'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default ParetoFilterBar;
