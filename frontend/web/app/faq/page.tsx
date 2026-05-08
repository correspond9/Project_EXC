"use client";

import Link from "next/link";
import { useState } from "react";

const FAQS = [
  {
    question: "Is XChange regulated?",
    answer:
      "Yes. XChange is licensed by the Virtual Assets Regulatory Authority (VARA) in Dubai, UAE under [Licence Number]. We comply with all VARA AML/CFT requirements.",
  },
  {
    question: "Do I need to verify my identity to use the platform?",
    answer:
      "Simulation mode is available to all registered users with no KYC required. To access live trading with real funds, you must complete our KYC process: upload a government-issued ID, proof of address, and a selfie.",
  },
  {
    question: "What is Simulation mode?",
    answer:
      "Simulation mode lets you practice trading with virtual funds at real live market prices. Your orders go through the same mechanics as real trading — but no real money changes hands. It's completely free and a great way to learn before going live.",
  },
  {
    question: "How do I enable Live trading?",
    answer:
      "Complete KYC verification (Settings → Verification), then contact support to request Live mode activation. Once your KYC is approved, an admin will enable Live mode on your account.",
  },
  {
    question: "What cryptocurrencies can I trade?",
    answer:
      "We currently support all Binance Spot and Futures pairs including BTC, ETH, BNB, SOL, and many more. The full instrument list is available in the trading terminal.",
  },
  {
    question: "What are the trading fees?",
    answer:
      "Live trading is charged at 0.1% maker / 0.1% taker per executed trade. Simulation trading is completely free. See our Pricing page for full details.",
  },
  {
    question: "Is my money safe?",
    answer:
      "Your live trading balances are held and executed via Binance, a globally licensed virtual asset service provider. We maintain full audit trails of all deposits, withdrawals, and trades. All withdrawals require manual admin approval. However, all trading carries risk — please read our Risk Disclosure.",
  },
  {
    question: "Can I trade on mobile?",
    answer:
      "Yes. Our React Native mobile app is available for iOS and Android. It supports the full trading terminal including portfolio view, order placement, and real-time price updates.",
  },
  {
    question: "What leverage is available for Futures?",
    answer:
      "LIVE Futures leverage is available up to 20× subject to VARA regulatory limits and per-user caps set by our compliance team. Simulation Futures supports up to 100× for educational purposes.",
  },
  {
    question: "How do I withdraw funds?",
    answer:
      "Go to Wallet → Withdraw, enter the amount and your destination address. All withdrawals are reviewed by our team (typically within 1 business day) before being processed to the blockchain.",
  },
  {
    question: "What happens if there's a technical problem during my live trade?",
    answer:
      "Our execution service continuously reconciles open orders with Binance every 5 minutes. If a fill is missed, it will be caught and recorded automatically. In the event of a broader issue, our team can halt trading platform-wide to prevent further impact.",
  },
  {
    question: "How do I contact support?",
    answer: "Email us at support@[domain] or use the in-app chat. We aim to respond within 4 business hours.",
  },
];

export default function FAQPage() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-zinc-800">
        <Link href="/landing" className="text-xl font-bold tracking-tight">
          XChange
        </Link>
        <div className="flex gap-4 text-sm">
          <Link href="/login" className="px-4 py-2 rounded-lg border border-zinc-700 hover:border-zinc-400 transition-colors">
            Log In
          </Link>
          <Link href="/register" className="px-4 py-2 rounded-lg bg-blue-600 font-medium hover:bg-blue-500 transition-colors">
            Get Started
          </Link>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-8 py-24">
        <h1 className="text-4xl font-bold mb-4">Frequently Asked Questions</h1>
        <p className="text-zinc-400 mb-12">
          Can&apos;t find what you&apos;re looking for?{" "}
          <a href="mailto:support@[domain]" className="text-blue-400 hover:underline">
            Contact support
          </a>
          .
        </p>

        <div className="space-y-3">
          {FAQS.map((faq, i) => (
            <div
              key={i}
              className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden"
            >
              <button
                className="w-full flex items-center justify-between px-6 py-4 text-left"
                onClick={() => setOpen(open === i ? null : i)}
                aria-expanded={open === i}
              >
                <span className="font-medium text-sm">{faq.question}</span>
                <span className="text-zinc-500 ml-4 text-lg">{open === i ? "−" : "+"}</span>
              </button>
              {open === i && (
                <div className="px-6 pb-5 text-sm text-zinc-400 leading-relaxed border-t border-zinc-800 pt-4">
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-16 text-center text-xs text-zinc-500 flex justify-center gap-6">
          <Link href="/terms" className="hover:text-zinc-300">Terms</Link>
          <Link href="/privacy" className="hover:text-zinc-300">Privacy</Link>
          <Link href="/risk-disclosure" className="hover:text-zinc-300">Risk Disclosure</Link>
          <Link href="/pricing" className="hover:text-zinc-300">Pricing</Link>
        </div>
      </div>
    </div>
  );
}
