import { useEffect, useState, useCallback, useMemo } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface LegPoint {
  code: string;
  name: string;
  lat: number;
  lon: number;
  isIntermediate?: boolean;
}

interface Props {
  origin?: string;
  destination?: string;
  legs?: Array<{
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

// Auto-fit map bounds when coordinates change
function MapBoundsUpdater({ coords }: { coords: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    if (coords.length >= 2) {
      map.fitBounds(coords, { padding: [60, 60], maxZoom: 11 });
    } else if (coords.length === 1) {
      map.setView(coords[0], 8);
    }
  }, [coords, map]);
  return null;
}

export default function RouteMap({ legs = [], busLegs = [] }: Props) {
  const [revealedStations, setRevealedStations] = useState<Set<string>>(new Set());

  // Extract train route coordinates
  const trainCoords: [number, number][] = useMemo(() => {
    const pts: [number, number][] = [];
    legs.forEach((leg, i) => {
      if (leg.from_lat != null && leg.from_lon != null) {
        if (i === 0 || pts.length === 0) {
          pts.push([leg.from_lat, leg.from_lon]);
        }
      }
      if (leg.to_lat != null && leg.to_lon != null) {
        pts.push([leg.to_lat, leg.to_lon]);
      }
    });
    return pts;
  }, [legs]);

  // Extract bus route coordinates
  const busCoords: [number, number][] = useMemo(() => {
    const pts: [number, number][] = [];
    busLegs.forEach((leg) => {
      if (leg.from_lat != null && leg.from_lon != null) {
        pts.push([leg.from_lat, leg.from_lon]);
      }
      if (leg.to_lat != null && leg.to_lon != null) {
        pts.push([leg.to_lat, leg.to_lon]);
      }
    });
    return pts;
  }, [busLegs]);

  // Combined bounds coordinates
  const allCoords = useMemo(() => [...trainCoords, ...busCoords], [trainCoords, busCoords]);

  // Extract origin, destination, and intermediate stations
  const { originPt, destPt, intermediatePts } = useMemo(() => {
    let o: LegPoint | null = null;
    let d: LegPoint | null = null;
    const intermediates: LegPoint[] = [];

    if (legs.length > 0) {
      const first = legs[0];
      if (first.from_lat != null && first.from_lon != null) {
        o = {
          code: first.from_station,
          name: first.from_station_name,
          lat: first.from_lat,
          lon: first.from_lon,
        };
      }
      legs.forEach((l, idx) => {
        if (idx < legs.length - 1 && l.to_lat != null && l.to_lon != null) {
          intermediates.push({
            code: l.to_station,
            name: l.to_station_name,
            lat: l.to_lat,
            lon: l.to_lon,
            isIntermediate: true,
          });
        }
      });
      const last = legs[legs.length - 1];
      if (last.to_lat != null && last.to_lon != null) {
        d = {
          code: last.to_station,
          name: last.to_station_name,
          lat: last.to_lat,
          lon: last.to_lon,
        };
      }
    }

    if (busLegs.length > 0) {
      const lastBus = busLegs[busLegs.length - 1];
      if (lastBus.to_lat != null && lastBus.to_lon != null) {
        d = {
          code: lastBus.to_station_code,
          name: lastBus.to_terminal,
          lat: lastBus.to_lat,
          lon: lastBus.to_lon,
        };
      }
    }

    return { originPt: o, destPt: d, intermediatePts: intermediates };
  }, [legs, busLegs]);

  // Progressive reveal: hover over the route line permanently reveals all intermediate stations
  const handleRouteHover = useCallback(() => {
    intermediatePts.forEach((s) => {
      setRevealedStations((prev) => new Set(prev).add(s.code));
    });
  }, [intermediatePts]);

  // Fallback center for India
  const centerCoord: [number, number] = allCoords.length > 0 ? allCoords[0] : [22.5, 78.9];

  return (
    <div className="w-full h-full relative">
      <MapContainer
        center={centerCoord}
        zoom={6}
        className="w-full h-full"
        zoomControl={false}
        style={{ background: '#F5F0E8' }}
      >
        {/* Clean OpenStreetMap tiles with no watermark */}
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          maxZoom={18}
          className="map-tiles-soft"
        />

        {allCoords.length >= 2 && <MapBoundsUpdater coords={allCoords} />}

        {/* Train Route Polyline (Royal Blue) */}
        {trainCoords.length >= 2 && (
          <Polyline
            positions={trainCoords}
            color="#3B5BDB"
            weight={5}
            opacity={0.9}
            eventHandlers={{
              mouseover: handleRouteHover,
            }}
          />
        )}

        {/* Bus Alternative Polyline (Warm Amber Dashed) */}
        {busCoords.length >= 2 && (
          <Polyline
            positions={busCoords}
            color="#D4A843"
            weight={4}
            dashArray="8, 8"
            opacity={0.9}
            eventHandlers={{
              mouseover: handleRouteHover,
            }}
          />
        )}

        {/* Origin Marker (Sage/Olive Green) */}
        {originPt && (
          <CircleMarker
            center={[originPt.lat, originPt.lon]}
            radius={9}
            color="#5A6B3C"
            fillColor="#5A6B3C"
            fillOpacity={1}
            weight={3}
          >
            <Tooltip permanent direction="top" offset={[0, -10]} className="!bg-white !border-0 !shadow-md !rounded-full !px-3 !py-1 !font-sans !text-xs !font-semibold !text-slate-800">
              {originPt.name} ({originPt.code})
            </Tooltip>
          </CircleMarker>
        )}

        {/* Destination Marker (Royal Blue) */}
        {destPt && (
          <CircleMarker
            center={[destPt.lat, destPt.lon]}
            radius={9}
            color="#3B5BDB"
            fillColor="#3B5BDB"
            fillOpacity={1}
            weight={3}
          >
            <Tooltip permanent direction="top" offset={[0, -10]} className="!bg-white !border-0 !shadow-md !rounded-full !px-3 !py-1 !font-sans !text-xs !font-semibold !text-slate-800">
              {destPt.name} ({destPt.code})
            </Tooltip>
          </CircleMarker>
        )}

        {/* Intermediate Junctions (Hidden until route hover, then stay visible) */}
        {intermediatePts.map((s) => {
          const isRevealed = revealedStations.has(s.code);
          return (
            <CircleMarker
              key={s.code}
              center={[s.lat, s.lon]}
              radius={6}
              color="#3B5BDB"
              fillColor="#FFFFFF"
              fillOpacity={isRevealed ? 1 : 0}
              opacity={isRevealed ? 1 : 0}
              weight={2.5}
            >
              {isRevealed && (
                <Tooltip direction="top" offset={[0, -8]} className="!bg-white !border-0 !shadow-md !rounded-lg !px-2.5 !py-1 !font-sans !text-xs !text-slate-700">
                  {s.name} ({s.code})
                </Tooltip>
              )}
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Floating Info Box at Bottom-Left of Map (rounded-xl, no capsules) */}
      <div className="absolute bottom-4 left-4 z-[400] bg-white/95 backdrop-blur-md px-4 py-2.5 rounded-xl shadow-md border border-stone-200/90 text-xs font-sans text-slate-700 flex items-center gap-3">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#5A6B3C]" /> Origin
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-[#3B5BDB]" /> Train Route
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-[#D4A843] border-b border-dashed border-[#D4A843]" /> Bus Leg
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#3B5BDB]" /> Destination
        </span>
      </div>
    </div>
  );
}
