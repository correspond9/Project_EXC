import { useEffect, useRef } from "react";
import DataFeed from "./datafeed";

declare global {
  interface Window {
    TradingView?: {
      widget: new (config: Record<string, unknown>) => { remove: () => void };
    };
  }
}

type TradingViewChartProps = {
  symbol: string;
  interval?: string;
  locale?: string;
};

const loadScript = (id: string, src: string): Promise<void> => {
  const existing = document.getElementById(id) as HTMLScriptElement | null;
  if (existing) {
    if (existing.dataset.loaded === "true") return Promise.resolve();

    return new Promise((resolve, reject) => {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)), { once: true });
    });
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.id = id;
    script.src = src;
    script.async = true;
    script.onload = () => {
      script.dataset.loaded = "true";
      resolve();
    };
    script.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(script);
  });
};

const TradingViewChart = ({ symbol, interval = "60", locale = "en" }: TradingViewChartProps) => {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let tvWidget: { remove: () => void } | null = null;
    let mounted = true;

    const init = async () => {
      await loadScript("tv-charting-library", "/charting_library/charting_library.standalone.js");
      await loadScript("tv-udf-datafeed", "/datafeeds/udf/dist/bundle.js");

      if (!mounted || !window.TradingView || !containerRef.current) return;

      tvWidget = new window.TradingView.widget({
        container: containerRef.current,
        locale,
        library_path: "/charting_library/",
        datafeed: DataFeed,
        symbol,
        interval,
        autosize: true,
      });
    };

    init().catch((error) => {
      console.error("TradingView initialization failed", error);
    });

    return () => {
      mounted = false;
      tvWidget?.remove();
    };
  }, [interval, locale, symbol]);

  return <div id="chartContainer" ref={containerRef} style={{ width: "100%", height: "100%", minHeight: 420 }} />;
};

export default TradingViewChart;
