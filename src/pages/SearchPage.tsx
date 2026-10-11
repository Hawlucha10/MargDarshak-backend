import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import SearchBar from '../components/SearchBar';
import InteractiveGrid from '../components/InteractiveGrid';
import { useChat } from '../context/ChatContext';

const HEADINGS = [
  'Where to next?',
  'Plan without limits.',
  'Uncover every route.',
  'Less rush. More wonder.',
  'Ready for the rails?',
];

export default function SearchPage() {
  const [headingIndex, setHeadingIndex] = useState(0);
  const { toggleChat } = useChat();

  useEffect(() => {
    const interval = setInterval(() => {
      setHeadingIndex((prev) => (prev + 1) % HEADINGS.length);
    }, 3200);
    return () => clearInterval(interval);
  }, []);

  return (
    <InteractiveGrid>
      {/* Main Content Area - Strictly fits vertically on mobile & desktop without scroll */}
      <div className="flex-1 flex flex-col items-center justify-center px-3 sm:px-4 py-2 sm:py-6 max-w-4xl mx-auto w-full min-h-0 overflow-hidden">
        {/* Animated Headline in Galter font, text black */}
        <div className="w-full text-center mb-2 sm:mb-6 md:mb-8 shrink-0">
          <div className="h-12 sm:h-20 md:h-26 relative overflow-hidden flex justify-center items-center">
            <AnimatePresence mode="wait">
              <motion.h1
                key={headingIndex}
                initial={{ y: 25, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -25, opacity: 0 }}
                transition={{ duration: 0.35, ease: 'easeOut' }}
                className="text-[28px] sm:text-[46px] md:text-[62px] lg:text-[74px] text-[#111111] tracking-normal absolute select-none font-normal"
                style={{ fontFamily: "'Galter', serif" }}
              >
                {HEADINGS[headingIndex]}
              </motion.h1>
            </AnimatePresence>
          </div>
        </div>

        {/* Short & Compact Search Card */}
        <div className="w-full max-w-2xl relative z-10 shrink-0">
          <SearchBar />
        </div>
      </div>

      {/* Bottom Green Stripe */}
      <footer className="w-full bg-[#4A5D30] py-2.5 sm:py-3.5 px-4 sm:px-10 flex items-center justify-between shrink-0 shadow-lg z-20">
        {/* Logo: MargDarshak in ROSSTEN font (font-normal to prevent synthetic bolding artifacts) */}
        <div className="flex-1 flex justify-start items-center">
          <span
            className="text-[#F6F0E6] text-[24px] sm:text-[32px] tracking-wider select-none font-normal"
            style={{ fontFamily: "'ROSSTEN', sans-serif" }}
          >
            MargDarshak
          </span>
        </div>

        {/* Center: MargDarshak AI text button directly on the strip itself */}
        <div className="flex-1 flex justify-center items-center">
          <button
            type="button"
            onClick={toggleChat}
            className="text-[#F6F0E6] hover:text-white text-[15px] sm:text-[18px] tracking-wide font-normal select-none cursor-pointer hover:opacity-85 transition-opacity"
            style={{ fontFamily: "'Timeless', sans-serif" }}
          >
            MargDarshak AI
          </button>
        </div>

        {/* Slogan at bottom right - Hidden on phone screens (< md) to avoid congestion */}
        <div className="hidden md:flex flex-1 justify-end items-center">
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
