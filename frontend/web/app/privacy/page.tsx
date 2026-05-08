export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950 py-16 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-white mb-2">Privacy Policy</h1>
        <p className="text-sm text-zinc-500 mb-8">
          Effective date: [Date upon VARA approval] &nbsp;·&nbsp; Data Controller: [Company Name],
          Dubai, UAE
        </p>

        <Section title="1. Data We Collect">
          <p>We collect the following categories of personal data:</p>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>
              <strong>Identity:</strong> full name, email, phone, date of birth, nationality,
              government ID, selfie
            </li>
            <li>
              <strong>Financial:</strong> wallet addresses, transaction history, order history,
              portfolio balances
            </li>
            <li>
              <strong>Technical:</strong> IP address, device type, login timestamps, API logs
            </li>
            <li>
              <strong>Communications:</strong> support correspondence, email preferences
            </li>
          </ul>
        </Section>

        <Section title="2. How We Use Your Data">
          <table className="w-full text-sm border-collapse mt-2">
            <thead>
              <tr className="border-b border-zinc-200 dark:border-zinc-700">
                <th className="text-left py-2 text-zinc-600 dark:text-zinc-400">Purpose</th>
                <th className="text-left py-2 text-zinc-600 dark:text-zinc-400">Legal Basis</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {[
                ["Account registration & auth", "Contract performance"],
                ["KYC verification & AML screening", "Legal obligation (VARA / FATF)"],
                ["Order execution & portfolio", "Contract performance"],
                ["Fee calculation & invoicing", "Contract performance"],
                ["VARA regulatory reporting", "Legal obligation"],
                ["Fraud prevention & sanctions", "Legitimate interest / Legal obligation"],
                ["Marketing (with consent)", "Consent"],
              ].map(([purpose, basis]) => (
                <tr key={purpose}>
                  <td className="py-2 pr-4 text-zinc-700 dark:text-zinc-300">{purpose}</td>
                  <td className="py-2 text-zinc-700 dark:text-zinc-300">{basis}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        <Section title="3. Data Retention">
          <table className="w-full text-sm border-collapse mt-2">
            <thead>
              <tr className="border-b border-zinc-200 dark:border-zinc-700">
                <th className="text-left py-2 text-zinc-600 dark:text-zinc-400">Category</th>
                <th className="text-left py-2 text-zinc-600 dark:text-zinc-400">Retention</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {[
                ["KYC documents", "5 years after account closure"],
                ["Transaction records", "5 years"],
                ["Audit logs", "2 years"],
                ["Support communications", "3 years"],
                ["Marketing data", "Until consent withdrawn"],
              ].map(([cat, ret]) => (
                <tr key={cat}>
                  <td className="py-2 pr-4 text-zinc-700 dark:text-zinc-300">{cat}</td>
                  <td className="py-2 text-zinc-700 dark:text-zinc-300">{ret}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        <Section title="4. Data Sharing">
          <ul className="list-disc pl-5 space-y-1">
            <li>
              <strong>Binance:</strong> Order execution data shared for live trade routing.
            </li>
            <li>
              <strong>KYC / AML providers:</strong> Identity documents shared with accredited
              providers for verification.
            </li>
            <li>
              <strong>Regulatory authorities:</strong> VARA, UAE Central Bank, and law enforcement
              upon valid legal request.
            </li>
            <li>We do not sell your personal data to any third party.</li>
          </ul>
        </Section>

        <Section title="5. Your Rights">
          <p>
            You have the right to access, correct, delete, or port your personal data. You may also
            withdraw consent for marketing at any time. To exercise these rights, contact{" "}
            <a
              href="mailto:privacy@[domain]"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              privacy@[domain]
            </a>
            .
          </p>
        </Section>

        <Section title="6. Security">
          <p>
            All data in transit is encrypted via TLS 1.2+. Passwords are stored using bcrypt.
            Access to personal data is role-based and fully audited. We conduct regular penetration
            testing.
          </p>
        </Section>

        <Section title="7. Cookies">
          <p>
            We use only essential cookies for authentication (HttpOnly, Secure). We do not use
            tracking or advertising cookies.
          </p>
        </Section>

        <Section title="8. Contact">
          <p>
            Data Protection Officer:{" "}
            <a
              href="mailto:dpo@[domain]"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              dpo@[domain]
            </a>
          </p>
        </Section>

        <p className="mt-12 text-xs text-zinc-400">
          [Company Name] is regulated by VARA under [Licence Number].
        </p>

        <div className="mt-8 pt-8 border-t border-zinc-200 dark:border-zinc-800 text-sm text-zinc-500 flex gap-4">
          <a href="/terms" className="hover:underline">
            Terms of Service
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
