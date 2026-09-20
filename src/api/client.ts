import type {
  RouteSearchResponse,
  StationItem,
  TrainAvailabilityResponse,
  TrainLiveStatus,
} from './types';

const API_BASE = 'http://localhost:8000/api/v1';

// Popular Indian City -> Nearby Railway Stations Mapping (for cities with/without direct railway stations)
export const CITY_NEARBY_HUBS: Record<string, StationItem[]> = {
  noida: [
    { code: 'ANVT', name: 'Anand Vihar Terminal', state: 'Delhi', distance_km: 11 },
    { code: 'NZM', name: 'Hazrat Nizamuddin', state: 'Delhi', distance_km: 14 },
    { code: 'NDLS', name: 'New Delhi', state: 'Delhi', distance_km: 18 },
    { code: 'GZB', name: 'Ghaziabad Junction', state: 'Uttar Pradesh', distance_km: 16 },
  ],
  gurgaon: [
    { code: 'GGN', name: 'Gurgaon Railway Station', state: 'Haryana', distance_km: 4 },
    { code: 'DEC', name: 'Delhi Cantt', state: 'Delhi', distance_km: 19 },
    { code: 'NZM', name: 'Hazrat Nizamuddin', state: 'Delhi', distance_km: 31 },
    { code: 'NDLS', name: 'New Delhi', state: 'Delhi', distance_km: 32 },
  ],
  gurugram: [
    { code: 'GGN', name: 'Gurgaon Railway Station', state: 'Haryana', distance_km: 4 },
    { code: 'DEC', name: 'Delhi Cantt', state: 'Delhi', distance_km: 19 },
    { code: 'NZM', name: 'Hazrat Nizamuddin', state: 'Delhi', distance_km: 31 },
  ],
  gwalior: [
    { code: 'GWL', name: 'Gwalior Junction', state: 'Madhya Pradesh', distance_km: 0 },
    { code: 'DBA', name: 'Dabra', state: 'Madhya Pradesh', distance_km: 42 },
    { code: 'MRA', name: 'Morena', state: 'Madhya Pradesh', distance_km: 38 },
  ],
  pune: [
    { code: 'PUNE', name: 'Pune Junction', state: 'Maharashtra', distance_km: 0 },
    { code: 'SVJR', name: 'Shivajinagar', state: 'Maharashtra', distance_km: 3 },
    { code: 'KK', name: 'Khadki', state: 'Maharashtra', distance_km: 7 },
    { code: 'CCH', name: 'Chinchwad', state: 'Maharashtra', distance_km: 16 },
  ],
  navi_mumbai: [
    { code: 'PNVL', name: 'Panvel Junction', state: 'Maharashtra', distance_km: 8 },
    { code: 'TNA', name: 'Thane', state: 'Maharashtra', distance_km: 18 },
    { code: 'LTT', name: 'Lokmanya Tilak Terminus', state: 'Maharashtra', distance_km: 22 },
    { code: 'CSMT', name: 'Mumbai CSMT', state: 'Maharashtra', distance_km: 32 },
  ],
  bengaluru: [
    { code: 'SBC', name: 'KSR Bengaluru City', state: 'Karnataka', distance_km: 0 },
    { code: 'YPR', name: 'Yesvantpur Junction', state: 'Karnataka', distance_km: 6 },
    { code: 'SMVB', name: 'SMVT Bengaluru', state: 'Karnataka', distance_km: 12 },
    { code: 'BNC', name: 'Bengaluru Cantt', state: 'Karnataka', distance_km: 4 },
  ],
};

export async function searchStations(query: string): Promise<StationItem[]> {
  const cleanQ = query.trim().toLowerCase();
  if (cleanQ.length < 2) return [];

  // Check city satellite suggestions first
  const nearbyHubs = CITY_NEARBY_HUBS[cleanQ] || CITY_NEARBY_HUBS[cleanQ.replace(/\s+/g, '_')];
  if (nearbyHubs) {
    return nearbyHubs;
  }

  try {
    const res = await fetch(`${API_BASE}/stations/search?q=${encodeURIComponent(query)}`);
    if (res.ok) {
      const data = await res.json();
      return data;
    }
  } catch (err) {
    console.warn('Backend station search error, using fallback:', err);
  }

  // Fallback known stations for offline robustness
  const fallbackList: StationItem[] = [
    { code: 'GWL', name: 'Gwalior Junction', state: 'Madhya Pradesh' },
    { code: 'PUNE', name: 'Pune Junction', state: 'Maharashtra' },
    { code: 'NDLS', name: 'New Delhi', state: 'Delhi' },
    { code: 'BPL', name: 'Bhopal Junction', state: 'Madhya Pradesh' },
    { code: 'JHS', name: 'Jhansi Junction', state: 'Uttar Pradesh' },
    { code: 'BINA', name: 'Bina Junction', state: 'Madhya Pradesh' },
    { code: 'BSL', name: 'Bhusaval Junction', state: 'Maharashtra' },
    { code: 'MMR', name: 'Manmad Junction', state: 'Maharashtra' },
    { code: 'CSMT', name: 'Mumbai CSMT', state: 'Maharashtra' },
    { code: 'HWH', name: 'Howrah Junction', state: 'West Bengal' },
    { code: 'CNB', name: 'Kanpur Central', state: 'Uttar Pradesh' },
  ];

  return fallbackList.filter(
    (s) =>
      s.code.toLowerCase().includes(cleanQ) ||
      s.name.toLowerCase().includes(cleanQ)
  );
}

export async function searchRoutes(params: {
  origin: string;
  destination: string;
  travelDate: string;
  maxTransfers?: number;
  priority?: string;
  accessibleOnly?: boolean;
}): Promise<RouteSearchResponse> {
  const payload = {
    origin: params.origin.toUpperCase().trim(),
    destination: params.destination.toUpperCase().trim(),
    travel_date: params.travelDate,
    max_transfers: params.maxTransfers ?? 2,
    priority: params.priority ?? 'balanced',
    accessible_only: params.accessibleOnly ?? false,
  };

  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Route search failed with status ${res.status}`);
  }
  return res.json();
}

export async function checkTrainAvailability(params: {
  trainNumber: string;
  fromStation: string;
  toStation: string;
  travelDate: string;
  quota?: string;
}): Promise<TrainAvailabilityResponse> {
  const payload = {
    train_number: params.trainNumber,
    from_station: params.fromStation,
    to_station: params.toStation,
    travel_date: params.travelDate,
    quota: params.quota ?? 'GN',
  };

  const res = await fetch(`${API_BASE}/availability/train`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Availability check failed with status ${res.status}`);
  }
  return res.json();
}

export async function getLiveTrainStatus(trainNumber: string): Promise<TrainLiveStatus> {
  const res = await fetch(`${API_BASE}/trains/${encodeURIComponent(trainNumber)}/live`);
  if (!res.ok) {
    throw new Error(`Live status check failed with status ${res.status}`);
  }
  return res.json();
}
