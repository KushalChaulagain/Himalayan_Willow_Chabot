import { UserProfile } from '../types';

const STORAGE_KEY = 'hw_user_profile';
const RETURNING_THRESHOLD_DAYS = 90;

export function saveProfile(data: Partial<UserProfile>): void {
  try {
    const existing = loadProfile();
    const merged: UserProfile = {
      ...existing,
      ...data,
      last_visit: new Date().toISOString(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
  } catch {
    // localStorage may be unavailable in private browsing
  }
}

export function loadProfile(): UserProfile | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as UserProfile;
  } catch {
    return null;
  }
}

export function clearProfile(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // noop
  }
}

export function isReturningUser(): boolean {
  const profile = loadProfile();
  if (!profile?.last_visit) return false;
  const lastVisit = new Date(profile.last_visit);
  const daysSince = (Date.now() - lastVisit.getTime()) / (1000 * 60 * 60 * 24);
  return daysSince <= RETURNING_THRESHOLD_DAYS;
}

export function addPurchaseToHistory(
  productId: number,
  productName: string
): void {
  const profile = loadProfile() || {};
  const history = profile.purchase_history || [];
  history.push({
    product_id: productId,
    name: productName,
    date: new Date().toISOString(),
  });
  saveProfile({ purchase_history: history });
}

export function getSavedSessionId(): string | null {
  return loadProfile()?.session_id || null;
}
