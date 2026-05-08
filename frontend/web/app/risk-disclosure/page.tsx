export default function RiskDisclosurePage() {
  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950 py-16 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Warning banner */}
        <div className="mb-8 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 px-6 py-4">
          <p className="text-amber-800 dark:text-amber-300 font-semibold text-sm">
            ⚠ Important: Virtual asset trading is highly speculative. You may lose your entire
            investment. Please read this document carefully before trading with real funds.
          </p>
        </div>

        <h1 className="text-3xl font-bold text-zinc-900 dark:text-white mb-2">
          Risk Disclosure Statement
        </h1>
        <p className="text-sm text-zinc-500 mb-8">
          Effective date: [Date upon VARA approval]
        </p>

        <Section title="1. Market Risk">
          Virtual asset prices are extremely volatile and can change rapidly and unpredictably.
          Factors include regulatory announcements, technology events, market sentiment, and
          macroeconomic conditions. Past performance is not indicative of future results.
        </Section>

        <Section title="2. Leverage Risk">
          Leveraged futures trading amplifies both potential gains and potential losses. A position
          with 10× leverage means a 10% adverse price move results in a 100% loss of your margin.
          Your position may be automatically liquidated if your margin balance falls below the
          maintenance margin requirement. You may lose your entire margin deposit.
          <p className="mt-2 font-medium text-amber-700 dark:text-amber-400">
            We strongly advise inexperienced traders to avoid leveraged trading.
          </p>
        </Section>

        <Section title="3. Liquidity Risk">
          There may be situations where you are unable to close a position at a desired price due
          to insufficient market liquidity. During periods of high volatility, slippage between the
          quoted price and the execution price may be significant.
        </Section>

        <Section title="4. Technology & Operational Risk">
          The Platform may experience downtime, technical errors, or connectivity issues. Exchange
          API disruptions (Binance) may delay or prevent order execution. Software issues could
          affect order routing or balance calculation. We are not liable for losses arising from
          technical failures beyond our reasonable control.
        </Section>

        <Section title="5. Counterparty Risk">
          Live orders are routed to Binance. Your funds on Binance are subject to Binance&apos;s
          terms, security practices, and regulatory status. In the event of a Binance insolvency or
          regulatory action, your funds held on Binance may be at risk.
        </Section>

        <Section title="6. Regulatory Risk">
          The regulatory landscape for virtual assets is rapidly evolving. Future changes in the
          UAE or in the jurisdictions where your underlying assets are held may adversely affect
          your ability to trade, the value of your assets, or the operation of the Platform.
        </Section>

        <Section title="7. Cybersecurity Risk">
          Your account could be compromised if your credentials are stolen. We strongly recommend
          enabling two-factor authentication (2FA) and never sharing your password with anyone. Be
          vigilant of phishing attempts — we will never ask for your password by email.
        </Section>

        <Section title="8. No Investment Advice">
          Nothing on the XChange Platform constitutes investment advice or any recommendation to
          buy or sell any virtual asset. You should seek independent professional advice before
          making any trading decisions.
        </Section>

        <Section title="9. Your Acknowledgement">
          By using the Platform in Live mode you confirm that you have read and understood this
          Risk Disclosure Statement, you understand you may lose your entire investment, you are
          trading with funds you can afford to lose, and you are making independent trading
          decisions.
        </Section>

        <p className="mt-12 text-xs text-zinc-400">
          [Company Name] is regulated by VARA under [Licence Number].
        </p>

        <div className="mt-8 pt-8 border-t border-zinc-200 dark:border-zinc-800 text-sm text-zinc-500 flex gap-4">
          <a href="/terms" className="hover:underline">
            Terms of Service
          </a>
          <a href="/privacy" className="hover:underline">
            Privacy Policy
          </a>
          <a href="/" className="hover:underline">
            Back to Platform
          </a>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <h2 className="text-xl font-semibold text-zinc-800 dark:text-zinc-100 mb-3">{title}</h2>
      <div className="text-zinc-700 dark:text-zinc-300 leading-7 space-y-2">{children}</div>
    </div>
  );
}
