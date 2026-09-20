export interface StationItem {
  code: string;
  name: string;
  state?: string;
  zone?: string;
  distance_km?: number;
}

export interface TrainLeg {
  train_number: string;
  train_name: string;
  from_station: string;
  from_station_name: string;
  to_station: string;
  to_station_name: string;
  departure_time: string;
  arrival_time: string;
  day: number;
  predicted_delay_min: number;
  fare_estimate?: number;
  departure_platform?: string;
  arrival_platform?: string;
}

export interface TransferConnection {
  station_code: string;
  station_name: string;
  wait_time_minutes: number;
  is_safe: boolean;
  delay_risk_warning?: string | null;
  arrival_platform?: string;
  departure_platform?: string;
  interchange_guide?: string;
}

export interface JourneyRoute {
  label: string;
  total_travel_time: string;
  total_fare?: number;
  transfers: number;
  reliability_score: number;
  joint_reliability_percent?: string;
  legs: TrainLeg[];
  transfers_info: TransferConnection[];
  fare_arbitrage_tip?: string | null;
  accessibility_badge?: string | null;
  weather_advisory?: string | null;
}

export interface RouteSearchResponse {
  search_id: string;
  origin: string;
  destination: string;
  travel_date: string;
  total_routes_found: number;
  routes: JourneyRoute[];
  cached: boolean;
  computed_in_ms: number;
}

export interface ClassAvailabilityInfo {
  class_code: string;
  class_name: string;
  status: string;
  available_seats: number;
  fare_inr: number;
  confirmation_probability?: number | null;
  confirmation_probability_pct?: string | null;
  is_available: boolean;
}

export interface QuotaArbitrageTip {
  upstream_station_code: string;
  upstream_station_name: string;
  quota_type: string;
  available_seats: number;
  ticket_fare: number;
  origin_fare: number;
  savings_inr: number;
  instruction: string;
}

export interface TrainAvailabilityResponse {
  train_number: string;
  train_name: string;
  from_station: string;
  to_station: string;
  travel_date: string;
  quota: string;
  classes: ClassAvailabilityInfo[];
  arbitrage_recommendation?: QuotaArbitrageTip | null;
  cached: boolean;
  checked_at: string;
}

export interface TrainStop {
  station_code: string;
  station_name: string;
  arrival?: string | null;
  departure?: string | null;
  day: number;
  stop_sequence?: number;
  distance_km?: number;
  delay_minutes: number;
  actual_arrival?: string | null;
  actual_departure?: string | null;
  has_passed: boolean;
}

export interface TrainLiveStatus {
  train_number: string;
  train_name: string;
  current_station: string;
  current_station_name: string;
  delay_minutes: number;
  delay_status: string;
  delay_trend: string;
  next_stop: string;
  next_stop_name: string;
  eta: string;
  journey_percent: number;
  distance_travelled_km?: number;
  total_distance_km?: number;
  station_timeline: TrainStop[];
  updated_at: string;
  source: string;
  cached: boolean;
}
