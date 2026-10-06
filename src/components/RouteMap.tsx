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

// Map Bounds Controller
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

// Map View & Hover Interaction Controller
function MapInteractionController({
  stations,
  routeStationMap,
  onHover,
  onZoomChange,
}: {
  stations: StationGeo[];
  routeStationMap: Map<string, StationGeo>;
  onHover: (s: StationGeo | null, pos: { x: number; y: number } | null) => void;
  onZoomChange: (z: number) => void;
}) {
  const map = useMap();

  useEffect(() => {
    onZoomChange(map.getZoom());

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

    const handleZoomEnd = () => {
      onZoomChange(map.getZoom());
    };

    map.on('mousemove', handleMouseMove);
    map.on('zoomend', handleZoomEnd);
    map.on('mouseout', () => onHover(null, null));

    return () => {
      map.off('mousemove', handleMouseMove);
      map.off('zoomend', handleZoomEnd);
      map.off('mouseout', () => onHover(null, null));
    };
  }, [map, stations, routeStationMap, onHover, onZoomChange]);

  return null;
}

// High-Performance HTML5 Canvas Station Dot Renderer (60 FPS for 8,697 stations)
function StationCanvasLayer({
  stations,
  routeStationMap,
  hoveredStation,
  canvasRef,
}: {
  stations: StationGeo[];
  routeStationMap: Map<string, StationGeo>;
  hoveredStation: StationGeo | null;
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
}) {
  const map = useMap();

  const redraw = useCallback(() => {
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
    }

    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const zoom = map.getZoom();
    const bounds = map.getBounds();
    const south = bounds.getSouth() - 0.2;
    const north = bounds.getNorth() + 0.2;
    const west = bounds.getWest() - 0.2;
    const east = bounds.getEast() + 0.2;

    const showCityLabels = zoom >= 7;

    // 1. Render all non-route stations as equal-sized dots matching the reference image teal palette
    const baseRadius = zoom < 7 ? 2.2 : 2.7;
    ctx.fillStyle = '#3E7E6F';

    for (let i = 0; i < stations.length; i++) {
      const s = stations[i];
      if (s.lat >= south && s.lat <= north && s.lon >= west && s.lon <= east) {
        if (!routeStationMap.has(s.c)) {
          const pt = map.latLngToContainerPoint([s.lat, s.lon]);
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, baseRadius, 0, Math.PI * 2);
          ctx.fill();

          // As user zooms in, show city/station names along with the dots
          if (showCityLabels) {
            ctx.font = '500 10.5px Timeless, system-ui, sans-serif';
            ctx.fillStyle = '#1D3528';
            ctx.fillText(s.n, pt.x + 5.5, pt.y + 3.5);
            ctx.fillStyle = '#3E7E6F'; // Restore dot fill
          }
        }
      }
    }

    // 2. Render entire routed sequence through illuminated dots (train & bus)
    for (const s of routeStationMap.values()) {
      const pt = map.latLngToContainerPoint([s.lat, s.lon]);

      if (s.routeRole === 'ORIGIN') {
        // Origin Pin / Dot
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#4A5D30';
        ctx.fill();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = '#FFFFFF';
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#FFFFFF';
        ctx.fill();

        ctx.font = 'bold 12px Timeless, system-ui, sans-serif';
        ctx.fillStyle = '#4A5D30';
        ctx.fillText(`Origin: ${s.n} (${s.c})`, pt.x + 11, pt.y + 4);
      } else if (s.routeRole === 'DESTINATION') {
        // Destination Pin / Dot
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#C05621';
        ctx.fill();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = '#FFFFFF';
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#FFFFFF';
        ctx.fill();

        ctx.font = 'bold 12px Timeless, system-ui, sans-serif';
        ctx.fillStyle = '#C05621';
        ctx.fillText(`Destination: ${s.n} (${s.c})`, pt.x + 11, pt.y + 4);
      } else if (s.routeRole === 'TRANSFER') {
        // Transfer Junction
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 6.5, 0, Math.PI * 2);
        ctx.fillStyle = '#D97706';
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#FFFFFF';
        ctx.stroke();

        ctx.font = 'bold 11px Timeless, system-ui, sans-serif';
        ctx.fillStyle = '#D97706';
        ctx.fillText(`Change: ${s.n}`, pt.x + 9, pt.y + 4);
      } else if (s.routeRole === 'BUS_STOP') {
        // Multimodal Bus Route Dot (Highway Amber)
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 4.5, 0, Math.PI * 2);
        ctx.fillStyle = '#D4A843';
        ctx.fill();
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = '#FFFFFF';
        ctx.stroke();

        if (showCityLabels || zoom >= 6) {
          ctx.font = '600 11px Timeless, system-ui, sans-serif';
          ctx.fillStyle = '#B45309';
          ctx.fillText(s.n, pt.x + 7, pt.y + 3.5);
        }
      } else if (s.routeRole === 'TRAIN_STOP') {
        // Scheduled Timetable Train Stop (Dark Green #4A5D30 with white ring)
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 5.2, 0, Math.PI * 2);
        ctx.fillStyle = '#4A5D30';
        ctx.fill();
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = '#FFFFFF';
        ctx.stroke();

        if (showCityLabels || zoom >= 6) {
          ctx.font = '600 11px Timeless, system-ui, sans-serif';
          ctx.fillStyle = '#1D3528';
          ctx.fillText(s.n, pt.x + 8, pt.y + 3.5);
        }
      } else {
        // TRAIN_CORRIDOR station dot along the line
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 3.8, 0, Math.PI * 2);
        ctx.fillStyle = '#4A5D30';
        ctx.fill();
        ctx.lineWidth = 1;
        ctx.strokeStyle = '#FFFFFF';
        ctx.stroke();

        if (showCityLabels) {
          ctx.font = '500 10px Timeless, system-ui, sans-serif';
          ctx.fillStyle = '#22382D';
          ctx.fillText(s.n, pt.x + 6, pt.y + 3);
        }
      }
    }

    // 3. Hover state: dot gets bigger and glows (radius 7.5px)
    if (hoveredStation) {
      const pt = map.latLngToContainerPoint([hoveredStation.lat, hoveredStation.lon]);
      const isRoute = routeStationMap.has(hoveredStation.c);

      // Outer soft glow ring
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 11, 0, Math.PI * 2);
      ctx.strokeStyle = isRoute ? 'rgba(224, 83, 60, 0.45)' : 'rgba(62, 126, 111, 0.45)';
      ctx.lineWidth = 3;
      ctx.stroke();

      // Enlarged dot
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 7.5, 0, Math.PI * 2);
      ctx.fillStyle = isRoute ? '#E0533C' : '#3E7E6F';
      ctx.fill();
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = '#FFFFFF';
      ctx.stroke();
    }

    ctx.restore();
  }, [map, stations, routeStationMap, hoveredStation, canvasRef]);

  useEffect(() => {
    redraw();
    map.on('move', redraw);
    map.on('zoom', redraw);
    map.on('resize', redraw);
    map.on('viewreset', redraw);

    return () => {
      map.off('move', redraw);
      map.off('zoom', redraw);
      map.off('resize', redraw);
      map.off('viewreset', redraw);
    };
  }, [map, redraw]);

  return null;
}

// Map Controls Component (Zoom +, Zoom -, Whole India, Focus Route)
function CustomMapControls({
  routeCoords,
  onResetIndia,
  onFocusRoute,
}: {
  routeCoords: [number, number][];
  onResetIndia: () => void;
  onFocusRoute: () => void;
}) {
  const map = useMap();

  return (
    <div className="absolute top-4 right-4 z-[500] flex flex-col gap-2 font-['Timeless']">
      <div className="flex flex-col bg-[#F6F0E6] rounded-xl shadow-lg border border-[#4A5D30]/25 overflow-hidden">
        <button
          type="button"
          onClick={() => map.zoomIn()}
          className="w-8 h-8 flex items-center justify-center text-[#4A5D30] font-bold text-lg hover:bg-[#E5D5BF] transition-colors border-b border-[#4A5D30]/15 cursor-pointer"
          title="Zoom In"
        >
          +
        </button>
        <button
          type="button"
          onClick={() => map.zoomOut()}
          className="w-8 h-8 flex items-center justify-center text-[#4A5D30] font-bold text-lg hover:bg-[#E5D5BF] transition-colors cursor-pointer"
          title="Zoom Out"
        >
          −
        </button>
      </div>

      <button
        type="button"
        onClick={onResetIndia}
        className="px-3 py-1.5 bg-[#F6F0E6] hover:bg-[#E5D5BF] text-[#4A5D30] rounded-xl shadow-md border border-[#4A5D30]/25 text-[11px] font-bold tracking-wide transition-colors cursor-pointer"
        title="View All India Station Network"
      >
        Whole India
      </button>

      {routeCoords.length >= 2 && (
        <button
          type="button"
          onClick={onFocusRoute}
          className="px-3 py-1.5 bg-[#4A5D30] hover:bg-[#3D4C27] text-[#F6F0E6] rounded-xl shadow-md text-[11px] font-bold tracking-wide transition-colors cursor-pointer"
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
  const [hoveredStation, setHoveredStation] = useState<StationGeo | null>(null);
  const [hoveredPos, setHoveredPos] = useState<{ x: number; y: number } | null>(null);
  const [currentZoom, setCurrentZoom] = useState<number>(5);
  const mapRef = useRef<L.Map | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // 1. Fetch 8,697 stations & timetable stops
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
  }, []);

  // Quick lookup table for stations by uppercase code
  const stationMap = useMemo(() => {
    const map = new Map<string, StationGeo>();
    stations.forEach((s) => map.set(s.c.toUpperCase(), s));
    return map;
  }, [stations]);

  // 2. Compute the full corridor sequence of dots for both Train and Bus legs
  const { routeStationMap, trainPolylineCoords, busPolylineCoords, allRouteCoords } = useMemo(() => {
    const rMap = new Map<string, StationGeo>();
    const trainCoords: [number, number][] = [];
    const busCoords: [number, number][] = [];
    const allCoords: [number, number][] = [];

    if (stations.length === 0) {
      return { routeStationMap: rMap, trainPolylineCoords: trainCoords, busPolylineCoords: busCoords, allRouteCoords: allCoords };
    }

    // Helper to find corridor stations between two geo points
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

      // Check if train exists in timetable stops
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

      // If scheduled timetable stops exist, interpolate corridor between each stop
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
        // Fallback: corridor stations between from & to
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

      // All cities/towns/stations along the bus highway corridor
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

  return (
    <div className="w-full h-full relative overflow-hidden bg-[#FAF7F2] font-['Timeless']">
      <MapContainer
        center={[22.5, 79.5]}
        zoom={5}
        ref={mapRef}
        className="w-full h-full"
        zoomControl={false}
        style={{ background: '#FAF7F2' }}
      >
        {/* CartoDB Positron No Labels: Minimalist clean geographic backdrop matching reference image */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
          subdomains={['a', 'b', 'c', 'd']}
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          maxZoom={18}
          className="map-clean-canvas"
        />

        {/* Auto-fit map to route on selection */}
        {allRouteCoords.length >= 2 && <MapBoundsUpdater coords={allRouteCoords} />}

        {/* Train Route Polyline: Deep Brand Green (#4A5D30) */}
        {trainPolylineCoords.length >= 2 && (
          <Polyline
            positions={trainPolylineCoords}
            color="#4A5D30"
            weight={4.5}
            opacity={0.95}
          />
        )}

        {/* Bus Route Polyline: Warm Highway Amber (#D4A843) Dashed */}
        {busPolylineCoords.length >= 2 && (
          <Polyline
            positions={busPolylineCoords}
            color="#D4A843"
            weight={4}
            dashArray="8, 8"
            opacity={0.95}
          />
        )}

        {/* High-Performance Canvas Dot Layer for all 8,697 stations & full route sequence */}
        <StationCanvasLayer
          stations={stations}
          routeStationMap={routeStationMap}
          hoveredStation={hoveredStation}
          canvasRef={canvasRef}
        />

        {/* Map Mouse Move & Zoom Level Event Controller */}
        <MapInteractionController
          stations={stations}
          routeStationMap={routeStationMap}
          onHover={(s, pos) => {
            setHoveredStation(s);
            setHoveredPos(pos);
          }}
          onZoomChange={setCurrentZoom}
        />

        {/* Floating Custom Navigation Controls */}
        <CustomMapControls
          routeCoords={allRouteCoords}
          onResetIndia={handleResetIndia}
          onFocusRoute={handleFocusRoute}
        />
      </MapContainer>

      {/* Synchronized Full-Viewport HTML5 Canvas Overlay */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 pointer-events-none z-[400]"
      />

      {/* Station Hover Tooltip: Dot enlarges and city name comes written below */}
      {hoveredStation && hoveredPos && (
        <div
          style={{ left: hoveredPos.x, top: hoveredPos.y + 14 }}
          className="absolute z-[1000] pointer-events-none -translate-x-1/2 bg-[#F6F0E6] text-[#111111] px-3.5 py-2 rounded-xl shadow-xl border border-[#4A5D30]/35 text-xs font-['Timeless'] whitespace-nowrap animate-in fade-in duration-100 flex flex-col items-center"
        >
          <div className="font-bold text-[13px] text-[#4A5D30] tracking-wide flex items-center gap-1.5">
            {hoveredStation.n}
            <span className="text-[11px] font-semibold px-1.5 py-0.5 rounded bg-[#4A5D30]/15 text-[#4A5D30]">
              {hoveredStation.c}
            </span>
          </div>
          {hoveredStation.routeRole && (
            <div className="text-[11px] font-medium text-stone-700 mt-0.5 flex items-center gap-1">
              {hoveredStation.routeRole === 'ORIGIN' && <span className="text-emerald-700 font-bold">Origin Station</span>}
              {hoveredStation.routeRole === 'DESTINATION' && <span className="text-amber-800 font-bold">Destination Station</span>}
              {hoveredStation.routeRole === 'TRANSFER' && <span className="text-amber-700 font-bold">Change Station</span>}
              {hoveredStation.routeRole === 'TRAIN_STOP' && <span className="text-[#4A5D30] font-semibold">Scheduled Train Stop</span>}
              {hoveredStation.routeRole === 'TRAIN_CORRIDOR' && <span className="text-[#4A5D30]/85">Railway Corridor Station</span>}
              {hoveredStation.routeRole === 'BUS_STOP' && <span className="text-[#B45309] font-semibold">Bus Stop</span>}
            </div>
          )}
        </div>
      )}

      {/* Top-Left Metadata Badge */}
      <div className="absolute top-4 left-4 z-[450] bg-[#F6F0E6]/95 backdrop-blur-md px-3.5 py-2 rounded-xl shadow-md border border-[#4A5D30]/25 text-xs font-['Timeless'] text-[#4A5D30] flex items-center gap-2">
        <span className="w-2.5 h-2.5 rounded-full bg-[#3E7E6F] animate-pulse" />
        <span className="font-bold">
          {stations.length > 0 ? `${stations.length.toLocaleString()} Stations` : 'Loading stations...'}
        </span>
        <span className="text-stone-400">·</span>
        <span className="text-stone-600 font-medium">
          {currentZoom >= 7 ? 'City names visible' : 'Zoom in for city names'}
        </span>
      </div>

      {/* Bottom-Left Interactive Legend Bar */}
      <div className="absolute bottom-4 left-4 z-[450] bg-[#F6F0E6]/95 backdrop-blur-md px-3.5 py-2 rounded-xl shadow-md border border-[#4A5D30]/25 text-xs font-['Timeless'] text-stone-700 flex items-center gap-3">
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2.5 h-2.5 rounded-full bg-[#4A5D30] border border-white" /> Origin / Dest
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-3.5 h-1 bg-[#4A5D30] rounded-xs" /> Train Route
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-3.5 h-1 bg-[#D4A843] border-b border-dashed border-[#D4A843]" /> Bus Leg
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2 h-2 rounded-full bg-[#3E7E6F]" /> Station Dot
        </span>
      </div>
    </div>
  );
}
