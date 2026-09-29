import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="p-6 absolute top-0 left-0 z-50">
      <Link
        to="/"
        className="group inline-flex items-center gap-3 bg-white/95 backdrop-blur-md px-5 py-2.5 rounded-2xl shadow-[0_4px_20px_rgba(26,39,102,0.08)] border border-stone-200/80 transition-all hover:shadow-[0_6px_24px_rgba(26,39,102,0.12)] hover:-translate-y-0.5"
      >
        <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#1A2766] to-[#3B5BDB] flex items-center justify-center text-[#F5F0E8] font-serif font-bold text-xl shadow-xs group-hover:scale-105 transition-transform">
          M
        </span>
        <div className="flex flex-col">
          <span
            className="text-[#1A2766] text-2xl font-bold tracking-tight leading-none group-hover:text-brand-blue transition-colors"
            style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}
          >
            MargDarshak
          </span>
        </div>
      </Link>
    </nav>
  );
}
