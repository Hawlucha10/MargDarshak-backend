import React, { useState, useEffect } from 'react';

interface Props {
  children: React.ReactNode;
}

export default function InteractiveGrid({ children }: Props) {
  const [mousePos, setMousePos] = useState({ x: -1000, y: -1000 });
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
      setIsHovered(true);
    };

    const handleMouseLeave = () => {
      setIsHovered(false);
    };

    window.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <div className="relative w-full h-[100dvh] max-h-[100dvh] overflow-hidden bg-[#E5D5BF]">
      {/* 1. Base Blueprint Grid (#4A5D30 Dark Green on #E5D5BF Background) */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(74, 93, 48, 0.12) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(74, 93, 48, 0.12) 1px, transparent 1px),
            linear-gradient(to right, rgba(74, 93, 48, 0.28) 1.5px, transparent 1.5px),
            linear-gradient(to bottom, rgba(74, 93, 48, 0.28) 1.5px, transparent 1.5px)
          `,
          backgroundSize: '24px 24px, 24px 24px, 120px 120px, 120px 120px',
        }}
      />

      {/* 2. Bold Hovering Grid Lines - Removed all color hue/radial glow */}
      {isHovered && (
        <>
          {/* Bold vertical grid line */}
          <div
            className="absolute top-0 bottom-0 pointer-events-none w-[2px] bg-[#4A5D30]/65 z-[1]"
            style={{ left: `${mousePos.x}px` }}
          />
          {/* Bold horizontal grid line */}
          <div
            className="absolute left-0 right-0 pointer-events-none h-[2px] bg-[#4A5D30]/65 z-[1]"
            style={{ top: `${mousePos.y}px` }}
          />
        </>
      )}

      {/* 3. Page Content */}
      <div className="relative z-10 w-full h-full flex flex-col justify-between overflow-hidden min-h-0">
        {children}
      </div>
    </div>
  );
}
