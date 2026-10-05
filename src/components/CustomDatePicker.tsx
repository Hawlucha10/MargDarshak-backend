import { useState, useRef, useEffect } from 'react';

interface Props {
  value: string; // ISO date string "YYYY-MM-DD"
  onChange: (dateStr: string) => void;
  minDate?: string; // Optional minimum selectable date "YYYY-MM-DD"
  disabled?: boolean;
}

export default function CustomDatePicker({ value, onChange, minDate, disabled = false }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Parse initial selected date or default to today
  const selectedDate = value ? new Date(value + 'T00:00:00') : new Date();
  const minDateObj = minDate ? new Date(minDate + 'T00:00:00') : new Date();
  minDateObj.setHours(0, 0, 0, 0);

  // Month and Year view state
  const [viewYear, setViewYear] = useState(selectedDate.getFullYear());
  const [viewMonth, setViewMonth] = useState(selectedDate.getMonth()); // 0-indexed

  // Sync view when value changes
  useEffect(() => {
    if (value) {
      const d = new Date(value + 'T00:00:00');
      setViewYear(d.getFullYear());
      setViewMonth(d.getMonth());
    }
  }, [value]);

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const handlePrevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear((prev) => prev - 1);
    } else {
      setViewMonth((prev) => prev - 1);
    }
  };

  const handleNextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear((prev) => prev + 1);
    } else {
      setViewMonth((prev) => prev + 1);
    }
  };

  // Generate calendar grid
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const firstDayIndex = new Date(viewYear, viewMonth, 1).getDay(); // 0 = Sunday
  const prevMonthDays = new Date(viewYear, viewMonth, 0).getDate();

  const calendarDays = [];

  // Previous month trailing days
  for (let i = firstDayIndex - 1; i >= 0; i--) {
    calendarDays.push({
      day: prevMonthDays - i,
      month: viewMonth - 1,
      year: viewMonth === 0 ? viewYear - 1 : viewYear,
      isCurrentMonth: false,
    });
  }

  // Current month days
  for (let d = 1; d <= daysInMonth; d++) {
    calendarDays.push({
      day: d,
      month: viewMonth,
      year: viewYear,
      isCurrentMonth: true,
    });
  }

  // Next month leading days
  const remainingCells = (7 - (calendarDays.length % 7)) % 7;
  for (let d = 1; d <= remainingCells; d++) {
    calendarDays.push({
      day: d,
      month: viewMonth + 1,
      year: viewMonth === 11 ? viewYear + 1 : viewYear,
      isCurrentMonth: false,
    });
  }

  const formatDisplay = (isoStr: string) => {
    if (!isoStr) return 'Select Date';
    const [y, m, d] = isoStr.split('-');
    return `${d} - ${m} - ${y}`;
  };

  const isSelected = (d: number, m: number, y: number) => {
    if (!value) return false;
    const [currY, currM, currD] = value.split('-').map(Number);
    return currY === y && currM - 1 === m && currD === d;
  };

  const isPast = (d: number, m: number, y: number) => {
    const cellDate = new Date(y, m, d);
    cellDate.setHours(0, 0, 0, 0);
    return cellDate < minDateObj;
  };

  const handleDaySelect = (d: number, m: number, y: number) => {
    if (isPast(d, m, y)) return;
    const actualMonth = (m + 12) % 12 + 1;
    const actualYear = m < 0 ? y - 1 : m > 11 ? y + 1 : y;
    const formatted = `${actualYear}-${String(actualMonth).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    onChange(formatted);
    setIsOpen(false);
  };

  const handleSelectToday = () => {
    const today = new Date();
    const formatted = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    onChange(formatted);
    setViewYear(today.getFullYear());
    setViewMonth(today.getMonth());
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative inline-block">
      {/* Trigger Button - Perfectly centered capsule */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className="h-8.5 inline-flex items-center justify-center gap-2.5 bg-[#FAF7F2] border border-[#4A5D30]/25 hover:border-[#4A5D30] rounded-full px-3.5 text-sm sm:text-[15px] font-['Timeless'] text-[#111111] transition-all shadow-2xs hover:bg-[#F3ECE0] cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
      >
        <span className="font-semibold tracking-wide leading-none translate-y-[0.5px]">
          {formatDisplay(value)}
        </span>
        <svg
          className="w-3.5 h-3.5 text-[#4A5D30] shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.8}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      </button>

      {/* Popover Calendar - Always opens UPWARDS so it never overlaps the bottom stripe */}
      {isOpen && (
        <div className="absolute z-[100] bottom-full mb-2.5 left-0 w-72 bg-[#F6F0E6] border border-[#4A5D30]/25 rounded-2xl shadow-2xl p-4 font-['Timeless'] animate-in fade-in zoom-in-95 duration-150">
          {/* Header */}
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-[#4A5D30]/15">
            <span className="font-bold text-sm text-[#111111] tracking-wide">
              {monthNames[viewMonth]}, {viewYear}
            </span>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handlePrevMonth}
                className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-[#E5D5BF] text-[#4A5D30] transition-colors cursor-pointer text-sm font-bold"
                title="Previous month"
              >
                ←
              </button>
              <button
                type="button"
                onClick={handleNextMonth}
                className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-[#E5D5BF] text-[#4A5D30] transition-colors cursor-pointer text-sm font-bold"
                title="Next month"
              >
                →
              </button>
            </div>
          </div>

          {/* Weekday Labels */}
          <div className="grid grid-cols-7 gap-1 text-center mb-1 text-xs font-semibold text-[#4A5D30]/80">
            <span>Su</span>
            <span>Mo</span>
            <span>Tu</span>
            <span>We</span>
            <span>Th</span>
            <span>Fr</span>
            <span>Sa</span>
          </div>

          {/* Days Grid */}
          <div className="grid grid-cols-7 gap-1 text-center text-xs">
            {calendarDays.map((cell, idx) => {
              const selected = isSelected(cell.day, cell.month, cell.year);
              const past = isPast(cell.day, cell.month, cell.year);

              return (
                <button
                  key={idx}
                  type="button"
                  disabled={past}
                  onClick={() => handleDaySelect(cell.day, cell.month, cell.year)}
                  className={`h-7 w-7 sm:h-8 sm:w-8 mx-auto flex items-center justify-center text-xs transition-all ${
                    selected
                      ? 'bg-[#4A5D30] text-[#F6F0E6] font-bold rounded-xl shadow-xs'
                      : past
                      ? 'text-stone-300 cursor-not-allowed'
                      : cell.isCurrentMonth
                      ? 'text-[#111111] hover:bg-[#E5D5BF] rounded-xl cursor-pointer'
                      : 'text-stone-400 hover:bg-[#E5D5BF]/50 rounded-xl cursor-pointer'
                  }`}
                >
                  {cell.day}
                </button>
              );
            })}
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between mt-3 pt-2 border-t border-[#4A5D30]/15 text-xs font-semibold">
            <button
              type="button"
              onClick={() => { onChange(''); setIsOpen(false); }}
              className="text-stone-500 hover:text-[#111111] transition-colors cursor-pointer"
            >
              Clear
            </button>
            <button
              type="button"
              onClick={handleSelectToday}
              className="text-[#4A5D30] hover:underline transition-all cursor-pointer font-bold"
            >
              Today
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
