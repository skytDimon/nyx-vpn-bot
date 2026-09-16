import { getToken } from '../lib/auth';
import type { CabinetData } from '../types';

export async function getCabinetData(): Promise<CabinetData> {
  const token = getToken();
  const url = `/cabinet/api/subscription?t=${encodeURIComponent(token)}`;
  const res = await fetch(url);
  if (!res.ok) {
    if (res.status === 401) throw new Error('TokenExpired');
    if (res.status === 404) throw new Error('UserNotFound');
    throw new Error(`HTTP ${res.status}`);
  }
  const data = (await res.json()) as CabinetData;
  return data;
}
