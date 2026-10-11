import { useState } from 'react';

export default function DisclaimerBanner() {
  const [isVisible, setIsVisible] = useState(() => {
    return sessionStorage.getItem('dismiss_prototype_banner') !== 'true';
  });

  if (!isVisible) return null;

  const handleDismiss = () => {
    sessionStorage.setItem('dismiss_prototype_banner', 'true');
    setIsVisible(false);
  };

  return (
    <aside
      aria-label="Prototype Version Disclaimer"
      className="w-full bg-[#3D4C27] text-[#F6F0E6] text-[11px] sm:text-xs py-1.5 px-3 sm:px-4 flex items-center justify-between gap-2 font-['Timeless'] shrink-0 z-50 tracking-wide border-b border-[#2D381D] select-none shadow-xs"
    >
      <div className="flex-1 flex items-center justify-center gap-2 flex-wrap text-center">
        <span className="inline-flex items-center px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider bg-[#F6F0E6]/20 text-[#FAF7F2] rounded">
          Test Version
        </span>
        <span className="font-medium text-stone-200">
          <span className="hidden sm:inline">
            Prototype Evaluation Build: Operating on augmented transit data for SIH. Official Indian Railways CRIS & WTT live feed integration ready.
          </span>
          <span className="inline sm:hidden">
            Built on augmented prototype data for SIH (CRIS & WTT ready).
          </span>
        </span>
      </div>

      <button
        type="button"
        onClick={handleDismiss}
        className="text-[#F6F0E6]/70 hover:text-white p-0.5 rounded transition-colors cursor-pointer shrink-0"
        title="Dismiss banner"
        aria-label="Dismiss banner"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </aside>
  );
}
