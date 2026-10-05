import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="p-4 sm:p-5 absolute top-0 left-0 z-50">
      <Link
        to="/"
        className="group inline-flex items-center gap-2.5 bg-[#F6F0E6]/95 backdrop-blur-md px-4 py-2 rounded-xl shadow-[0_4px_16px_rgba(74,93,48,0.12)] border border-[#4A5D30]/20 transition-all hover:-translate-y-0.5"
      >
        <span
          className="text-[#4A5D30] text-xl font-bold tracking-wider lowercase"
          style={{ fontFamily: "'ROSSTEN', sans-serif" }}
        >
          margdarshak
        </span>
      </Link>
    </nav>
  );
}
