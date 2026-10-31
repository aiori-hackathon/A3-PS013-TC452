import { useState, type FormEvent } from "react";
import { Link2, ArrowRight, AlertTriangle } from "lucide-react";
import { api, jsonBody, type Evidence } from "./types";

type Proposal = {
  id: string;
  offset_seconds: number;
  uncertainty_seconds: number;
  residual_seconds: number;
  span_seconds: number;
  limitation: string;
  pairs: {
    identifier: string;
    target_record_id: string;
    reference_record_id: string;
    target_utc: string;
    reference_corrected: string;
    delta_seconds: number;
  }[];
};

export default function Calibration({
  caseId,
  target,
  evidence,
  onApplied,
}: {
  caseId: string;
  target: Evidence;
  evidence: Evidence[];
  onApplied: () => void;
}) {
  const [reference, setReference] = useState(""),
    [proposal, setProposal] = useState<Proposal | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const base = `/investigations/${caseId}/calibration/proposals`;
  async function preview(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(e.currentTarget);
    try {
      setProposal(
        await api<Proposal>(base, {
          method: "POST",
          ...jsonBody({
            evidence_id: target.id,
            reference_id: reference,
            same_event_basis: form.get("basis"),
          }),
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function approve(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(e.currentTarget);
    try {
      await api(base + `/${proposal!.id}/approve`, {
        method: "POST",
        ...jsonBody({ reason: form.get("approval") }),
      });
      onApplied();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="calibration">
      <div className="section-heading">
        <div>
          <h2>
            <Link2 size={17} /> Anchor-based proposal
          </h2>
          <p>
            Optional. A shared ID alone does not establish a valid clock anchor.
          </p>
        </div>
      </div>
      {error && (
        <div className="banner error" role="alert">
          <AlertTriangle size={17} />
          {error}
        </div>
      )}
      {!proposal ? (
        <form onSubmit={preview}>
          <p className="subtitle">
            Use only when repeated IDs denote the same event on distinct
            sources, with negligible systematic logging delay. Three unique
            anchors spanning at least 60 seconds are required; inconsistent
            matches are rejected.
          </p>
          <label>
            Reference evidence
            <select
              aria-label="Reference evidence"
              required
              value={reference}
              onChange={(e) => setReference(e.target.value)}
            >
              <option value="">Choose a trusted reference clock</option>
              {evidence
                .filter((e) => e.id !== target.id && e.source !== target.source)
                .map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.source} · {e.filename}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Why do these identifiers denote the same events?
            <textarea
              name="basis"
              aria-label="Same-event anchor basis"
              required
              minLength={20}
              maxLength={2000}
              rows={3}
              placeholder="Explain the identifier semantics, reference clock, and logging latency."
            />
          </label>
          <button className="secondary full" disabled={busy || !reference}>
            {busy ? "Checking anchors…" : "Preview supported correction"}
            <ArrowRight size={16} />
          </button>
        </form>
      ) : (
        <form onSubmit={approve}>
          <div className="info-strip">
            Proposed correction: {proposal.offset_seconds > 0 ? "+" : ""}
            {proposal.offset_seconds}s · uncertainty ±
            {proposal.uncertainty_seconds}s<br />
            {proposal.pairs.length} anchors · span {proposal.span_seconds}s ·
            largest residual {proposal.residual_seconds}s
          </div>
          <p className="subtitle">{proposal.limitation}</p>
          <div className="anchor-list">
            {proposal.pairs.map((p) => (
              <details key={p.identifier}>
                <summary>
                  {p.identifier} · {p.delta_seconds > 0 ? "+" : ""}
                  {p.delta_seconds}s
                </summary>
                <pre>
                  Target UTC: {p.target_utc}
                  {"\n"}Reference corrected: {p.reference_corrected}
                  {"\n"}Target event: {p.target_record_id}
                  {"\n"}Reference event: {p.reference_record_id}
                </pre>
              </details>
            ))}
          </div>
          <label>
            Investigator approval reason
            <textarea
              name="approval"
              aria-label="Anchor approval reason"
              required
              minLength={10}
              maxLength={2000}
              rows={2}
            />
          </label>
          <div className="button-row">
            <button
              className="secondary"
              type="button"
              onClick={() => setProposal(null)}
              disabled={busy}
            >
              Discard preview
            </button>
            <button className="primary" disabled={busy}>
              {busy ? "Applying…" : "Approve & apply correction"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
