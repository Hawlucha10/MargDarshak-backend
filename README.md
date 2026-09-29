# MargDarshak Frontend Client
### Next-Gen Editorial Rail & Multimodal Interface

**Architect & Lead Engineer:** Ojas Nagar (`oriio1309` · oriio.1304@gmail.com)  
**Pitch / Hackathon:** Team `potato_1` · Smart India Hackathon (SIH 2026)  
**Repository Branch:** [Hawlucha10/MargDarshak-backend (frontend branch)](https://github.com/Hawlucha10/MargDarshak-backend/tree/frontend)  
**Standalone Remote:** `https://github.com/Hawlucha10/MargDarshak-frontend.git`

---

## 🎨 Design System & UX Principles

The MargDarshak Frontend Client is built with **React 19, TypeScript, Vite 8, and Tailwind CSS v4**.

- **Editorial Color Palette**: Warm Cream (`#F5F0E8`), Soft Periwinkle (`#C5D0F6`), Midnight Navy (`#1A2766`), Olive Green (`#5A6B3C`), and Bus Gold (`#D4A843`).
- **Typography**: `DM Serif Display` for editorial, commanding headers; `Inter` and `DM Sans` for crisp data layouts.
- **Ergonomics (No Capsule Shapes)**: Strict elimination of pill/capsule shapes (`rounded-[999px]`). Clean, tactile rectangular rounded corners (`rounded-xl` and `rounded-2xl`).
- **Date Picking**: Disallows past dates with `min={todayStr}` and provides one-click quick chips (`Today`, `Tomorrow`, `This Weekend`, `+1 Week`).
- **Dynamic Headings**: Rotating destination queries with zero static hardcoding.
- **Conversational Clarification**: When an ambiguous query (e.g., `"ghar"`) is submitted, a dedicated clarification card appears with helpful prompts and one-click corridor suggestions.
- **Optimized Screen Real Estate**: Widened route and AI insights panel (62–65% desktop width) with a compact, sticky India overview map (35–38% desktop width).
- **Interactive Geospatial Cartography**: Light-contrast OpenStreetMap canvas with dynamic route polylines (blue for train, amber for bus) and interactive hover-to-reveal intermediate junctions.

---

## 🛠️ Components & Architecture

```text
src/
├── components/
│   ├── SearchForm.tsx           # Multi-modal input form with date guards & class filters
│   ├── StationInput.tsx         # Real-time search across 8,989 stations with hub tags
│   ├── RouteCard.tsx            # Multi-leg route tile with platform guidance & delay tags
│   ├── RouteDetailsModal.tsx    # Comprehensive leg timeline, coach configs & bus connections
│   ├── QuotaArbitrageModal.tsx  # ConfirmTkt-style upstream booking instructions
│   ├── AmbiguityCard.tsx        # Conversational guidance for vague natural language searches
│   ├── IndiaMap.tsx             # Canvas-accelerated Leaflet map with progressive junction reveal
│   └── TelemetryPanel.tsx       # Live IR ISRO/COA train tracking & delay metrics
├── services/
│   └── api.ts                   # Fast REST API client interfacing backend microservice
└── App.tsx                      # Main application shell with split desktop layout
```

---

## 🚀 Development & Production Build

```bash
# 1. Install dependencies
npm install

# 2. Start Vite development server
npm run dev -- --port 3000 --host

# 3. Build for production (TypeScript type-check + bundle)
npm run build
```
Production build compiles cleanly in **< 900 ms** with zero errors.

---

## 📜 Intellectual Property & Authorship

- **Project**: MargDarshak Frontend Client
- **Author & Lead Architect**: Ojas Nagar (`oriio1309` · oriio.1304@gmail.com)
- **Pitched At**: Smart India Hackathon (SIH 2026) · Team `potato_1`
- **License**: MIT License
