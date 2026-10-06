import { useEffect, useState, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Marker, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export interface RouteStation {
  c: string; // Station code (e.g. NDLS)
  n: string; // Station name (e.g. New Delhi)
  lat: number;
  lon: number;
  routeRole: 'ORIGIN' | 'DESTINATION' | 'TRANSFER' | 'TRAIN_STOP' | 'BUS_STOP';
  trainNumber?: string;
  busOperator?: string;
}

interface StationGeo {
  c: string;
  n: string;
  lat: number;
  lon: number;
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

// Map Bounds Controller to smoothly focus the active route
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

// Minimalist Google Maps Destination Pin Icon (Classic Red Marker)
const googleDestPinIcon = L.divIcon({
  className: 'google-maps-dest-marker',
  html: `
    <div style="position: relative; width: 28px; height: 36px; transform: translate(-14px, -36px); cursor: pointer; filter: drop-shadow(0 2px 5px rgba(0,0,0,0.3));">
      <svg width="28" height="36" viewBox="0 0 24 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 0C5.37258 0 0 5.37258 0 12C0 21 12 32 12 32C12 32 24 21 24 12C24 5.37258 18.6274 0 12 0Z" fill="#EA4335" stroke="#FFFFFF" stroke-width="1.2"/>
        <circle cx="12" cy="11.5" r="4.5" fill="#FFFFFF"/>
      </svg>
    </div>
  `,
  iconSize: [28, 36],
  iconAnchor: [14, 36],
});

// Floating Minimalist Map Controls
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
      <div className="flex flex-col bg-white rounded-xl shadow-md border border-stone-200 overflow-hidden text-stone-800">
        <button
          type="button"
          onClick={() => map.zoomIn()}
          className="w-8.5 h-8.5 flex items-center justify-center text-stone-700 font-bold text-lg hover:bg-stone-100 transition-colors border-b border-stone-200 cursor-pointer"
          title="Zoom In"
        >
          +
        </button>
        <button
          type="button"
          onClick={() => map.zoomOut()}
          className="w-8.5 h-8.5 flex items-center justify-center text-stone-700 font-bold text-lg hover:bg-stone-100 transition-colors cursor-pointer"
          title="Zoom Out"
        >
          −
        </button>
      </div>

      <button
        type="button"
        onClick={onResetIndia}
        className="px-3 py-1.5 bg-white hover:bg-stone-50 text-stone-700 rounded-xl shadow-md border border-stone-200 text-xs font-semibold tracking-wide transition-all cursor-pointer"
        title="View All India"
      >
        Whole India
      </button>

      {routeCoords.length >= 2 && (
        <button
          type="button"
          onClick={onFocusRoute}
          className="px-3 py-1.5 bg-[#1A73E8] hover:bg-[#1557B0] text-white rounded-xl shadow-md text-xs font-semibold tracking-wide transition-all cursor-pointer"
          title="Focus on Active Route"
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
  const mapRef = useRef<L.Map | null>(null);

  // Fetch station database and train timetable stops on initial mount
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

  // Quick lookup table for stations by code
  const stationMap = useMemo(() => {
    const map = new Map<string, StationGeo>();
    stations.forEach((s) => map.set(s.c.toUpperCase(), s));
    return map;
  }, [stations]);

  // Compute ONLY the stations and coordinates for the selected route
  const { routeStations, trainPolylineCoords, busPolylineCoords, allRouteCoords } = useMemo(() => {
    const stationList: RouteStation[] = [];
    const addedCodes = new Set<string>();
    const trainCoords: [number, number][] = [];
    const busCoords: [number, number][] = [];
    const allCoords: [number, number][] = [];

    if (stations.length === 0) {
      return { routeStations: stationList, trainPolylineCoords: trainCoords, busPolylineCoords: busCoords, allRouteCoords: allCoords };
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

    // 1. Process Train Legs
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
          const isOrigin = i === 0 && legIdx === 0;
          const isDest = i === timetableStops.length - 1 && legIdx === legs.length - 1 && busLegs.length === 0;
          const isTransfer = (i === timetableStops.length - 1 && legIdx < legs.length - 1) || (i === 0 && legIdx > 0);

          if (!addedCodes.has(st.c)) {
            addedCodes.add(st.c);
            stationList.push({
              c: st.c,
              n: st.n,
              lat: st.lat,
              lon: st.lon,
              routeRole: isOrigin ? 'ORIGIN' : isDest ? 'DESTINATION' : isTransfer ? 'TRANSFER' : 'TRAIN_STOP',
              trainNumber: tNum,
            });
          }

          trainCoords.push([st.lat, st.lon]);
          allCoords.push([st.lat, st.lon]);
        });
      } else {
        // Fallback: corridor stations between from & to
        if (fromSt && !addedCodes.has(fromSt.c)) {
          addedCodes.add(fromSt.c);
          stationList.push({
            c: fromSt.c,
            n: fromSt.n,
            lat: fromSt.lat,
            lon: fromSt.lon,
            routeRole: legIdx === 0 ? 'ORIGIN' : 'TRANSFER',
            trainNumber: tNum,
          });
        }
        trainCoords.push([fLat, fLon]);
        allCoords.push([fLat, fLon]);

        const corridor = findCorridorStations(fLat, fLon, tLat, tLon, 12);
        corridor.forEach((s) => {
          if (!addedCodes.has(s.c) && s.c !== fromCode && s.c !== toCode) {
            addedCodes.add(s.c);
            stationList.push({
              c: s.c,
              n: s.n,
              lat: s.lat,
              lon: s.lon,
              routeRole: 'TRAIN_STOP',
              trainNumber: tNum,
            });
            trainCoords.push([s.lat, s.lon]);
            allCoords.push([s.lat, s.lon]);
          }
        });

        if (toSt && !addedCodes.has(toSt.c)) {
          addedCodes.add(toSt.c);
          stationList.push({
            c: toSt.c,
            n: toSt.n,
            lat: toSt.lat,
            lon: toSt.lon,
            routeRole: legIdx === legs.length - 1 && busLegs.length === 0 ? 'DESTINATION' : 'TRANSFER',
            trainNumber: tNum,
          });
        }
        trainCoords.push([tLat, tLon]);
        allCoords.push([tLat, tLon]);
      }
    });

    // 2. Process Bus Legs
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

      if (fromSt && !addedCodes.has(fromSt.c)) {
        addedCodes.add(fromSt.c);
        stationList.push({
          c: fromSt.c,
          n: fromSt.n,
          lat: fromSt.lat,
          lon: fromSt.lon,
          routeRole: legs.length === 0 && bIdx === 0 ? 'ORIGIN' : 'TRANSFER',
          busOperator: bus.operator_name,
        });
      }
      busCoords.push([fLat, fLon]);
      allCoords.push([fLat, fLon]);

      const busCorridor = findCorridorStations(fLat, fLon, tLat, tLon, 15);
      busCorridor.forEach((s) => {
        if (!addedCodes.has(s.c) && s.c !== fromCode && s.c !== toCode) {
          addedCodes.add(s.c);
          stationList.push({
            c: s.c,
            n: s.n,
            lat: s.lat,
            lon: s.lon,
            routeRole: 'BUS_STOP',
            busOperator: bus.operator_name,
          });
          busCoords.push([s.lat, s.lon]);
          allCoords.push([s.lat, s.lon]);
        }
      });

      if (toSt && !addedCodes.has(toSt.c)) {
        addedCodes.add(toSt.c);
        stationList.push({
          c: toSt.c,
          n: toSt.n,
          lat: toSt.lat,
          lon: toSt.lon,
          routeRole: bIdx === busLegs.length - 1 ? 'DESTINATION' : 'TRANSFER',
          busOperator: bus.operator_name,
        });
      }
      busCoords.push([tLat, tLon]);
      allCoords.push([tLat, tLon]);
    });

    return { routeStations: stationList, trainPolylineCoords: trainCoords, busPolylineCoords: busCoords, allRouteCoords: allCoords };
  }, [stations, trainStops, stationMap, legs, busLegs]);

  const handleResetIndia = () => {
    if (mapRef.current) {
      mapRef.current.setView([22.5, 79.5], 5);
    }
  };

  const handleFocusRoute = () => {
    if (mapRef.current && allRouteCoords.length >= 2) {
      mapRef.current.fitBounds(allRouteCoords, { padding: [55, 55], maxZoom: 10 });
    }
  };

  // Identify Key Route Endpoints
  const originStation = routeStations.find((s) => s.routeRole === 'ORIGIN');
  const destStation = routeStations.find((s) => s.routeRole === 'DESTINATION');
  const intermediateStops = routeStations.filter((s) => s.routeRole !== 'ORIGIN' && s.routeRole !== 'DESTINATION');

  return (
    <div className="w-full h-full relative overflow-hidden bg-[#F2EFE9] font-['Timeless'] select-none">
      <MapContainer
        center={[22.5, 79.5]}
        zoom={5}
        minZoom={3}
        maxZoom={19}
        ref={mapRef}
        className="w-full h-full"
        zoomControl={false}
      >
        {/* Google Maps Standard Roadmap (Normal green & cream color palette) */}
        <TileLayer
          url="https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
          subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
          attribution='&copy; Google Maps'
          maxZoom={20}
        />

        {/* Auto-fit map to route bounds */}
        {allRouteCoords.length >= 2 && <MapBoundsUpdater coords={allRouteCoords} />}

        {/* Train Route Polyline: Google Transit Blue (#1A73E8) with White Outline */}
        {trainPolylineCoords.length >= 2 && (
          <>
            <Polyline
              positions={trainPolylineCoords}
              color="#FFFFFF"
              weight={7}
              opacity={0.9}
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
          <>
            <Polyline
              positions={busPolylineCoords}
              color="#FFFFFF"
              weight={6}
              opacity={0.9}
            />
            <Polyline
              positions={busPolylineCoords}
              color="#F59E0B"
              weight={3.5}
              dashArray="7, 7"
              opacity={1}
            />
          </>
        )}

        {/* Intermediate Route Stop Dots (Only along the active route) */}
        {intermediateStops.map((st) => (
          <CircleMarker
            key={st.c}
            center={[st.lat, st.lon]}
            radius={st.routeRole === 'TRANSFER' ? 5.5 : 4}
            pathOptions={{
              fillColor: '#FFFFFF',
              fillOpacity: 1,
              color: st.routeRole === 'TRANSFER' ? '#F59E0B' : st.routeRole === 'BUS_STOP' ? '#D97706' : '#1A73E8',
              weight: st.routeRole === 'TRANSFER' ? 2.5 : 2,
            }}
          >
            <Tooltip direction="top" offset={[0, -6]} opacity={0.95}>
              <div className="font-['Timeless'] text-xs px-1 py-0.5 text-stone-900 font-semibold leading-tight">
                <div>{st.n} ({st.c})</div>
                <div className="text-[10px] text-stone-500 font-medium mt-0.5">
                  {st.routeRole === 'TRANSFER' ? 'Change Station' : st.routeRole === 'BUS_STOP' ? 'Bus Stop' : 'Train Stop'}
                </div>
              </div>
            </Tooltip>
          </CircleMarker>
        ))}

        {/* Origin Station Marker: Google Maps Blue Circle with White Center */}
        {originStation && (
          <CircleMarker
            center={[originStation.lat, originStation.lon]}
            radius={7.5}
            pathOptions={{
              fillColor: '#FFFFFF',
              fillOpacity: 1,
              color: '#1A73E8',
              weight: 3.5,
            }}
          >
            <Tooltip direction="top" offset={[0, -8]} permanent opacity={0.95}>
              <div className="font-['Timeless'] text-xs font-bold text-[#1A73E8] bg-white px-2 py-0.5 rounded shadow-sm border border-blue-200">
                {originStation.n} ({originStation.c})
              </div>
            </Tooltip>
          </CircleMarker>
        )}

        {/* Destination Station Marker: Iconic Google Maps Red Pin */}
        {destStation && (
          <Marker
            position={[destStation.lat, destStation.lon]}
            icon={googleDestPinIcon}
          >
            <Tooltip direction="top" offset={[0, -36]} permanent opacity={0.95}>
              <div className="font-['Timeless'] text-xs font-bold text-[#EA4335] bg-white px-2 py-0.5 rounded shadow-sm border border-red-200">
                {destStation.n} ({destStation.c})
              </div>
            </Tooltip>
          </Marker>
        )}

        {/* Floating Controls */}
        <CustomMapControls
          routeCoords={allRouteCoords}
          onResetIndia={handleResetIndia}
          onFocusRoute={handleFocusRoute}
        />
      </MapContainer>

      {/* Top-Left Minimalist Route Badge */}
      {originStation && destStation && (
        <div className="absolute top-4 left-4 z-[450] bg-white/95 backdrop-blur-md px-3.5 py-2 rounded-xl shadow-md border border-stone-200 text-xs font-['Timeless'] text-stone-800 flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#1A73E8]" />
          <span className="font-bold text-[#1A73E8]">
            {originStation.c}
          </span>
          <span className="text-stone-400">→</span>
          <span className="font-bold text-[#EA4335]">
            {destStation.c}
          </span>
          <span className="text-stone-300">|</span>
          <span className="text-stone-600 font-medium">
            {intermediateStops.length} stops
          </span>
        </div>
      )}

      {/* Bottom-Left Minimalist Legend Bar */}
      <div className="absolute bottom-4 left-4 z-[450] bg-white/95 backdrop-blur-md px-3.5 py-1.5 rounded-xl shadow-md border border-stone-200 text-xs font-['Timeless'] text-stone-700 flex items-center gap-3">
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2.5 h-2.5 rounded-full bg-[#1A73E8] border border-white" /> Origin
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2.5 h-2.5 rounded-full bg-[#EA4335] border border-white" /> Dest
        </span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-3.5 h-1 bg-[#1A73E8] rounded-xs" /> Train Route
        </span>
        {busPolylineCoords.length > 0 && (
          <span className="flex items-center gap-1.5 font-medium">
            <span className="w-3.5 h-1 bg-[#F59E0B] border-b border-dashed border-[#F59E0B]" /> Bus Leg
          </span>
        )}
        <span className="flex items-center gap-1.5 font-medium">
          <span className="w-2 h-2 rounded-full bg-white border border-[#1A73E8]" /> Stop
        </span>
      </div>
    </div>
  );
}
