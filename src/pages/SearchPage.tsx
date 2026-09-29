import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import SearchBar from '../components/SearchBar';

const HEADINGS = [
  'Where to next?',
  'Plan without limits.',
  'Uncover every route.',
  'Less rush. More wonder.',
  'Ready for the rails?',
];

export default function SearchPage() {
  const [headingIndex, setHeadingIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setHeadingIndex((prev) => (prev + 1) % HEADINGS.length);
    }, 3200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-20 relative min-h-screen">
      {/* Animated Heading */}
      <div className="w-full max-w-3xl text-center mb-10">
        <div className="h-20 md:h-28 relative overflow-hidden flex justify-center items-center">
          <AnimatePresence mode="wait">
            <motion.h1
              key={headingIndex}
              initial={{ y: 35, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -35, opacity: 0 }}
              transition={{ duration: 0.45, ease: 'easeOut' }}
              className="text-4xl md:text-7xl font-[var(--font-serif)] text-brand-text font-bold tracking-tight absolute"
            >
              {HEADINGS[headingIndex]}
            </motion.h1>
          </AnimatePresence>
        </div>
      </div>

      {/* Search Card */}
      <div className="w-full max-w-3xl relative z-10">
        <SearchBar />
      </div>

      {/* Footer */}
      <footer className="absolute bottom-0 w-full bg-brand-darkolive py-5 text-center">
        <p className="font-[var(--font-serif)] text-brand-cream text-lg tracking-wide font-normal">
          Less rush. More wonder.
        </p>
      </footer>
    </div>
  );
}
