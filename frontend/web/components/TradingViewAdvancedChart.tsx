"use client";

import { useEffect, useRef } from "react";
import datafeed from "@/lib/tradingviewDatafeed";

declare global {
  interface Window {
    TradingView?: {
      widget: new (config: Record<string, unknown>) => { remove: () => void };
    };
  }
}

type TradingViewAdvancedChartProps = {
  symbol: string;
  interval: string;
  locale?: string;
};

const toTvInterval = (interval: string): string => {
  if (interval === "1m") return "1";
  if (interval === "5m") return "5";
  if (interval === "1h") return "60";
  if (interval === "1d") return "1D";
  return "60";
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

export default function TradingViewAdvancedChart({
  symbol,
  interval,
  locale = "en",
}: TradingViewAdvancedChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let tvWidget: { remove: () => void } | null = null;
    let mounted = true;

    const init = async () => {
      await loadScript("tv-charting-library", "/charting_library/charting_library.standalone.js");

      if (!mounted || !window.TradingView || !containerRef.current) return;

      tvWidget = new window.TradingView.widget({
        container: containerRef.current,
        locale,
        library_path: "/charting_library/",
        datafeed,
        symbol,
        interval: toTvInterval(interval),
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

  return <div ref={containerRef} style={{ width: "100%", height: 420 }} />;
}
