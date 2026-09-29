export default function BusLegBadge() {
  return (
    <span className="bg-[#D4A843]/15 text-[#9E6D14] border border-[#D4A843]/40 px-2.5 py-1 rounded-lg text-xs font-[var(--font-ui)] font-semibold inline-flex items-center gap-1.5">
      <svg className="w-3.5 h-3.5 text-[#B88728]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
      Bus Connection
    </span>
  );
}
