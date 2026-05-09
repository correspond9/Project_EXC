export type ResolutionString = string;

type Kline = {
  open_time: number;
  open_price: string;
  high_price: string;
  low_price: string;
  close_price: string;
};

type Bar = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
};

type LibrarySymbolInfo = {
  description: string;
  name: string;
  ticker: string;
  session: string;
  timezone: string;
  type: string;
  has_intraday: boolean;
  has_daily: boolean;
  exchange: string;
  minmov: number;
  minmove2: number;
  fractional: boolean;
  currency_code: string;
  pricescale: number;
  supported_resolutions: string[];
};

type PeriodParams = {
  from: number;
  to: number;
};

type OnReadyCallback = (config: { supported_resolutions: string[] }) => void;
type HistoryCallback = (bars: Bar[], meta: { noData: boolean }) => void;
type ErrorCallback = (error: string) => void;

const getApiBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_BASE_URL || window.location.origin;
  }

  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost";
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

const countDecimals = (value: string): number => {
  const [, decimals = ""] = value.split(".");
  return decimals.length;
};

const getKlines = async (symbol: string, interval: string, limit: number): Promise<Kline[]> => {
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

const getQuoteBySymbol = async (symbol: string): Promise<Kline | null> => {
  const candles = await getKlines(symbol, "1m", 1);
  return candles.length > 0 ? candles[candles.length - 1] : null;
};

const getSymbolHistories = async ({
  from,
  to,
  resolution,
  symbol,
}: {
  from: number;
  to: number;
  resolution: ResolutionString;
  symbol: string;
}): Promise<Kline[]> => {
  const interval = resolutionToInterval(resolution);
  const requestedBars = Math.max(200, Math.min(2000, Math.ceil((to - from) / 60)));
  const candles = await getKlines(symbol, interval, requestedBars);

  return candles.filter((k) => {
    const t = Math.floor(k.open_time / 1000);
    return t >= from && t <= to;
  });
};

const datafeed = {
  onReady: (callback: OnReadyCallback) => {
    const config = {
      supported_resolutions: ["1", "5", "60", "1D"],
    };
    setTimeout(() => callback(config));
  },
  resolveSymbol: async (symbolName: string, onSymbolResolvedCallback: (info: LibrarySymbolInfo) => void) => {
    const quote = await getQuoteBySymbol(symbolName);
    const closePrice = quote?.close_price || "1";
    const pricescale = Math.pow(10, Math.max(0, countDecimals(closePrice)));

    const symbolInfo = {
      description: symbolName,
      name: symbolName,
      ticker: symbolName,
      session: "24x7",
      timezone: "Etc/UTC",
      type: "crypto",
      has_intraday: true,
      has_daily: true,
      exchange: "",
      minmov: 1,
      minmove2: 0,
      fractional: false,
      currency_code: "",
      pricescale,
      supported_resolutions: ["1", "5", "60", "1D"],
    } as LibrarySymbolInfo;

    onSymbolResolvedCallback(symbolInfo);
  },
  getBars: async (
    symbolInfo: LibrarySymbolInfo,
    resolution: ResolutionString,
    periodParams: PeriodParams,
    onHistoryCallback: HistoryCallback,
    onErrorCallback: ErrorCallback
  ) => {
    const symbol = symbolInfo.name;
    const { from, to } = periodParams;

    try {
      const rows = await getSymbolHistories({
        resolution,
        symbol,
        to,
        from,
      });

      if (!rows.length) {
        onHistoryCallback([], { noData: true });
        return;
      }

      const bars = rows.map((k) => ({
        time: k.open_time,
        open: parseFloat(k.open_price),
        high: parseFloat(k.high_price),
        low: parseFloat(k.low_price),
        close: parseFloat(k.close_price),
      }));

      onHistoryCallback(bars, { noData: false });
    } catch (error) {
      onErrorCallback(error instanceof Error ? error.message : "Failed to load bars");
    }
  },
  subscribeBars: (
    _symbolInfo: LibrarySymbolInfo,
    _resolution: ResolutionString,
    _onRealtimeCallback: (bar: Bar) => void,
    _subscriberUID: string
  ) => {
    // Real-time stream can be connected in a later step.
  },
  unsubscribeBars: (_subscriberUID: string) => {
    // No-op until real-time stream wiring is added.
  },
};

export default datafeed;
