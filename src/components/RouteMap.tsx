import { useEffect, useState, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip, useMap } from 'react-leaflet';
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
  onOpenRouteDetails?: () => void;
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

// Floating Minimalist Zoom Controls anchored at Bottom-Right (Google Maps style)
function BottomRightZoomControls() {
  const map = useMap();

  return (
    <div className="absolute bottom-5 right-4 z-[500] flex flex-col bg-white rounded-lg shadow-md border border-stone-300 overflow-hidden">
      <button
        type="button"
        onClick={() => map.zoomIn()}
        className="w-8.5 h-8.5 flex items-center justify-center text-stone-700 hover:text-black hover:bg-stone-100 font-bold text-xl transition-colors cursor-pointer leading-none select-none"
        title="Zoom In"
      >
        +
      </button>
      <div className="w-full h-[1px] bg-stone-200" />
      <button
        type="button"
        onClick={() => map.zoomOut()}
        className="w-8.5 h-8.5 flex items-center justify-center text-stone-700 hover:text-black hover:bg-stone-100 font-bold text-xl transition-colors cursor-pointer leading-none select-none"
        title="Zoom Out"
      >
        −
      </button>
    </div>
  );
}

export default function RouteMap({ legs = [], busLegs = [], onOpenRouteDetails }: Props) {
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
  const { routeStations, trainPolylineCoords, busPolylineCoords, allRouteCoords, originCoord, destCoord } = useMemo(() => {
    const stationList: RouteStation[] = [];
    const addedCodes = new Set<string>();
    const trainCoords: [number, number][] = [];
    const busCoords: [number, number][] = [];
    const allCoords: [number, number][] = [];

    if (stations.length === 0) {
      return {
        routeStations: stationList,
        trainPolylineCoords: trainCoords,
        busPolylineCoords: busCoords,
        allRouteCoords: allCoords,
        originCoord: null,
        destCoord: null,
      };
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

      // Ensure the exact destination endpoint of the leg is securely linked in the polyline
      if (legIdx === legs.length - 1 && busLegs.length === 0) {
        const lastCoord = trainCoords[trainCoords.length - 1];
        if (!lastCoord || Math.hypot(lastCoord[0] - tLat, lastCoord[1] - tLon) > 0.0005) {
          trainCoords.push([tLat, tLon]);
          allCoords.push([tLat, tLon]);
        }
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

    // Exact Origin and Destination coordinates guaranteed to connect to the polyline ends
    const origPoint: [number, number] | null =
      trainCoords.length > 0
        ? trainCoords[0]
        : busCoords.length > 0
        ? busCoords[0]
        : null;

    const destPoint: [number, number] | null =
      busCoords.length > 0
        ? busCoords[busCoords.length - 1]
        : trainCoords.length > 0
        ? trainCoords[trainCoords.length - 1]
        : null;

    return {
      routeStations: stationList,
      trainPolylineCoords: trainCoords,
      busPolylineCoords: busCoords,
      allRouteCoords: allCoords,
      originCoord: origPoint,
      destCoord: destPoint,
    };
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

  // Identify Key Route Endpoints and Intermediate Stops
  const originStation = routeStations.find((s) => s.routeRole === 'ORIGIN');
  const destStation = routeStations.find((s) => s.routeRole === 'DESTINATION');
  const intermediateStops = routeStations.filter(
    (s) => s.routeRole !== 'ORIGIN' && s.routeRole !== 'DESTINATION'
  );

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
            radius={st.routeRole === 'TRANSFER' ? 5 : 3.8}
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

        {/* Origin Station Dot: Color 1 (Google Blue #1A73E8) */}
        {originCoord && (
          <CircleMarker
            center={originCoord}
            radius={7}
            pathOptions={{
              fillColor: '#FFFFFF',
              fillOpacity: 1,
              color: '#1A73E8',
              weight: 3.5,
            }}
          >
            <Tooltip direction="top" offset={[0, -6]} opacity={0.95}>
              <div className="font-['Timeless'] text-xs font-bold text-[#1A73E8] bg-white px-1.5 py-0.5 rounded shadow-sm">
                Origin: {originStation?.n || 'Origin Station'} ({originStation?.c || ''})
              </div>
            </Tooltip>
          </CircleMarker>
        )}

        {/* Destination Station Dot: Color 2 (Google Red #EA4335) - Placed directly on polyline terminus */}
        {destCoord && (
          <CircleMarker
            center={destCoord}
            radius={7}
            pathOptions={{
              fillColor: '#FFFFFF',
              fillOpacity: 1,
              color: '#EA4335',
              weight: 3.5,
            }}
          >
            <Tooltip direction="top" offset={[0, -6]} opacity={0.95}>
              <div className="font-['Timeless'] text-xs font-bold text-[#EA4335] bg-white px-1.5 py-0.5 rounded shadow-sm">
                Destination: {destStation?.n || 'Destination Station'} ({destStation?.c || ''})
              </div>
            </Tooltip>
          </CircleMarker>
        )}

        {/* Google Maps Style Zoom Controls at Bottom Right */}
        <BottomRightZoomControls />
      </MapContainer>

      {/* Top-Right Controls: Whole India & Focus Route */}
      <div className="absolute top-4 right-4 z-[500] flex items-center gap-2 font-['Timeless']">
        <button
          type="button"
          onClick={handleResetIndia}
          className="px-3 py-1.5 bg-white hover:bg-stone-50 text-stone-700 rounded-xl shadow-md border border-stone-200 text-xs font-semibold tracking-wide transition-all cursor-pointer"
          title="View All India"
        >
          Whole India
        </button>

        {allRouteCoords.length >= 2 && (
          <button
            type="button"
            onClick={handleFocusRoute}
            className="px-3 py-1.5 bg-[#1A73E8] hover:bg-[#1557B0] text-white rounded-xl shadow-md text-xs font-semibold tracking-wide transition-all cursor-pointer"
            title="Focus on Active Route"
          >
            Focus Route
          </button>
        )}
      </div>

      {/* Top-Left Minimalist Route Badge - Clickable to open timetable on route card */}
      {originStation && destStation && (
        <button
          type="button"
          onClick={onOpenRouteDetails}
          className="absolute top-4 left-4 z-[450] bg-white hover:bg-stone-50 px-3.5 py-2 rounded-xl shadow-md border border-stone-200 text-xs font-['Timeless'] text-stone-800 flex items-center gap-2 transition-all hover:scale-102 hover:shadow-lg active:scale-98 cursor-pointer group"
          title="Click to view full station timetable on selected route card"
        >
          <span className="w-2.5 h-2.5 rounded-full bg-[#1A73E8]" />
          <span className="font-bold text-[#1A73E8]">{originStation.c}</span>
          <span className="text-stone-400">→</span>
          <span className="font-bold text-[#EA4335]">{destStation.c}</span>
          <span className="text-stone-300">|</span>
          <span className="text-stone-600 font-medium">{intermediateStops.length} stops</span>
          <span className="text-[11px] text-[#1A73E8] font-bold group-hover:underline flex items-center gap-0.5 ml-0.5">
            View stops
            <svg className="w-3 h-3 text-[#1A73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </span>
        </button>
      )}

      {/* Bottom-Left Minimalist Legend Bar */}
      <div className="absolute bottom-5 left-4 z-[450] bg-white/95 backdrop-blur-md px-3.5 py-1.5 rounded-xl shadow-md border border-stone-200 text-xs font-['Timeless'] text-stone-700 flex items-center gap-3">
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
