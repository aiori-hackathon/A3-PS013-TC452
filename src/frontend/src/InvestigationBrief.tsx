import { useEffect, useState } from "react";
import { api, type EventRecord, type Evidence, type Investigation, type Lead, type Verification } from "./types";

type Props = {
  investigation: Investigation; files: Evidence[]; leads: Lead[]; checks: Verification[];
  inspect: (id: string) => void; review: () => void; verify: () => void; busy: boolean;
};
type Page = { items: EventRecord[]; total: number };
export const utc = (value: string) => value.replace("T", " ").replace(".000000Z", "Z");
export const signed = (value: number) => (value > 0 ? "+" : "") + value;

export default function InvestigationBrief({ investigation, files, leads, checks, inspect, review, verify, busy }: Props) {
  const [open, setOpen] = useState(false);
  const [observations, setObservations] = useState<EventRecord[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    const timeline = (query: string) => api<Page>(`/investigations/${investigation.id}/timeline?limit=1&${query}`, { signal: controller.signal });
    async function load() {
      setError("");
      setObservations(null);
      const first = await timeline("");
      if (!first.total) { setObservations([]); return; }
      const samples = await Promise.all([timeline("kind=web"), timeline("kind=auth"), timeline("kind=system"), timeline("offset=" + (first.total - 1))]);
      const rows = [first, ...samples].flatMap(page => page.items);
      setObservations([...new Map(rows.map(row => [row.id, row])).values()].sort((a,b) => a.corrected_timestamp.localeCompare(b.corrected_timestamp)));
    }
    load().catch(err => { if (!controller.signal.aborted) setError(err.message); });
    return () => controller.abort();
  }, [open, investigation.id, files]);
  const failed = checks.filter(check => check.status !== "verified");
  const complete = files.length > 0 && files.every(file => checks.some(c => c.evidence_id === file.id && c.status === "verified"));
  const clocks = files.filter(file => file.offset_seconds || file.uncertainty_seconds);
  const gapCount = files.reduce((n, f) => n + f.gap_records, 0);
  return <section className="card case-brief">
    <button className="brief-toggle" aria-expanded={open} onClick={() => setOpen(!open)}>
      <strong>Investigation Brief</strong><span>{open ? "Collapse" : "Open overview"} {open ? "▴" : "▾"}</span>
    </button>
    {open && <div className="brief-content">
      <h2>{investigation.name}</h2><p>{investigation.description}</p>
      <p className="brief-stats">{new Set(files.map(f => f.source)).size} sources · {files.length} files · {files.reduce((n,f) => n+f.parsed_records,0)} normalized events · {gapCount} parsing {gapCount === 1 ? "gap" : "gaps"} · {leads.length} investigative leads</p>
      <div className="button-row"><strong className={failed.length ? "tag critical" : complete ? "tag good" : "subtle-pill"}>
        {failed.length ? "Integrity check failed: " + failed.map(c => c.filename + " (" + c.status + ")").join(", ") : complete ? "Verified at " + utc(checks[0].checked_at) : "Integrity: Not checked"}
      </strong><button className="text-button" disabled={busy || !files.length} onClick={verify}>Check integrity</button></div>
      <h3>Observed activity</h3>
      {error ? <p role="alert">{error}</p> : observations === null ? <p>Reading timeline…</p> : observations.length === 0 ? <p>No normalized observations.</p> : <>
        <p><strong>Corrected UTC range</strong> {utc(observations[0].corrected_timestamp)} — {utc(observations[observations.length-1].corrected_timestamp)}</p>
        <p>First observation of each record type and case boundaries. Equal times and overlapping intervals leave order unresolved.</p>
        <ul>{observations.map(row => <li key={row.id}><time>{utc(row.corrected_timestamp)}</time> · {row.message} <button className="text-button" onClick={() => inspect(row.id)}>{row.source} · {row.filename} line {row.line_number}</button></li>)}</ul>
      </>}
      <details><summary>Clock assumptions ({clocks.length} files with offsets or bounds)</summary>
        {files.length ? files.map(f => <p key={f.id}>{f.source} · {f.filename} · {signed(f.offset_seconds)} s · supplied ±{f.uncertainty_seconds} s · {f.correction_reason}</p>) : <p>No source clocks imported.</p>}
      </details>
      <h3>Requires investigator review</h3>
      {leads.length === 0 ? <p>No investigative leads.</p> : <><ul>{leads.slice(0,4).map(l => <li key={l.type+l.record_ids[0]}><strong>{l.title}</strong> · {l.priority} · {l.references.length} supporting events<br/>
        <p>{l.message}{l.ip && " Source IP: " + l.ip + "."}</p>
        <time>{utc(l.start)}{l.start !== l.end && " — " + utc(l.end)}</time><div className="button-row">{l.references.slice(0,3).map(r => <button className="text-button" key={r.id} onClick={() => inspect(r.id)}>{r.source} · {r.filename} line {r.line_number}</button>)}</div></li>)}</ul>
        <button className="secondary" onClick={review}>Review all {leads.length} leads and supporting records</button></>}
      <h3>Not established</h3><p>Shared IPs and nearby timestamps cannot identify an actor or establish causation. HTTP success alone cannot establish exfiltration. Timing depends on source-clock assumptions, and unsupported or missing records limit reconstruction.</p>
    </div>}
  </section>;
}
