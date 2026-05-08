import Link from "next/link";

const TIERS = [
  {
    name: "Simulation",
    price: "Free",
    priceNote: "forever",
    description: "Practice trading with no real money at risk.",
    features: [
      "Access to live market prices (Binance feed)",
      "Simulated SPOT and FUTURES trading",
      "Full order book: market, limit, stop orders",
      "Real-time P&L and portfolio tracking",
      "No KYC required",
    ],
    cta: "Get Started",
    ctaHref: "/register",
    highlight: false,
  },
  {
    name: "Live",
    price: "0.1%",
    priceNote: "maker / 0.1% taker per trade",
    description: "Trade with real funds once KYC-approved.",
    features: [
      "Everything in Simulation",
      "SPOT trading with real funds",
      "Leverage FUTURES (up to 20× — per VARA limits)",
      "Crypto deposits and withdrawals",
      "Full audit trail & transaction history",
      "VARA-regulated platform",
    ],
    cta: "Upgrade to Live",
    ctaHref: "/register",
    highlight: true,
  },
];

export default function PricingPage() {
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

      <div className="max-w-4xl mx-auto px-8 py-24">
        <h1 className="text-4xl font-bold text-center mb-4">Simple, Transparent Pricing</h1>
        <p className="text-center text-zinc-400 mb-16">
          Simulation is always free. Live trading is fee-only — no subscription, no hidden charges.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`rounded-2xl border p-8 ${
                tier.highlight
                  ? "border-blue-600 bg-zinc-900 ring-1 ring-blue-600/30"
                  : "border-zinc-800 bg-zinc-900"
              }`}
            >
              {tier.highlight && (
                <span className="inline-block mb-4 px-3 py-1 rounded-full bg-blue-950 border border-blue-800 text-blue-400 text-xs font-medium">
                  LIVE TRADING
                </span>
              )}
              <h2 className="text-2xl font-bold mb-1">{tier.name}</h2>
              <div className="text-3xl font-bold text-blue-400 mb-1">{tier.price}</div>
              <div className="text-xs text-zinc-500 mb-4">{tier.priceNote}</div>
              <p className="text-zinc-400 text-sm mb-6">{tier.description}</p>
              <ul className="space-y-3 mb-8">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-zinc-300">
                    <span className="text-green-400 mt-0.5">✓</span>
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href={tier.ctaHref}
                className={`block text-center py-3 rounded-lg font-medium transition-colors ${
                  tier.highlight
                    ? "bg-blue-600 hover:bg-blue-500"
                    : "border border-zinc-700 hover:border-zinc-500 text-zinc-300"
                }`}
              >
                {tier.cta}
              </Link>
            </div>
          ))}
        </div>

        <div className="mt-16 p-6 rounded-xl bg-zinc-900 border border-zinc-800">
          <h3 className="font-semibold mb-2">Fee Notes</h3>
          <ul className="text-sm text-zinc-400 space-y-1">
            <li>• Fees are charged per executed trade and deducted from your balance automatically.</li>
            <li>• No fees are charged on simulated trades.</li>
            <li>• Withdrawal fees depend on the blockchain network (shown at time of withdrawal).</li>
            <li>• Fee rates may be updated with 14 days&apos; notice.</li>
            <li>• All fees are inclusive of VAT where applicable.</li>
          </ul>
        </div>

        {/* Footer links */}
        <div className="mt-12 text-center text-xs text-zinc-500 flex justify-center gap-6">
          <Link href="/terms" className="hover:text-zinc-300">Terms</Link>
          <Link href="/risk-disclosure" className="hover:text-zinc-300">Risk Disclosure</Link>
          <Link href="/faq" className="hover:text-zinc-300">FAQ</Link>
        </div>
      </div>
    </div>
  );
}
