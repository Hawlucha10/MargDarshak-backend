export interface RecentSearchItem {
  id: string;
  type: 'station' | 'nlp';
  origin?: string;
  originCode?: string;
  destination?: string;
  destCode?: string;
  query?: string;
  label: string; // e.g. "INDB → JBP" or "Udaipur to Gwalior"
  date?: string;
  timestamp: number;
}

const STORAGE_KEY = 'margdarshak_recent_searches';
const MAX_RECENT_SEARCHES = 2;

export function getRecentSearches(): RecentSearchItem[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.slice(0, MAX_RECENT_SEARCHES);
  } catch (err) {
    console.error('Failed to parse recent searches', err);
    return [];
  }
}

export function saveRecentSearch(
  item: Omit<RecentSearchItem, 'id' | 'timestamp'>
): RecentSearchItem[] {
  if (typeof window === 'undefined') return [];
  try {
    const existing = getRecentSearches();

    // Deduplicate by origin+dest or query
    const filtered = existing.filter((e) => {
      if (item.type === 'station' && e.type === 'station') {
        const sameOrig = e.originCode?.toUpperCase() === item.originCode?.toUpperCase();
        const sameDest = e.destCode?.toUpperCase() === item.destCode?.toUpperCase();
        return !(sameOrig && sameDest);
      }
      if (item.type === 'nlp' && e.type === 'nlp') {
        return e.query?.toLowerCase() !== item.query?.toLowerCase();
      }
      return e.label.toLowerCase() !== item.label.toLowerCase();
    });

    const newItem: RecentSearchItem = {
      ...item,
      id: `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      timestamp: Date.now(),
    };

    const updated = [newItem, ...filtered].slice(0, MAX_RECENT_SEARCHES);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

    // Dispatch event so other components immediately update
    window.dispatchEvent(new CustomEvent('recentSearchesUpdated', { detail: updated }));

    return updated;
  } catch (err) {
    console.error('Failed to save recent search', err);
    return [];
  }
}

export function clearRecentSearches(): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.removeItem(STORAGE_KEY);
    window.dispatchEvent(new CustomEvent('recentSearchesUpdated', { detail: [] }));
  } catch (err) {
    console.error('Failed to clear recent searches', err);
  }
}
