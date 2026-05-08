import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-zinc-800">
        <span className="text-xl font-bold tracking-tight">XChange</span>
        <div className="flex items-center gap-6 text-sm">
          <Link href="/features" className="text-zinc-400 hover:text-white transition-colors">
            Features
          </Link>
          <Link href="/pricing" className="text-zinc-400 hover:text-white transition-colors">
            Pricing
          </Link>
          <Link href="/faq" className="text-zinc-400 hover:text-white transition-colors">
            FAQ
          </Link>
          <Link
            href="/login"
            className="px-4 py-2 rounded-lg border border-zinc-700 text-sm hover:border-zinc-400 transition-colors"
          >
            Log In
          </Link>
          <Link
            href="/register"
            className="px-4 py-2 rounded-lg bg-blue-600 text-sm font-medium hover:bg-blue-500 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-8 py-32 text-center">
        <div className="inline-block mb-6 px-3 py-1 rounded-full bg-blue-950 border border-blue-800 text-blue-400 text-xs font-medium tracking-wide uppercase">
          VARA Licensed · Dubai, UAE
        </div>
        <h1 className="text-5xl font-bold leading-tight tracking-tight mb-6">
          Learn to trade crypto.
          <br />
          <span className="text-blue-400">Without the risk.</span>
        </h1>
        <p className="text-lg text-zinc-400 max-w-2xl mx-auto mb-10">
          Start with our risk-free simulation mode. Master the markets with real prices and real
          order mechanics — then go live when you&apos;re ready.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/register"
            className="px-6 py-3 rounded-lg bg-blue-600 font-medium hover:bg-blue-500 transition-colors"
          >
            Start Trading for Free
          </Link>
          <Link
            href="/features"
            className="px-6 py-3 rounded-lg border border-zinc-700 text-zinc-300 hover:border-zinc-500 transition-colors"
          >
            See How It Works
          </Link>
        </div>
      </section>

      {/* Feature highlights */}
      <section className="max-w-5xl mx-auto px-8 pb-24 grid grid-cols-1 md:grid-cols-3 gap-8">
        {[
          {
            icon: "📊",
            title: "Paper Trading",
            desc: "Practice with real live market prices and real order mechanics, but simulated funds. No risk, all the learning.",
          },
          {
            icon: "🔒",
            title: "KYC-Secured Live Trading",
            desc: "When you're ready to trade real funds, complete KYC and unlock live trading — regulated by VARA.",
          },
          {
            icon: "⚡",
            title: "Spot & Futures",
            desc: "Trade BTC, ETH, and more on spot. Advanced traders can access leveraged futures when approved.",
          },
        ].map((f) => (
          <div
            key={f.title}
            className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 hover:border-zinc-700 transition-colors"
          >
            <div className="text-3xl mb-4">{f.icon}</div>
            <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
            <p className="text-zinc-400 text-sm leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 px-8 py-8 text-center text-xs text-zinc-500">
        <div className="flex justify-center gap-6 mb-4">
          <Link href="/terms" className="hover:text-zinc-300 transition-colors">Terms</Link>
          <Link href="/privacy" className="hover:text-zinc-300 transition-colors">Privacy</Link>
          <Link href="/risk-disclosure" className="hover:text-zinc-300 transition-colors">Risk Disclosure</Link>
          <Link href="/faq" className="hover:text-zinc-300 transition-colors">FAQ</Link>
        </div>
        <p>© {new Date().getFullYear()} [Company Name]. All rights reserved.</p>
        <p className="mt-1">Regulated by VARA under [Licence Number]. Dubai, UAE.</p>
      </footer>
    </div>
  );
}
