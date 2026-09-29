import type {
  RouteAvailabilityRequest,
  RouteAvailabilityResponse,
  RouteSearchResponse,
  StationItem,
  TrainAvailabilityResponse,
  TrainLiveStatus,
} from './types';

const API_BASE = '/api/v1';

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

export async function getPopularStations(): Promise<StationItem[]> {
  try {
    const res = await fetch(`${API_BASE}/stations/popular?limit=10`);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Failed to fetch popular stations, using fallback:', err);
  }

  return [
    { code: 'NDLS', name: 'NEW DELHI', zone: 'NR', state: 'Delhi', is_hub: true },
    { code: 'GWL', name: 'GWALIOR JN', zone: 'NCR', state: 'Madhya Pradesh', is_hub: true },
    { code: 'PUNE', name: 'PUNE JN', zone: 'CR', state: 'Maharashtra', is_hub: true },
    { code: 'CSTM', name: 'MUMBAI CST', zone: 'CR', state: 'Maharashtra', is_hub: true },
    { code: 'BPL', name: 'BHOPAL JN', zone: 'WCR', state: 'Madhya Pradesh', is_hub: true },
    { code: 'INDB', name: 'INDORE JN BG', zone: 'WR', state: 'Madhya Pradesh', is_hub: true },
    { code: 'JBP', name: 'JABALPUR', zone: 'WCR', state: 'Madhya Pradesh', is_hub: true },
    { code: 'HWH', name: 'HOWRAH JN', zone: 'ER', state: 'West Bengal', is_hub: true },
    { code: 'SBC', name: 'KSR BENGALURU', zone: 'SWR', state: 'Karnataka', is_hub: true },
    { code: 'MAS', name: 'MGR CHENNAI CTL', zone: 'SR', state: 'Tamil Nadu', is_hub: true },
  ];
}

export async function searchStations(query: string): Promise<StationItem[]> {
  const cleanQ = query.trim().toLowerCase();
  if (!cleanQ) {
    return getPopularStations();
  }

  // Check city satellite suggestions first
  const nearbyHubs = CITY_NEARBY_HUBS[cleanQ] || CITY_NEARBY_HUBS[cleanQ.replace(/\s+/g, '_')];
  if (nearbyHubs) {
    return nearbyHubs;
  }

  try {
    const res = await fetch(`${API_BASE}/stations/search?q=${encodeURIComponent(query)}&limit=15`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data;
      }
    }
  } catch (err) {
    console.warn('Backend station search error, using fallback:', err);
  }

  // Fallback known stations for offline robustness
  const fallbackList: StationItem[] = [
    { code: 'GWL', name: 'GWALIOR JN', zone: 'NCR', state: 'Madhya Pradesh', is_hub: true },
    { code: 'PUNE', name: 'PUNE JN', zone: 'CR', state: 'Maharashtra', is_hub: true },
    { code: 'NDLS', name: 'NEW DELHI', zone: 'NR', state: 'Delhi', is_hub: true },
    { code: 'BPL', name: 'BHOPAL JN', zone: 'WCR', state: 'Madhya Pradesh', is_hub: true },
    { code: 'INDB', name: 'INDORE JN BG', zone: 'WR', state: 'Madhya Pradesh', is_hub: true },
    { code: 'JBP', name: 'JABALPUR', zone: 'WCR', state: 'Madhya Pradesh', is_hub: true },
    { code: 'CSTM', name: 'MUMBAI CST', zone: 'CR', state: 'Maharashtra', is_hub: true },
    { code: 'HWH', name: 'HOWRAH JN', zone: 'ER', state: 'West Bengal', is_hub: true },
    { code: 'SBC', name: 'KSR BENGALURU', zone: 'SWR', state: 'Karnataka', is_hub: true },
    { code: 'MAS', name: 'MGR CHENNAI CTL', zone: 'SR', state: 'Tamil Nadu', is_hub: true },
    { code: 'CNB', name: 'KANPUR CENTRAL', zone: 'NCR', state: 'Uttar Pradesh', is_hub: true },
    { code: 'JHS', name: 'JHANSI JN', zone: 'NCR', state: 'Uttar Pradesh' },
    { code: 'BINA', name: 'BINA JN', zone: 'WCR', state: 'Madhya Pradesh' },
    { code: 'BSL', name: 'BHUSAVAL JN', zone: 'CR', state: 'Maharashtra' },
    { code: 'MMR', name: 'MANMAD JN', zone: 'CR', state: 'Maharashtra' },
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
  travelClass?: string;
}): Promise<TrainAvailabilityResponse> {
  const payload = {
    train_number: params.trainNumber,
    from_station: params.fromStation,
    to_station: params.toStation,
    travel_date: params.travelDate,
    quota: params.quota ?? 'GN',
    travel_class: params.travelClass ?? 'SL',
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

export async function checkRouteAvailability(
  payload: RouteAvailabilityRequest
): Promise<RouteAvailabilityResponse> {
  const res = await fetch(`${API_BASE}/availability/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Route availability check failed with status ${res.status}`);
  }
  return res.json();
}

