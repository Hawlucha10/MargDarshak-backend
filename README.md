# MargDarshak Frontend Client
### Next-Gen Editorial Rail & Multimodal Interface

**Smart India Hackathon 2025 · Problem Statement #58**  
*Author:* `oriio1309 <oriio.1304@gmail.com>` | *Team:* Binary Beacons

---

## 🎨 Design System & UX Standards

The frontend client is engineered with **React 19, TypeScript, Vite 8, and Tailwind CSS v4**.

- **Palette**: Warm Cream (`#F5F0E8`), Soft Periwinkle (`#C5D0F6`), Midnight Navy (`#1A2766`), Olive Green (`#5A6B3C`), and Bus Gold (`#D4A843`).
- **Typography**: `DM Serif Display` for elegant, editorial titles; `Inter` and `DM Sans` for crisp route leg cards.
- **Ergonomics**: **No capsule/pill shapes** (`rounded-[999px]`). Clean, tactile rectangular rounded corners (`rounded-xl` and `rounded-2xl`).
- **Date Picking**: Disallows past dates with `min={todayStr}` and provides one-click quick chips (`Today`, `Tomorrow`, `This Weekend`, `+1 Week`).
- **Dynamic Headings**: Rotating destination queries with zero static hardcoding.
- **Conversational Clarification**: When an ambiguous query (e.g., `"ghar"`) is submitted, a dedicated clarification card appears with helpful prompts and one-click corridor suggestions.
- **Optimized Ratio**: Widened route and AI insights panel (62–65% desktop width) with a compact, sticky India overview map (35–38% desktop width).

---

## 🛠️ Development & Production Build

```bash
# Install dependencies
npm install

# Start development server
npm run dev -- --port 3000 --host

# Build for production (TypeScript check + Vite bundle)
npm run build
```
Production build compiles cleanly in **< 900 ms** with zero errors.
