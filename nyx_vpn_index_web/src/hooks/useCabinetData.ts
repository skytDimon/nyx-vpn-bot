import { useEffect, useState } from 'react';
import { getCabinetData } from '../api/api';
import { hasToken } from '../lib/auth';
import type { CabinetData } from '../types';

export function useCabinetData() {
  const [data, setData] = useState<CabinetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasToken()) {
      setError('NoToken');
      setLoading(false);
      return;
    }
    let cancelled = false;
    getCabinetData()
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, loading, error };
}
