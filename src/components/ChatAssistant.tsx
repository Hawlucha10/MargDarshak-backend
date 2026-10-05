import React, { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '../api/client';
import type { ChatMessage, ChatBusOption, ChatRoutePreview } from '../api/types';

interface ChatAssistantProps {
  currentOrigin?: string;
  currentDestination?: string;
  travelDate?: string;
  onSelectRoute?: (origin: string, destination: string) => void;
}

interface ExtendedChatMessage extends ChatMessage {
  id: string;
  suggestedActions?: string[];
  busesPreview?: ChatBusOption[];
  routesPreview?: ChatRoutePreview[];
}

export const ChatAssistant: React.FC<ChatAssistantProps> = ({
  currentOrigin,
  currentDestination,
  travelDate,
  onSelectRoute,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ExtendedChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Namaste! I am MargDarshak AI, your multimodal journey assistant. ' +
        'Ask me for train routes, delay predictions, upstream confirmed seat hacks, or taking connecting buses to avoid long layovers!',
      suggestedActions: [
        'Can I take a bus from Pune to Mumbai CST?',
        'Is train 12138 running on time?',
        'How does upstream booking work?',
      ],
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend ?? input).trim();
    if (!text || loading) return;

    const userMsg: ExtendedChatMessage = {
      id: String(Date.now()),
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const history: ChatMessage[] = messages
        .filter((m) => m.id !== 'welcome')
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await sendChatMessage({
        message: text,
        conversation_history: history,
        current_origin: currentOrigin,
        current_destination: currentDestination,
        travel_date: travelDate,
      });

      const botMsg: ExtendedChatMessage = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: res.reply,
        suggestedActions: res.suggested_actions,
        busesPreview: res.buses_preview,
        routesPreview: res.routes_preview,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          role: 'assistant',
          content: 'Sorry, I encountered an issue connecting to the AI assistant. Please try again.',
          suggestedActions: ['Can I take a bus from Pune to Mumbai CST?'],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content:
          'Namaste! How can I help plan your trip? Ask about train routes, connecting buses, live delays, or seat availability hacks.',
        suggestedActions: [
          'Can I take a bus from Pune to Mumbai CST?',
          'Is train 12138 running on time?',
          'Fastest train from Delhi to Pune',
        ],
      },
    ]);
  };

  return (
    <div className={`fixed z-50 font-['Timeless'] ${isOpen ? 'bottom-6 right-4 sm:right-6' : 'bottom-[38px] sm:bottom-[42px] right-6 sm:right-10'}`}>
      {/* Floating Toggle Button - Raised so it cleanly overlaps the footer strip */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="group flex items-center gap-3 px-5 py-3.5 bg-[#4A5D30] hover:bg-[#3D4C27] text-[#F6F0E6] rounded-full shadow-2xl transition-all duration-300 hover:scale-105 active:scale-95 border-2 border-[#E5D5BF]"
          aria-label="Open MargDarshak AI Travel Assistant"
        >
          <div className="relative">
            <svg
              className="w-6 h-6 text-[#F6F0E6]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#E5D5BF] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-[#E5D5BF]"></span>
            </span>
          </div>
          <span className="font-semibold tracking-wide text-sm font-['Timeless']">MargDarshak AI</span>
        </button>
      )}

      {/* Slide-Up Chat Window */}
      {isOpen && (
        <div className="w-[390px] max-w-[95vw] h-[580px] max-h-[85vh] bg-[#F6F0E6] rounded-2xl shadow-2xl border-2 border-[#4A5D30]/20 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-300 font-['Timeless']">
          {/* Header */}
          <div className="bg-[#4A5D30] text-white px-4 py-3 flex items-center justify-between shadow-md">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center border border-white/20">
                <svg
                  className="w-4 h-4 text-[#E5D5BF]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-bold text-sm tracking-wide flex items-center gap-2">
                  MargDarshak AI
                  <span className="inline-block w-2 h-2 rounded-full bg-emerald-400"></span>
                </h3>
                <p className="text-[11px] text-[#E5D5BF]">Multimodal Railway & Bus Assistant</p>
              </div>
            </div>
            <div className="flex items-center gap-1 text-white/80">
              <button
                onClick={clearChat}
                title="Clear Chat"
                className="p-1.5 hover:text-white hover:bg-white/10 rounded-lg transition-colors text-xs"
              >
                Clear
              </button>
              <button
                onClick={() => setIsOpen(false)}
                title="Minimize"
                className="p-1.5 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </div>

          {/* Active Context Bar if on Search/Results */}
          {currentOrigin && currentDestination && (
            <div className="bg-[#E5D5BF]/60 px-3.5 py-1.5 border-b border-[#E5D5BF] flex items-center justify-between text-xs text-[#4A5D30] font-medium">
              <span>
                Active Corridor: <strong>{currentOrigin}</strong> → <strong>{currentDestination}</strong>
              </span>
              <span className="text-[10px] bg-[#4A5D30]/10 px-1.5 py-0.5 rounded">Context Active</span>
            </div>
          )}

          {/* Message History */}
          <div className="flex-1 p-3.5 overflow-y-auto space-y-3.5 text-sm">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[88%] rounded-2xl px-3.5 py-2.5 shadow-sm text-sm leading-relaxed whitespace-pre-wrap ${
                    m.role === 'user'
                      ? 'bg-[#4A5D30] text-white rounded-br-none'
                      : 'bg-white text-gray-900 border border-[#E5D5BF] rounded-bl-none'
                  }`}
                >
                  {m.content}
                </div>

                {/* Bus Preview Cards */}
                {m.busesPreview && m.busesPreview.length > 0 && (
                  <div className="mt-2.5 w-full space-y-1.5">
                    <p className="text-[11px] font-semibold text-[#4A5D30] uppercase tracking-wider px-1">
                      🚌 Bus Corridors Available
                    </p>
                    {m.busesPreview.slice(0, 3).map((b, idx) => (
                      <div
                        key={idx}
                        className="bg-white p-2.5 rounded-xl border border-[#E5D5BF] shadow-xs text-xs space-y-1 hover:border-[#4A5D30] transition-colors"
                      >
                        <div className="flex justify-between items-center">
                          <span className="font-semibold text-gray-900">{b.operator_name}</span>
                          <span className="font-bold text-[#4A5D30]">₹{b.fare}</span>
                        </div>
                        <div className="flex justify-between text-gray-600 text-[11px]">
                          <span>
                            {b.departure} → {b.arrival} ({Math.floor(b.duration_minutes / 60)}h{' '}
                            {b.duration_minutes % 60}m)
                          </span>
                          <span className="bg-[#E5D5BF]/50 px-1.5 py-0.5 rounded text-[10px] text-gray-800">
                            {b.bus_type}
                          </span>
                        </div>
                        <div className="text-[10px] text-gray-500 truncate">
                          {b.from_terminal} → {b.to_terminal}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Route Preview Cards */}
                {m.routesPreview && m.routesPreview.length > 0 && (
                  <div className="mt-2.5 w-full space-y-1.5">
                    <p className="text-[11px] font-semibold text-[#4A5D30] uppercase tracking-wider px-1">
                      🚆 Recommended Travel Options
                    </p>
                    {m.routesPreview.map((r, idx) => (
                      <div
                        key={idx}
                        className="bg-white p-2.5 rounded-xl border border-[#E5D5BF] shadow-xs text-xs space-y-1 hover:border-[#4A5D30] transition-colors"
                      >
                        <div className="flex justify-between items-center">
                          <span className="font-semibold text-gray-900">{r.label}</span>
                          <span className="font-bold text-[#4A5D30]">₹{r.fare}</span>
                        </div>
                        <div className="flex justify-between text-gray-600 text-[11px]">
                          <span>Duration: {r.duration}</span>
                          <span>{r.transfers === 0 ? 'Direct' : `${r.transfers} Transfer(s)`}</span>
                        </div>
                        <div className="text-[10px] text-gray-500 line-clamp-2">
                          {r.legs_summary}
                        </div>
                        {onSelectRoute && currentOrigin && currentDestination && (
                          <button
                            onClick={() => onSelectRoute(currentOrigin, currentDestination)}
                            className="mt-1 text-[11px] font-medium text-[#4A5D30] hover:underline"
                          >
                            View details on search page →
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Suggested Action Chips (lightbulbs removed, Timeless font applied) */}
                {m.suggestedActions && m.suggestedActions.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {m.suggestedActions.map((action, idx) => {
                      const cleanAction = action.replace(/^💡\s*/, '');
                      return (
                        <button
                          key={idx}
                          onClick={() => handleSend(cleanAction)}
                          className="text-[12px] bg-[#E5D5BF]/85 hover:bg-[#E5D5BF] text-gray-900 px-3 py-1.5 rounded-full border border-[#4A5D30]/25 transition-all hover:scale-102 active:scale-98 text-left font-['Timeless'] font-medium shadow-2xs cursor-pointer"
                        >
                          {cleanAction}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex items-center gap-2 text-xs text-gray-600 bg-white border border-[#E5D5BF] px-3.5 py-2.5 rounded-2xl rounded-bl-none shadow-sm max-w-[75%]">
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#4A5D30] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#4A5D30]"></span>
                </span>
                <span>MargDarshak AI is checking live data...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-3 bg-white border-t border-[#E5D5BF]">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about trains, buses, delays..."
                disabled={loading}
                className="flex-1 bg-[#F6F0E6] text-gray-900 text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-[#E5D5BF] focus:outline-none focus:border-[#4A5D30] transition-colors"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="p-2.5 bg-[#4A5D30] hover:bg-[#3D4C27] disabled:bg-[#4A5D30]/40 text-white rounded-xl shadow-sm transition-all duration-200"
                aria-label="Send Message"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14 5l7 7m0 0l-7 7m7-7H3"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
