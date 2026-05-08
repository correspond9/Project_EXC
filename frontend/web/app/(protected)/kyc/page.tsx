"use client";

import { useMemo, useState } from "react";
import api from "@/lib/api";

type KycStatus = "PENDING" | "SUBMITTED" | "APPROVED" | "REJECTED";
type KycDocType = "PASSPORT" | "EMIRATES_ID" | "SELFIE" | "PROOF_OF_ADDRESS";

interface KycDocInput {
  document_type: KycDocType;
  file_reference: string;
}

const DOC_TYPES: KycDocType[] = [
  "PASSPORT",
  "EMIRATES_ID",
  "SELFIE",
  "PROOF_OF_ADDRESS",
];

export default function KycPage() {
  const [kycStatus, setKycStatus] = useState<KycStatus | null>(null);
  const [docs, setDocs] = useState<KycDocInput[]>([
    { document_type: "PASSPORT", file_reference: "" },
    { document_type: "SELFIE", file_reference: "" },
  ]);
  const [msg, setMsg] = useState<string>("");
  const [busy, setBusy] = useState(false);

  const submitReady = useMemo(
    () => docs.every((d) => d.file_reference.trim().length > 0),
    [docs],
  );

  async function refreshStatus() {
    try {
      const res = await api.get("/api/kyc/status");
      setKycStatus(res.data.kyc_status as KycStatus);
    } catch {
      setMsg("Unable to load KYC status.");
    }
  }

  async function submitKyc() {
    if (!submitReady) return;
    setBusy(true);
    setMsg("");
    try {
      const payload = {
        documents: docs.map((d) => ({
          document_type: d.document_type,
          file_reference: d.file_reference.trim(),
        })),
      };
      const res = await api.post("/api/kyc/submit", payload);
      setKycStatus(res.data.kyc_status as KycStatus);
      setMsg("KYC submitted successfully.");
    } catch (err: any) {
      setMsg(err?.response?.data?.detail || "KYC submission failed.");
    } finally {
      setBusy(false);
    }
  }

  function updateDoc(index: number, field: keyof KycDocInput, value: string) {
    setDocs((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  }

  function addDoc() {
    setDocs((prev) => [...prev, { document_type: "PROOF_OF_ADDRESS", file_reference: "" }]);
  }

  function removeDoc(index: number) {
    setDocs((prev) => prev.filter((_, i) => i !== index));
  }

  return (
    <section style={{ maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ fontSize: "1.8rem", marginBottom: 8 }}>KYC Verification</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 16 }}>
        Submit document references for verification. LIVE mode remains locked until approval.
      </p>

      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <button onClick={refreshStatus} style={buttonStyle}>Refresh Status</button>
        <span style={{ alignSelf: "center", color: "var(--text-muted)" }}>
          Current status: <strong>{kycStatus ?? "Unknown"}</strong>
        </span>
      </div>

      <div style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
        {docs.map((doc, index) => (
          <div key={index} style={{ display: "grid", gridTemplateColumns: "180px 1fr auto", gap: 10, marginBottom: 10 }}>
            <select
              value={doc.document_type}
              onChange={(e) => updateDoc(index, "document_type", e.target.value)}
              aria-label="Document type"
              style={inputStyle}
            >
              {DOC_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <input
              value={doc.file_reference}
              onChange={(e) => updateDoc(index, "file_reference", e.target.value)}
              placeholder="Object storage key, URL, or upload reference"
              aria-label="File reference"
              style={inputStyle}
            />
            <button onClick={() => removeDoc(index)} style={dangerButtonStyle} disabled={docs.length <= 1}>
              Remove
            </button>
          </div>
        ))}

        <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
          <button onClick={addDoc} style={buttonStyle}>Add Document</button>
          <button
            onClick={submitKyc}
            disabled={!submitReady || busy}
            style={{ ...buttonStyle, opacity: !submitReady || busy ? 0.6 : 1 }}
          >
            {busy ? "Submitting..." : "Submit KYC"}
          </button>
        </div>
      </div>

      {msg && (
        <p style={{ marginTop: 14, color: msg.includes("failed") ? "#f87171" : "#86efac" }}>
          {msg}
        </p>
      )}
    </section>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.55rem 0.7rem",
  border: "1px solid var(--border)",
  borderRadius: 8,
  background: "var(--bg-secondary)",
  color: "var(--text-primary)",
};

const buttonStyle: React.CSSProperties = {
  padding: "0.55rem 0.9rem",
  borderRadius: 8,
  border: "1px solid var(--border)",
  background: "var(--bg-secondary)",
  color: "var(--text-primary)",
  cursor: "pointer",
};

const dangerButtonStyle: React.CSSProperties = {
  ...buttonStyle,
  border: "1px solid #ef4444",
  color: "#fecaca",
};
