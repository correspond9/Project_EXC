import Link from "next/link";

const STEPS = [
  {
    number: 1,
    title: "Create your account",
    description:
      "Register with your email address and set a strong password. You'll receive a verification email — click the link to confirm your account.",
    cta: "Register Now",
    ctaHref: "/register",
    icon: "📝",
  },
  {
    number: 2,
    title: "Verify your email",
    description:
      "Check your inbox for a verification email from XChange. Click the confirmation link to activate your account. Check spam if you don't see it within 2 minutes.",
    cta: null,
    ctaHref: null,
    icon: "📧",
  },
  {
    number: 3,
    title: "Complete KYC verification",
    description:
      "To trade with real funds, you must verify your identity. Go to Settings → Verification and upload a government-issued ID, a proof of address, and a selfie. Our team reviews submissions within 1 business day.",
    cta: null,
    ctaHref: null,
    icon: "🪪",
  },
  {
    number: 4,
    title: "Start trading",
    description:
      "Once KYC is approved, your account is unlocked for live trading. Deposit crypto, enable Live mode, and place your first real trade. You can also continue using Simulation mode at any time — no real money required.",
    cta: null,
    ctaHref: null,
    icon: "🚀",
  },
];

export default function OnboardingPage() {
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
        <h1 className="text-4xl font-bold mb-4">How to get started</h1>
        <p className="text-zinc-400 mb-16">
          From sign-up to your first live trade — here&apos;s the full journey.
        </p>

        <div className="relative">
          {/* Vertical connector line */}
          <div className="absolute left-6 top-8 bottom-8 w-0.5 bg-zinc-800" />

          <div className="space-y-8">
            {STEPS.map((step, i) => (
              <div key={step.number} className="relative flex gap-6">
                {/* Step circle */}
                <div
                  className={`z-10 flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold border-2 ${
                    i === 0
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "bg-zinc-900 border-zinc-700 text-zinc-400"
                  }`}
                >
                  {step.number}
                </div>

                {/* Content */}
                <div className="flex-1 pb-4">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{step.icon}</span>
                    <h3 className="text-lg font-semibold">{step.title}</h3>
                  </div>
                  <p className="text-zinc-400 text-sm leading-relaxed mb-4">
                    {step.description}
                  </p>
                  {step.cta && step.ctaHref && (
                    <Link
                      href={step.ctaHref}
                      className="inline-block px-5 py-2 rounded-lg bg-blue-600 text-sm font-medium hover:bg-blue-500 transition-colors"
                    >
                      {step.cta} →
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Simulation mode note */}
        <div className="mt-16 p-6 rounded-xl bg-zinc-900 border border-zinc-800">
          <h3 className="font-semibold mb-2">No KYC? No problem.</h3>
          <p className="text-sm text-zinc-400 leading-relaxed">
            You can start practising in <strong className="text-white">Simulation mode</strong> immediately
            after email verification — no KYC required. Simulation uses real live market prices with
            virtual funds. It&apos;s completely free and a great way to build confidence before going live.
          </p>
          <Link
            href="/register"
            className="inline-block mt-4 px-5 py-2 rounded-lg border border-zinc-700 text-sm hover:border-zinc-500 transition-colors"
          >
            Start Simulating for Free →
          </Link>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center text-xs text-zinc-500 flex justify-center gap-6">
          <Link href="/terms" className="hover:text-zinc-300">Terms</Link>
          <Link href="/risk-disclosure" className="hover:text-zinc-300">Risk Disclosure</Link>
          <Link href="/pricing" className="hover:text-zinc-300">Pricing</Link>
          <Link href="/faq" className="hover:text-zinc-300">FAQ</Link>
        </div>
      </div>
    </div>
  );
}
