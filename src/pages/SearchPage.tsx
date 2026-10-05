import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import SearchBar from '../components/SearchBar';
import InteractiveGrid from '../components/InteractiveGrid';

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
    <InteractiveGrid>
      {/* Main Content Area - Centered vertically without causing scroll */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-4 sm:py-6 max-w-4xl mx-auto w-full">
        {/* Animated Headline in Galter font, text black */}
        <div className="w-full text-center mb-6 sm:mb-8">
          <div className="h-18 sm:h-22 md:h-26 relative overflow-hidden flex justify-center items-center">
            <AnimatePresence mode="wait">
              <motion.h1
                key={headingIndex}
                initial={{ y: 30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -30, opacity: 0 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
                className="text-[38px] sm:text-[50px] md:text-[62px] lg:text-[74px] text-[#111111] tracking-normal absolute select-none font-normal"
                style={{ fontFamily: "'Galter', serif" }}
              >
                {HEADINGS[headingIndex]}
              </motion.h1>
            </AnimatePresence>
          </div>
        </div>

        {/* Short & Compact Search Card */}
        <div className="w-full max-w-2xl relative z-10">
          <SearchBar />
        </div>
      </div>

      {/* Bottom Green Stripe */}
      <footer className="w-full bg-[#4A5D30] py-3.5 px-6 sm:px-10 flex items-center justify-between shrink-0 shadow-lg z-20">
        {/* Logo: MargDarshak in ROSSTEN font (font-normal to prevent synthetic bolding artifacts) */}
        <div className="flex items-center">
          <span
            className="text-[#F6F0E6] text-[26px] sm:text-[32px] tracking-wider select-none font-normal"
            style={{ fontFamily: "'ROSSTEN', sans-serif" }}
          >
            MargDarshak
          </span>
        </div>

        {/* Slogan at bottom right */}
        <div className="flex items-center">
          <p
            className="text-[#F6F0E6]/90 text-[16px] sm:text-[18px] tracking-wide font-normal select-none"
            style={{ fontFamily: "'OFLGoudyStM', Georgia, serif" }}
          >
            Less rush. More wonder.
          </p>
        </div>
      </footer>
    </InteractiveGrid>
  );
}
