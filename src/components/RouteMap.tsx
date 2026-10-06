import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export interface StationGeo {
  c: string; // Station code (e.g. NDLS)
  n: string; // Station name (e.g. New Delhi)
  lat: number;
  lon: number;
  routeRole?: 'ORIGIN' | 'DESTINATION' | 'TRANSFER' | 'TRAIN_STOP' | 'TRAIN_CORRIDOR' | 'BUS_STOP';
  trainNumber?: string;
  busOperator?: string;
}

interface Props {
  origin?: string;
  destination?: string;
  legs?: Array<{
    train_number?: string;
    train_name?: string;
    from_station: string;
    from_station_name: string;
    to_station: string;
    to_station_name: string;
    from_lat?: number | null;
    from_lon?: number | null;
    to_lat?: number | null;
    to_lon?: number | null;
  }>;
  busLegs?: Array<{
    operator_name?: string;
    operator_code?: string;
    from_station_code: string;
    from_terminal: string;
    to_station_code: string;
    to_terminal: string;
    from_lat?: number | null;
    from_lon?: number | null;
    to_lat?: number | null;
    to_lon?: number | null;
  }>;
}

// Distance from point P to segment AB in km
function distancePointToSegmentKm(
  pLat: number,
  pLon: number,
  aLat: number,
  aLon: number,
  bLat: number,
  bLon: number
): { distKm: number; t: number } {
  const dx = bLon - aLon;
  const dy = bLat - aLat;
  const l2 = dx * dx + dy * dy;
  if (l2 === 0) {
    const dLat = (pLat - aLat) * 111;
    const dLon = (pLon - aLon) * 85;
    return { distKm: Math.sqrt(dLat * dLat + dLon * dLon), t: 0 };
  }
  const t = Math.max(0, Math.min(1, ((pLon - aLon) * dx + (pLat - aLat) * dy) / l2));
  const projLon = aLon + t * dx;
  const projLat = aLat + t * dy;
  const dLat = (pLat - projLat) * 111;
  const dLon = (pLon - projLon) * 85;
  return { distKm: Math.sqrt(dLat * dLat + dLon * dLon), t };
}

// Map Bounds Controller for active routes
function MapBoundsUpdater({ coords }: { coords: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    if (coords.length >= 2) {
      map.fitBounds(coords, { padding: [55, 55], maxZoom: 10 });
    } else if (coords.length === 1) {
      map.setView(coords[0], 7);
    }
  }, [coords, map]);
  return null;
}

// Unified Canvas Layer:
// 1. India Boundary Masking (Solid black background outside India using 'evenodd' fill rule)
// 2. Interactive Background Animation (Uniform grid of solid circles with trailing empty path)
// 3. Station dots & route illumination inside India
function UnifiedMapCanvasLayer({
  stations,
  routeStationMap,
  hoveredStation,
  indiaCoords,
  mousePos,
  onHover,
  onZoomChange,
  canvasRef,
}: {
  stations: StationGeo[];
  routeStationMap: Map<string, StationGeo>;
  hoveredStation: StationGeo | null;
  indiaCoords: number[][][][] | null;
  mousePos: { x: number; y: number } | null;
  onHover: (s: StationGeo | null, pos: { x: number; y: number } | null) => void;
  onZoomChange: (z: number) => void;
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
}) {
  const map = useMap();
  const cachedRingsRef = useRef<Array<Array<{ x: number; y: number }>>>([]);
  const dotScalesRef = useRef<Float32Array>(new Float32Array(0));
  const gridDimsRef = useRef<{ cols: number; rows: number }>({ cols: 0, rows: 0 });
  const animFrameIdRef = useRef<number | null>(null);

  // Sync projected India boundary rings when map moves/zooms
  const updateProjectedRings = useCallback(() => {
    if (!indiaCoords) return;
    const rings: Array<Array<{ x: number; y: number }>> = [];
    for (let i = 0; i < indiaCoords.length; i++) {
      const poly = indiaCoords[i];
      for (let j = 0; j < poly.length; j++) {
        const ring = poly[j];
        if (ring.length < 3) continue;
        const screenRing: Array<{ x: number; y: number }> = [];
        for (let k = 0; k < ring.length; k++) {
          const [lon, lat] = ring[k];
          const pt = map.latLngToContainerPoint([lat, lon]);
          screenRing.push(pt);
        }
        rings.push(screenRing);
      }
    }
    cachedRingsRef.current = rings;
  }, [indiaCoords, map]);

  // Initial and reactive projection update
  useEffect(() => {
    updateProjectedRings();
    onZoomChange(map.getZoom());

    const handleMove = () => updateProjectedRings();
    const handleZoomEnd = () => {
      updateProjectedRings();
      onZoomChange(map.getZoom());
    };

    map.on('move', handleMove);
    map.on('zoom', updateProjectedRings);
    map.on('zoomend', handleZoomEnd);
    map.on('resize', updateProjectedRings);
    map.on('viewreset', updateProjectedRings);

    return () => {
      map.off('move', handleMove);
      map.off('zoom', updateProjectedRings);
      map.off('zoomend', handleZoomEnd);
      map.off('resize', updateProjectedRings);
      map.off('viewreset', updateProjectedRings);
    };
  }, [map, updateProjectedRings, onZoomChange]);

  // Mouse move handler for station dot hover
  useEffect(() => {
    const handleMouseMove = (e: L.LeafletMouseEvent) => {
      const mouseX = e.containerPoint.x;
      const mouseY = e.containerPoint.y;
      const bounds = map.getBounds();

      let found: StationGeo | null = null;
      let minDistance = 14;

      // 1. Prioritize route stations (larger hit radius)
      for (const s of routeStationMap.values()) {
        const pt = map.latLngToContainerPoint([s.lat, s.lon]);
        const dist = Math.hypot(pt.x - mouseX, pt.y - mouseY);
        if (dist <= 16) {
          found = s;
          break;
        }
      }

      // 2. If not hovering a route station, check visible network stations
      if (!found) {
        const south = bounds.getSouth() - 0.15;
        const north = bounds.getNorth() + 0.15;
        const west = bounds.getWest() - 0.15;
        const east = bounds.getEast() + 0.15;

        for (let i = 0; i < stations.length; i++) {
          const s = stations[i];
          if (s.lat >= south && s.lat <= north && s.lon >= west && s.lon <= east) {
            const pt = map.latLngToContainerPoint([s.lat, s.lon]);
            const dist = Math.hypot(pt.x - mouseX, pt.y - mouseY);
            if (dist < minDistance) {
              minDistance = dist;
              found = s;
            }
          }
        }
      }

      if (found) {
        map.getContainer().style.cursor = 'pointer';
        const pt = map.latLngToContainerPoint([found.lat, found.lon]);
        onHover(found, { x: pt.x, y: pt.y });
      } else {
        map.getContainer().style.cursor = '';
        onHover(null, null);
      }
    };

    map.on('mousemove', handleMouseMove);
    map.on('mouseout', () => onHover(null, null));

    return () => {
      map.off('mousemove', handleMouseMove);
      map.off('mouseout', () => onHover(null, null));
    };
  }, [map, stations, routeStationMap, onHover]);

  // Main 60 FPS Render Loop
  useEffect(() => {
    const SPACING = 16;
    const BASE_RADIUS = 1.8;
    const HOVER_RADIUS = 75;
    const RECOVERY_SPEED = 0.022; // ~45 frames = ~0.75s to smoothly fade/scale back

    const render = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const size = map.getSize();
      const dpr = window.devicePixelRatio || 1;
      const width = size.x;
      const height = size.y;

      if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        // Resize particle scale array
        const cols = Math.ceil(width / SPACING) + 2;
        const rows = Math.ceil(height / SPACING) + 2;
        gridDimsRef.current = { cols, rows };
        const totalDots = cols * rows;
        const newScales = new Float32Array(totalDots);
        newScales.fill(1.0);
        dotScalesRef.current = newScales;
      }

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, height);

      const rings = cachedRingsRef.current;

      // ---------------------------------------------------------
      // Step 1: Solid Black Background Mask outside India
      // Uses the HTML5 Canvas 'evenodd' fill rule:
      // Outer viewport rect + India boundary rings =
      // 100% black fill outside India, 100% transparent inside India!
      // ---------------------------------------------------------
      if (rings.length > 0) {
        ctx.save();
        ctx.beginPath();
        // Outer rect covering whole map viewport
        ctx.rect(0, 0, width, height);
        // Inner India MultiPolygon boundary rings
        for (let i = 0; i < rings.length; i++) {
          const ring = rings[i];
          if (ring.length < 3) continue;
          ctx.moveTo(ring[0].x, ring[0].y);
          for (let j = 1; j < ring.length; j++) {
            ctx.lineTo(ring[j].x, ring[j].y);
          }
          ctx.closePath();
        }

        ctx.fillStyle = '#000000';
        ctx.fill('evenodd');

        // ---------------------------------------------------------
        // Step 2: Interactive Grid of Circles with Mouse Trail Effect
        // Clipped to outside of India with 'evenodd'!
        // ---------------------------------------------------------
        ctx.clip('evenodd');

        const { cols, rows } = gridDimsRef.current;
        const scales = dotScalesRef.current;
        const curMX = mousePos ? mousePos.x : -9999;
        const curMY = mousePos ? mousePos.y : -9999;

        let dotIdx = 0;
        for (let r = 0; r < rows; r++) {
          const y = r * SPACING;
          for (let c = 0; c < cols; c++) {
            const x = c * SPACING;
            const dist = Math.hypot(x - curMX, y - curMY);

            // Hover interaction: vanish instantly when cursor is near
            if (dist < HOVER_RADIUS) {
              scales[dotIdx] = 0;
            } else if (scales[dotIdx] < 1.0) {
              // Trail effect: slowly fade/scale back to original state
              scales[dotIdx] = Math.min(1.0, scales[dotIdx] + RECOVERY_SPEED);
            }

            const scale = scales[dotIdx];
            if (scale > 0.03) {
              ctx.beginPath();
              ctx.arc(x, y, BASE_RADIUS * scale, 0, Math.PI * 2);
              ctx.fillStyle = `rgba(255, 255, 255, ${0.75 * scale})`;
              ctx.fill();
            }
            dotIdx++;
          }
        }

        ctx.restore(); // Restore clip

        // ---------------------------------------------------------
        // Step 3: Subtle Crisp India Boundary Line
        // ---------------------------------------------------------
        ctx.save();
        ctx.beginPath();
        for (let i = 0; i < rings.length; i++) {
          const ring = rings[i];
          if (ring.length < 3) continue;
          ctx.moveTo(ring[0].x, ring[0].y);
          for (let j = 1; j < ring.length; j++) {
            ctx.lineTo(ring[j].x, ring[j].y);
          }
          ctx.closePath();
        }
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
        ctx.lineWidth = 1.3;
        ctx.stroke();
        ctx.restore();
      }

      // ---------------------------------------------------------
      // Step 4: Render Station Dots & Routes Inside India
      // ---------------------------------------------------------
      const zoom = map.getZoom();
      const bounds = map.getBounds();
      const south = bounds.getSouth() - 0.2;
      const north = bounds.getNorth() + 0.2;
      const west = bounds.getWest() - 0.2;
      const east = bounds.getEast() + 0.2;
      const showCityLabels = zoom >= 7;

      // A. All Non-route Stations: equal-sized dots matching teal palette
      const baseRadius = zoom < 7 ? 2.2 : 2.7;
      ctx.fillStyle = '#10B981'; // Bright emerald/teal that stands out over satellite terrain

      for (let i = 0; i < stations.length; i++) {
        const s = stations[i];
        if (s.lat >= south && s.lat <= north && s.lon >= west && s.lon <= east) {
          if (!routeStationMap.has(s.c)) {
            const pt = map.latLngToContainerPoint([s.lat, s.lon]);
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, baseRadius, 0, Math.PI * 2);
            ctx.fill();

            // Zoom-in reveals city/station name with dark halo for readability
            if (showCityLabels) {
              ctx.save();
              ctx.font = 'bold 11px Timeless, system-ui, sans-serif';
              ctx.shadowColor = '#000000';
              ctx.shadowBlur = 3;
              ctx.fillStyle = '#FFFFFF';
              ctx.fillText(s.n, pt.x + 5.5, pt.y + 3.5);
              ctx.restore();
              ctx.fillStyle = '#10B981';
            }
          }
        }
      }

      // B. Entire Routed Sequence (Origin, Destination, Timetable & Corridor Stops)
      for (const s of routeStationMap.values()) {
        const pt = map.latLngToContainerPoint([s.lat, s.lon]);

        if (s.routeRole === 'ORIGIN') {
          // Google Maps Origin: Blue Circle Marker with White Center
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 8.5, 0, Math.PI * 2);
          ctx.fillStyle = '#1A73E8';
          ctx.fill();
          ctx.lineWidth = 2.5;
          ctx.strokeStyle = '#FFFFFF';
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 3.5, 0, Math.PI * 2);
          ctx.fillStyle = '#FFFFFF';
          ctx.fill();

          ctx.save();
          ctx.font = 'bold 12.5px Timeless, system-ui, sans-serif';
          ctx.shadowColor = '#000000';
          ctx.shadowBlur = 4;
          ctx.fillStyle = '#FFFFFF';
          ctx.fillText(`Origin: ${s.n} (${s.c})`, pt.x + 12, pt.y + 4.5);
          ctx.restore();
        } else if (s.routeRole === 'DESTINATION') {
          // Google Maps Destination: Red Pin Marker with White Center
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 8.5, 0, Math.PI * 2);
          ctx.fillStyle = '#EA4335';
          ctx.fill();
          ctx.lineWidth = 2.5;
          ctx.strokeStyle = '#FFFFFF';
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 3.5, 0, Math.PI * 2);
          ctx.fillStyle = '#FFFFFF';
          ctx.fill();

          ctx.save();
          ctx.font = 'bold 12.5px Timeless, system-ui, sans-serif';
          ctx.shadowColor = '#000000';
          ctx.shadowBlur = 4;
          ctx.fillStyle = '#FFFFFF';
          ctx.fillText(`Destination: ${s.n} (${s.c})`, pt.x + 12, pt.y + 4.5);
          ctx.restore();
        } else if (s.routeRole === 'TRANSFER') {
          // Transfer Junction (Vibrant Amber)
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 6.5, 0, Math.PI * 2);
          ctx.fillStyle = '#F59E0B';
          ctx.fill();
          ctx.lineWidth = 2;
          ctx.strokeStyle = '#FFFFFF';
          ctx.stroke();

          ctx.save();
          ctx.font = 'bold 11px Timeless, system-ui, sans-serif';
          ctx.shadowColor = '#000000';
          ctx.shadowBlur = 3;
          ctx.fillStyle = '#FBBF24';
          ctx.fillText(`Change: ${s.n}`, pt.x + 9, pt.y + 4);
          ctx.restore();
        } else if (s.routeRole === 'BUS_STOP') {
          // Bus Stop (Highway Amber)
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 4.5, 0, Math.PI * 2);
          ctx.fillStyle = '#F59E0B';
          ctx.fill();
          ctx.lineWidth = 1.5;
          ctx.strokeStyle = '#FFFFFF';
          ctx.stroke();

          if (showCityLabels || zoom >= 6) {
            ctx.save();
            ctx.font = '600 11px Timeless, system-ui, sans-serif';
            ctx.shadowColor = '#000000';
            ctx.shadowBlur = 3;
            ctx.fillStyle = '#FDE68A';
            ctx.fillText(s.n, pt.x + 7, pt.y + 3.5);
            ctx.restore();
          }
        } else if (s.routeRole === 'TRAIN_STOP') {
          // Scheduled Timetable Train Stop (Vibrant Blue with white ring)
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 5.5, 0, Math.PI * 2);
          ctx.fillStyle = '#1A73E8';
          ctx.fill();
          ctx.lineWidth = 1.5;
          ctx.strokeStyle = '#FFFFFF';
          ctx.stroke();

          if (showCityLabels || zoom >= 6) {
            ctx.save();
            ctx.font = 'bold 11px Timeless, system-ui, sans-serif';
            ctx.shadowColor = '#000000';
            ctx.shadowBlur = 3;
            ctx.fillStyle = '#FFFFFF';
            ctx.fillText(s.n, pt.x + 8, pt.y + 3.5);
            ctx.restore();
          }
        } else {
          // Railway Corridor Dot along the line
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 3.8, 0, Math.PI * 2);
          ctx.fillStyle = '#38BDF8';
          ctx.fill();
          ctx.lineWidth = 1;
          ctx.strokeStyle = '#FFFFFF';
          ctx.stroke();

          if (showCityLabels) {
            ctx.save();
            ctx.font = '500 10px Timeless, system-ui, sans-serif';
            ctx.shadowColor = '#000000';
            ctx.shadowBlur = 3;
            ctx.fillStyle = '#E0F2FE';
            ctx.fillText(s.n, pt.x + 6, pt.y + 3);
            ctx.restore();
          }
        }
      }

      // C. Hover state: Dot enlarges and glows, city name written below!
      if (hoveredStation) {
        const pt = map.latLngToContainerPoint([hoveredStation.lat, hoveredStation.lon]);
        const isRoute = routeStationMap.has(hoveredStation.c);

        // Soft outer glow ring
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 12, 0, Math.PI * 2);
        ctx.strokeStyle = isRoute ? 'rgba(234, 67, 53, 0.55)' : 'rgba(16, 185, 129, 0.55)';
        ctx.lineWidth = 3.5;
        ctx.stroke();

        // Enlarged dot
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2);
        ctx.fillStyle = isRoute ? '#EA4335' : '#10B981';
        ctx.fill();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = '#FFFFFF';
        ctx.stroke();

        // City name written below dot with strong contrast halo
        ctx.save();
        ctx.font = 'bold 12px Timeless, system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.shadowColor = '#000000';
        ctx.shadowBlur = 4;
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(`${hoveredStation.n} (${hoveredStation.c})`, pt.x, pt.y + 22);
        ctx.restore();
      }

      ctx.restore();
      animFrameIdRef.current = requestAnimationFrame(render);
    };

    animFrameIdRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameIdRef.current != null) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, [map, stations, routeStationMap, hoveredStation, mousePos, canvasRef]);

  return null;
}

// Map Controls (Zoom +, Zoom -, Whole India, Focus Route, Satellite/Map layer toggle)
function CustomMapControls({
  routeCoords,
  mapType,
  onToggleMapType,
  onResetIndia,
  onFocusRoute,
}: {
  routeCoords: [number, number][];
  mapType: 'satellite' | 'street';
  onToggleMapType: () => void;
  onResetIndia: () => void;
  onFocusRoute: () => void;
}) {
  const map = useMap();

  return (
    <div className="absolute top-4 right-4 z-[500] flex flex-col gap-2 font-['Timeless']">
      <div className="flex flex-col bg-black/80 backdrop-blur-md rounded-xl shadow-xl border border-white/20 overflow-hidden text-white">
        <button
          type="button"
          onClick={() => map.zoomIn()}
          className="w-8 h-8 flex items-center justify-center text-white font-bold text-lg hover:bg-white/15 transition-colors border-b border-white/15 cursor-pointer"
          title="Zoom In"
        >
          +
        </button>
        <button
          type="button"
          onClick={() => map.zoomOut()}
          className="w-8 h-8 flex items-center justify-center text-white font-bold text-lg hover:bg-white/15 transition-colors cursor-pointer"
          title="Zoom Out"
        >
          −
        </button>
      </div>

      <button
        type="button"
        onClick={onToggleMapType}
        className="px-3 py-1.5 bg-black/80 hover:bg-black/95 text-white backdrop-blur-md rounded-xl shadow-xl border border-white/20 text-[11px] font-bold tracking-wide transition-all cursor-pointer flex items-center justify-center gap-1.5"
        title="Toggle Map Style"
      >
        <span>{mapType === 'satellite' ? '🛰 Satellite' : '🗺 Street'}</span>
      </button>

      <button
        type="button"
        onClick={onResetIndia}
        className="px-3 py-1.5 bg-black/80 hover:bg-black/95 text-white backdrop-blur-md rounded-xl shadow-xl border border-white/20 text-[11px] font-bold tracking-wide transition-all cursor-pointer"
        title="View All India"
      >
        Whole India
      </button>

      {routeCoords.length >= 2 && (
        <button
          type="button"
          onClick={onFocusRoute}
          className="px-3 py-1.5 bg-[#1A73E8] hover:bg-[#1557B0] text-white rounded-xl shadow-xl text-[11px] font-bold tracking-wide transition-all cursor-pointer border border-blue-400/40"
          title="Focus on Active Route Corridor"
        >
          Focus Route
        </button>
      )}
    </div>
  );
}

export default function RouteMap({ legs = [], busLegs = [] }: Props) {
  const [stations, setStations] = useState<StationGeo[]>([]);
  const [trainStops, setTrainStops] = useState<Record<string, string[]>>({});
  const [indiaCoords, setIndiaCoords] = useState<number[][][][] | null>(null);
  const [hoveredStation, setHoveredStation] = useState<StationGeo | null>(null);
  const [hoveredPos, setHoveredPos] = useState<{ x: number; y: number } | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
  const [currentZoom, setCurrentZoom] = useState<number>(5);
  const [mapType, setMapType] = useState<'satellite' | 'street'>('satellite');

  const mapRef = useRef<L.Map | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // 1. Fetch 8,697 stations, timetable stops & India boundary GeoJSON
  useEffect(() => {
    fetch('/data/stations_geo.json')
      .then((r) => r.json())
      .then((data: StationGeo[]) => {
        if (Array.isArray(data)) setStations(data);
      })
      .catch((err) => console.error('Failed to load stations_geo.json', err));

    fetch('/data/train_stops.json')
      .then((r) => r.json())
      .then((data: Record<string, string[]>) => {
        if (data && typeof data === 'object') setTrainStops(data);
      })
      .catch((err) => console.error('Failed to load train_stops.json', err));

    fetch('/data/india_boundary.json')
      .then((r) => r.json())
      .then((data) => {
        if (data?.features?.[0]?.geometry?.coordinates) {
          setIndiaCoords(data.features[0].geometry.coordinates);
        }
      })
      .catch((err) => console.error('Failed to load india_boundary.json', err));
  }, []);

  // Station lookup table
  const stationMap = useMemo(() => {
    const map = new Map<string, StationGeo>();
    stations.forEach((s) => map.set(s.c.toUpperCase(), s));
    return map;
  }, [stations]);

  // 2. Compute full corridor sequence of dots for both Train and Bus legs
  const { routeStationMap, trainPolylineCoords, busPolylineCoords, allRouteCoords } = useMemo(() => {
    const rMap = new Map<string, StationGeo>();
    const trainCoords: [number, number][] = [];
    const busCoords: [number, number][] = [];
    const allCoords: [number, number][] = [];

    if (stations.length === 0) {
      return { routeStationMap: rMap, trainPolylineCoords: trainCoords, busPolylineCoords: busCoords, allRouteCoords: allCoords };
    }

    const findCorridorStations = (
      fromLat: number,
      fromLon: number,
      toLat: number,
      toLon: number,
      bufferKm: number = 14
    ) => {
      const candidates: Array<{ t: number; station: StationGeo }> = [];
      stations.forEach((s) => {
        const { distKm, t } = distancePointToSegmentKm(s.lat, s.lon, fromLat, fromLon, toLat, toLon);
        if (distKm <= bufferKm && t >= 0 && t <= 1) {
          candidates.push({ t, station: s });
        }
      });
      candidates.sort((a, b) => a.t - b.t);
      return candidates.map((c) => c.station);
    };

    // A. Process Train Legs
    legs.forEach((leg, legIdx) => {
      const fromCode = leg.from_station.toUpperCase();
      const toCode = leg.to_station.toUpperCase();
      const fromSt = stationMap.get(fromCode);
      const toSt = stationMap.get(toCode);

      const fLat = leg.from_lat ?? fromSt?.lat;
      const fLon = leg.from_lon ?? fromSt?.lon;
      const tLat = leg.to_lat ?? toSt?.lat;
      const tLon = leg.to_lon ?? toSt?.lon;

      if (fLat == null || fLon == null || tLat == null || tLon == null) return;

      const tNum = (leg.train_number || '').trim();
      const stops = trainStops[tNum];
      let timetableStops: StationGeo[] = [];

      if (stops && stops.length > 0) {
        const fromIdx = stops.indexOf(fromCode);
        const toIdx = stops.indexOf(toCode);
        if (fromIdx >= 0 && toIdx >= 0) {
          const minIdx = Math.min(fromIdx, toIdx);
          const maxIdx = Math.max(fromIdx, toIdx);
          const subStops = stops.slice(minIdx, maxIdx + 1);
          if (fromIdx > toIdx) subStops.reverse();

          timetableStops = subStops
            .map((code) => stationMap.get(code))
            .filter((s): s is StationGeo => s != null);
        }
      }

      if (timetableStops.length >= 2) {
        timetableStops.forEach((st, i) => {
          rMap.set(st.c, {
            ...st,
            routeRole: i === 0 && legIdx === 0 ? 'ORIGIN' : i === timetableStops.length - 1 && legIdx === legs.length - 1 && busLegs.length === 0 ? 'DESTINATION' : 'TRAIN_STOP',
            trainNumber: tNum,
          });

          if (i === 0 && (legIdx === 0 || trainCoords.length === 0)) {
            trainCoords.push([st.lat, st.lon]);
            allCoords.push([st.lat, st.lon]);
          }

          if (i < timetableStops.length - 1) {
            const nextSt = timetableStops[i + 1];
            const intermediate = findCorridorStations(st.lat, st.lon, nextSt.lat, nextSt.lon, 10);
            intermediate.forEach((inter) => {
              if (!rMap.has(inter.c)) {
                rMap.set(inter.c, { ...inter, routeRole: 'TRAIN_CORRIDOR', trainNumber: tNum });
                trainCoords.push([inter.lat, inter.lon]);
                allCoords.push([inter.lat, inter.lon]);
              }
            });
            trainCoords.push([nextSt.lat, nextSt.lon]);
            allCoords.push([nextSt.lat, nextSt.lon]);
          }
        });
      } else {
        if (fromSt) {
          rMap.set(fromSt.c, {
            ...fromSt,
            routeRole: legIdx === 0 ? 'ORIGIN' : 'TRAIN_STOP',
            trainNumber: tNum,
          });
          trainCoords.push([fLat, fLon]);
          allCoords.push([fLat, fLon]);
        }

        const corridor = findCorridorStations(fLat, fLon, tLat, tLon, 14);
        corridor.forEach((s) => {
          if (!rMap.has(s.c)) {
            rMap.set(s.c, { ...s, routeRole: 'TRAIN_CORRIDOR', trainNumber: tNum });
            trainCoords.push([s.lat, s.lon]);
            allCoords.push([s.lat, s.lon]);
          }
        });

        if (toSt) {
          rMap.set(toSt.c, {
            ...toSt,
            routeRole: legIdx === legs.length - 1 && busLegs.length === 0 ? 'DESTINATION' : 'TRANSFER',
            trainNumber: tNum,
          });
          trainCoords.push([tLat, tLon]);
          allCoords.push([tLat, tLon]);
        }
      }
    });

    // B. Process Bus Legs
    busLegs.forEach((bus, bIdx) => {
      const fromCode = bus.from_station_code.toUpperCase();
      const toCode = bus.to_station_code.toUpperCase();
      const fromSt = stationMap.get(fromCode);
      const toSt = stationMap.get(toCode);

      const fLat = bus.from_lat ?? fromSt?.lat;
      const fLon = bus.from_lon ?? fromSt?.lon;
      const tLat = bus.to_lat ?? toSt?.lat;
      const tLon = bus.to_lon ?? toSt?.lon;

      if (fLat == null || fLon == null || tLat == null || tLon == null) return;

      if (fromSt) {
        rMap.set(fromSt.c, {
          ...fromSt,
          routeRole: legs.length === 0 && bIdx === 0 ? 'ORIGIN' : 'TRANSFER',
          busOperator: bus.operator_name,
        });
      }
      busCoords.push([fLat, fLon]);
      allCoords.push([fLat, fLon]);

      const busCorridor = findCorridorStations(fLat, fLon, tLat, tLon, 16);
      busCorridor.forEach((s) => {
        if (!rMap.has(s.c)) {
          rMap.set(s.c, {
            ...s,
            routeRole: 'BUS_STOP',
            busOperator: bus.operator_name,
          });
          busCoords.push([s.lat, s.lon]);
          allCoords.push([s.lat, s.lon]);
        }
      });

      if (toSt) {
        rMap.set(toSt.c, {
          ...toSt,
          routeRole: bIdx === busLegs.length - 1 ? 'DESTINATION' : 'TRANSFER',
          busOperator: bus.operator_name,
        });
      }
      busCoords.push([tLat, tLon]);
      allCoords.push([tLat, tLon]);
    });

    return { routeStationMap: rMap, trainPolylineCoords: trainCoords, busPolylineCoords: busCoords, allRouteCoords: allCoords };
  }, [stations, trainStops, stationMap, legs, busLegs]);

  const handleResetIndia = useCallback(() => {
    if (mapRef.current) {
      mapRef.current.setView([22.5, 79.5], 5);
    }
  }, []);

  const handleFocusRoute = useCallback(() => {
    if (mapRef.current && allRouteCoords.length >= 2) {
      mapRef.current.fitBounds(allRouteCoords, { padding: [55, 55], maxZoom: 10 });
    }
  }, [allRouteCoords]);

  // Track mouse coordinates across the map viewport for interactive trailing animation
  const handleContainerMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const handleContainerMouseLeave = () => {
    setMousePos(null);
    setHoveredStation(null);
    setHoveredPos(null);
  };

  return (
    <div
      onMouseMove={handleContainerMouseMove}
      onMouseLeave={handleContainerMouseLeave}
      className="w-full h-full relative overflow-hidden bg-black font-['Timeless'] select-none"
    >
      <MapContainer
        center={[22.5, 79.5]}
        zoom={5}
        minZoom={4}
        maxZoom={18}
        ref={mapRef}
        className="w-full h-full"
        zoomControl={false}
        style={{ background: '#000000' }}
      >
        {/* Google Maps Layer (Satellite Hybrid / Street) */}
        <TileLayer
          url={
            mapType === 'satellite'
              ? 'https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'
              : 'https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
          }
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution='&copy; Google Maps'
          maxZoom={20}
        />

        {/* Auto-fit map to route on selection */}
        {allRouteCoords.length >= 2 && <MapBoundsUpdater coords={allRouteCoords} />}

        {/* Train Route Polyline: Google Transit Blue (#1A73E8) with white contrast casing */}
        {trainPolylineCoords.length >= 2 && (
          <>
            <Polyline
              positions={trainPolylineCoords}
              color="#FFFFFF"
              weight={7}
              opacity={0.85}
            />
            <Polyline
              positions={trainPolylineCoords}
              color="#1A73E8"
              weight={4.5}
              opacity={1}
            />
          </>
        )}

        {/* Bus Route Polyline: Warm Highway Amber (#F59E0B) Dashed */}
        {busPolylineCoords.length >= 2 && (
          <Polyline
            positions={busPolylineCoords}
            color="#F59E0B"
            weight={4}
            dashArray="8, 8"
            opacity={0.95}
          />
        )}

        {/* Unified Canvas Layer (Black Background Mask outside India + Interactive Trail Animation + Station Dots) */}
        <UnifiedMapCanvasLayer
          stations={stations}
          routeStationMap={routeStationMap}
          hoveredStation={hoveredStation}
          indiaCoords={indiaCoords}
          mousePos={mousePos}
          onHover={(s, pos) => {
            setHoveredStation(s);
            setHoveredPos(pos);
          }}
          onZoomChange={setCurrentZoom}
          canvasRef={canvasRef}
        />

        {/* Floating Custom Navigation Controls */}
        <CustomMapControls
          routeCoords={allRouteCoords}
          mapType={mapType}
          onToggleMapType={() => setMapType((prev) => (prev === 'satellite' ? 'street' : 'satellite'))}
          onResetIndia={handleResetIndia}
          onFocusRoute={handleFocusRoute}
        />
      </MapContainer>

      {/* Synchronized Full-Viewport HTML5 Canvas Overlay */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 pointer-events-none z-[400]"
      />

      {/* Station Hover Tooltip Badge */}
      {hoveredStation && hoveredPos && (
        <div
          style={{ left: hoveredPos.x, top: hoveredPos.y + 14 }}
          className="absolute z-[1000] pointer-events-none -translate-x-1/2 bg-black/90 text-white px-3.5 py-2 rounded-xl shadow-2xl border border-white/25 text-xs font-['Timeless'] whitespace-nowrap animate-in fade-in duration-100 flex flex-col items-center backdrop-blur-md"
        >
          <div className="font-bold text-[13px] text-white tracking-wide flex items-center gap-1.5">
            {hoveredStation.n}
            <span className="text-[11px] font-semibold px-1.5 py-0.5 rounded bg-white/20 text-white">
              {hoveredStation.c}
            </span>
          </div>
          {hoveredStation.routeRole && (
            <div className="text-[11px] font-medium text-stone-300 mt-0.5 flex items-center gap-1">
              {hoveredStation.routeRole === 'ORIGIN' && <span className="text-blue-400 font-bold">Origin Station</span>}
              {hoveredStation.routeRole === 'DESTINATION' && <span className="text-rose-400 font-bold">Destination Station</span>}
              {hoveredStation.routeRole === 'TRANSFER' && <span className="text-amber-400 font-bold">Change Station</span>}
              {hoveredStation.routeRole === 'TRAIN_STOP' && <span className="text-emerald-400 font-semibold">Scheduled Train Stop</span>}
              {hoveredStation.routeRole === 'TRAIN_CORRIDOR' && <span className="text-sky-300 font-medium">Railway Corridor</span>}
              {hoveredStation.routeRole === 'BUS_STOP' && <span className="text-amber-300 font-semibold">Bus Stop</span>}
            </div>
          )}
        </div>
      )}

      {/* Top-Left Metadata Badge */}
      <div className="absolute top-4 left-4 z-[450] bg-black/80 backdrop-blur-md px-3.5 py-2 rounded-xl shadow-xl border border-white/20 text-xs font-['Timeless'] text-white flex items-center gap-2">
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
        <span className="font-bold">
          {stations.length > 0 ? `${stations.length.toLocaleString()} Stations` : 'Loading stations...'}
        </span>
        <span className="text-stone-500">·</span>
        <span className="text-stone-300 font-medium">
          {currentZoom >= 7 ? 'City names visible' : 'Zoom in for city names'}
        </span>
      </div>

      {/* Bottom-Left Interactive Legend Bar */}
      <div className="absolute bottom-4 left-4 z-[450] bg-black/80 backdrop-blur-md px-3.5 py-2 rounded-xl shadow-xl border border-white/20 text-xs font-['Timeless'] text-stone-200 flex items-center gap-3">
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2.5 h-2.5 rounded-full bg-[#1A73E8] border border-white" /> Origin
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2.5 h-2.5 rounded-full bg-[#EA4335] border border-white" /> Dest
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-3.5 h-1 bg-[#1A73E8] rounded-xs" /> Train Route
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-3.5 h-1 bg-[#F59E0B] border-b border-dashed border-[#F59E0B]" /> Bus Leg
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2 h-2 rounded-full bg-[#10B981]" /> Station Dot
        </span>
      </div>
    </div>
  );
}
