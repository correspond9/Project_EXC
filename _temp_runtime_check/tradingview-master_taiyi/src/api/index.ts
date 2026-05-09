export type ResolutionString = string;

export type Kline = {
  open_time: number;
  open_price: string;
  high_price: string;
  low_price: string;
  close_price: string;
};

const getApiBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    return (
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      process.env.REACT_APP_API_BASE_URL ||
      window.location.origin
    );
  }

  return process.env.NEXT_PUBLIC_API_BASE_URL || process.env.REACT_APP_API_BASE_URL || "http://localhost";
};

const createApiUrl = (path: string, params?: Record<string, string | number>) => {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const url = new URL(`${base}${path}`);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, String(value));
    });
  }

  return url.toString();
};

const resolutionToInterval = (resolution: ResolutionString): "1m" | "5m" | "1h" | "1d" => {
  if (/^\d+$/.test(resolution)) {
    const minutes = Number(resolution);
    if (minutes <= 1) return "1m";
    if (minutes <= 5) return "5m";
    if (minutes <= 60) return "1h";
    return "1d";
  }

  if (/D|W|M/i.test(resolution)) return "1d";
  return "1h";
};

export const getKlines = async (symbol: string, interval: string, limit: number): Promise<Kline[]> => {
  const url = createApiUrl(`/api/market/klines/${encodeURIComponent(symbol)}`, {
    interval,
    limit,
  });

  const response = await fetch(url, { credentials: "include" });
  if (!response.ok) {
    throw new Error(`Klines request failed: ${response.status}`);
  }

  return response.json();
};

export const getQuoteBySymbol = async (symbol: string): Promise<Kline | null> => {
  const candles = await getKlines(symbol, "1m", 1);
  return candles.length > 0 ? candles[candles.length - 1] : null;
};

type HistoryProps = {
  from: number;
  to: number;
  resolution: ResolutionString;
  symbol: string;
};

export const getSymbolHistories = async ({ from, to, resolution, symbol }: HistoryProps): Promise<Kline[]> => {
  const interval = resolutionToInterval(resolution);
  const requestedBars = Math.max(200, Math.min(2000, Math.ceil((to - from) / 60)));
  const candles = await getKlines(symbol, interval, requestedBars);

  return candles.filter((k) => {
    const t = Math.floor(k.open_time / 1000);
    return t >= from && t <= to;
  });
};
