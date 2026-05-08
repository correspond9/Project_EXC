export default function TermsPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950 py-16 px-4">
      <div className="max-w-3xl mx-auto prose dark:prose-invert">
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-white mb-2">
          Terms of Service
        </h1>
        <p className="text-sm text-zinc-500 mb-8">
          Effective date: [Date upon VARA approval] &nbsp;·&nbsp; Last updated: [Date]
        </p>

        <Section title="1. Acceptance of Terms">
          By registering an account on the XChange Platform you agree to be bound by these Terms of
          Service. If you do not agree, you may not use the Platform.
        </Section>

        <Section title="2. Eligibility">
          <ul className="list-disc pl-5 space-y-1 text-zinc-700 dark:text-zinc-300">
            <li>You must be at least 18 years of age.</li>
            <li>You must reside in a jurisdiction where virtual asset trading is legally permitted.</li>
            <li>
              You must successfully complete KYC verification before conducting any live trades.
            </li>
            <li>
              You must not be a citizen or resident of any sanctioned country (OFAC / FATF
              high-risk list).
            </li>
          </ul>
        </Section>

        <Section title="3. Account Registration & KYC">
          <p>
            Live trading is only available after KYC approval. KYC requires a government-issued photo
            ID, proof of address, and a selfie / liveness check. We reserve the right to request
            additional documents at any time for ongoing AML/CFT compliance.
          </p>
        </Section>

        <Section title="4. Trading Services">
          <p>
            <strong>Simulation Mode</strong> is available to all registered users. Simulated balances
            have no real monetary value.
          </p>
          <p>
            <strong>Live Mode</strong> is available only to KYC-approved users. Real funds are at
            risk. All trading involves significant risk of loss, including loss of your entire
            investment.
          </p>
          <p>
            We route live orders through Binance. We do not guarantee execution at any specific price.
            Leverage trading magnifies both gains and losses.
          </p>
        </Section>

        <Section title="5. Fees">
          <p>
            Trading fees apply to all live executed orders. The current fee schedule is published on
            our{" "}
            <a href="/pricing" className="text-blue-600 dark:text-blue-400 hover:underline">
              Pricing
            </a>{" "}
            page. Fees are non-refundable once a trade is executed.
          </p>
        </Section>

        <Section title="6. Deposits & Withdrawals">
          <p>
            Deposits are credited after blockchain confirmation and internal review. Withdrawals are
            subject to minimum amounts, identity verification, admin review, and AML/CFT checks. We
            may delay or refuse withdrawals where we reasonably suspect fraud or AML violations.
          </p>
        </Section>

        <Section title="7. Risk Disclosure">
          <p>
            Virtual asset trading carries substantial risk. You may lose your entire invested
            capital. Past performance is not indicative of future results. We do not provide
            investment advice. See our full{" "}
            <a
              href="/risk-disclosure"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Risk Disclosure
            </a>
            .
          </p>
        </Section>

        <Section title="8. Prohibited Activities">
          <ul className="list-disc pl-5 space-y-1 text-zinc-700 dark:text-zinc-300">
            <li>Money laundering, terrorist financing, or sanctions evasion</li>
            <li>Market price manipulation or wash trading</li>
            <li>Accessing the Platform from sanctioned jurisdictions</li>
            <li>Sharing account credentials with third parties</li>
          </ul>
        </Section>

        <Section title="9. Limitation of Liability">
          <p>
            To the maximum extent permitted by law, [Company Name] shall not be liable for trading
            losses, technical outages, Binance downtime, or any indirect or consequential damages.
          </p>
        </Section>

        <Section title="10. Governing Law">
          <p>
            These Terms are governed by the laws of the Emirate of Dubai and the UAE. Any disputes
            shall be submitted to the exclusive jurisdiction of the Dubai courts.
          </p>
        </Section>

        <Section title="11. Contact">
          <p>
            Questions? Email us at{" "}
            <a
              href="mailto:legal@[domain]"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              legal@[domain]
            </a>
          </p>
        </Section>

        <p className="mt-12 text-xs text-zinc-400">
          [Company Name] is regulated by VARA under [Licence Number].
        </p>

        <div className="mt-8 pt-8 border-t border-zinc-200 dark:border-zinc-800 text-sm text-zinc-500 flex gap-4">
          <a href="/privacy" className="hover:underline">
            Privacy Policy
          </a>
          <a href="/risk-disclosure" className="hover:underline">
            Risk Disclosure
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
