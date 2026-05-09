import { getQuoteBySymbol, getSymbolHistories, ResolutionString } from "../api";

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

const countDecimals = (value: string): number => {
  const [, decimals = ""] = value.split(".");
  return decimals.length;
};

const DataFeed = {
  onReady: (callback: OnReadyCallback) => {
    const config = {
      supported_resolutions: ["1", "5", "15", "60", "1D"],
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
      supported_resolutions: ["1", "5", "15", "60", "1D"],
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
    // Real-time stream can be plugged in during integration using your WebSocket endpoint.
  },
  unsubscribeBars: (_subscriberUID: string) => {
    // No-op until real-time stream wiring is enabled.
  },
};

export default DataFeed;
