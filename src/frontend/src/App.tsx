import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  Check,
  CheckCheck,
  ChevronLeft,
  ChevronRight,
  Clock3,
  FileText,
  Fingerprint,
  FolderPlus,
  HardDrive,
  Layers3,
  ListFilter,
  LockKeyhole,
  Plus,
  Search,
  ShieldCheck,
  ShieldQuestion,
  UploadCloud,
  X,
  AlertTriangle,
  SlidersHorizontal,
} from "lucide-react";
import Calibration from "./Calibration";
import {
  api,
  jsonBody,
  type Investigation,
  type Evidence,
  type EventRecord,
  type Verification,
  type Finding,
  type Audit,
} from "./types";

type Association = {
  identifier: string;
  record_ids: string[];
  message: string;
};
type Tab = "timeline" | "evidence" | "gaps" | "verify";
const time = (v: string) =>
  v ? v.replace("T", " ").replace(".000000", "") : "—";
const bytes = (n: number) =>
  n >= 1024 ? `${(n / 1024).toFixed(1)} KB` : `${n} B`;

function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      className="modal"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <div className="modal-head">
        <h2>{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}

export default function App() {
  const [cases, setCases] = useState<Investigation[]>([]),
    [caseId, setCaseId] = useState(""),
    [tab, setTab] = useState<Tab>("timeline");
  const [evidence, setEvidence] = useState<Evidence[]>([]),
    [events, setEvents] = useState<EventRecord[]>([]),
    [gaps, setGaps] = useState<EventRecord[]>([]),
    [findings, setFindings] = useState<Finding[]>([]),
    [audit, setAudit] = useState<Audit[]>([]);
  const [associations, setAssociations] = useState<Association[]>([]);
  const [checks, setChecks] = useState<Verification[]>([]),
    [total, setTotal] = useState(0),
    [q, setQ] = useState(""),
    [source, setSource] = useState(""),
    [kind, setKind] = useState(""),
    [start, setStart] = useState(""),
    [end, setEnd] = useState(""),
    [page, setPage] = useState(0);
  const [revision, setRevision] = useState(0),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [creating, setCreating] = useState(false),
    [importing, setImporting] = useState(false),
    [clock, setClock] = useState<Evidence | null>(null),
    [detail, setDetail] = useState<EventRecord | null>(null),
    [files, setFiles] = useState<File[]>([]);
  const [healthy, setHealthy] = useState(false);
  const selected = cases.find((c) => c.id === caseId),
    base = `/investigations/${caseId}`;
  const parsed = evidence.reduce((s, e) => s + e.parsed_records, 0),
    recordCount = evidence.reduce((s, e) => s + e.total_records, 0);

  useEffect(() => {
    api<Investigation[]>("/investigations")
      .then((items) => {
        setCases(items);
        setCaseId(items[0]?.id || "");
      })
      .catch((e) => setError(e.message));
    api<{ status: string }>("/health")
      .then((r) => setHealthy(r.status === "ok"))
      .catch(() => setHealthy(false));
  }, []);
  useEffect(() => {
    setPage(0);
  }, [q, source, kind, start, end, caseId]);
  useEffect(() => {
    setChecks([]);
    setDetail(null);
    setSource("");
    setQ("");
    setKind("");
    setStart("");
    setEnd("");
    setEvidence([]);
    setEvents([]);
    setGaps([]);
    setFindings([]);
    setAssociations([]);
    setTotal(0);
  }, [caseId]);
  useEffect(() => {
    if (!caseId) return;
    const abort = new AbortController();
    Promise.all([
      api<Evidence[]>(base + "/evidence", { signal: abort.signal }),
      api<EventRecord[]>(base + "/gaps", { signal: abort.signal }),
      api<Finding[]>(base + "/findings", { signal: abort.signal }),
      api<Audit[]>(base + "/audit", { signal: abort.signal }),
      api<Association[]>(base + "/relationships", { signal: abort.signal }),
    ])
      .then(([e, g, f, a, r]) => {
        setEvidence(e);
        setGaps(g);
        setFindings(f);
        setAudit(a);
        setAssociations(r);
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => abort.abort();
  }, [caseId, revision]);
  useEffect(() => {
    if (!caseId) return;
    const abort = new AbortController();
    setLoading(true);
    const timer = setTimeout(() => {
      const params = new URLSearchParams({
        q,
        limit: "100",
        offset: String(page * 100),
      });
      if (source) params.set("evidence_id", source);
      if (kind) params.set("kind", kind);
      if (start) params.set("start", start + "Z");
      if (end) params.set("end", end + "Z");
      api<{ items: EventRecord[]; total: number }>(
        base + "/timeline?" + params,
        { signal: abort.signal },
      )
        .then((r) => {
          setEvents(r.items);
          setTotal(r.total);
          setLoading(false);
        })
        .catch((e) => {
          if (e.name !== "AbortError") {
            setError(e.message);
            setLoading(false);
          }
        });
    }, 150);
    return () => {
      clearTimeout(timer);
      abort.abort();
    };
  }, [caseId, revision, q, source, kind, start, end, page]);

  async function action(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function createCase(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await action(async () => {
      const c = await api<Investigation>("/investigations", {
        method: "POST",
        ...jsonBody({
          name: form.get("name"),
          description: form.get("description"),
        }),
      });
      setCases([c, ...cases]);
      setCaseId(c.id);
      setCreating(false);
      setTab("timeline");
      setNotice(
        "Investigation created. Import your first evidence file to begin.",
      );
    });
  }
  async function importFiles(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const options = {
      source: form.get("source"),
      log_format: form.get("format"),
      timezone: form.get("timezone"),
      year: form.get("year") ? Number(form.get("year")) : null,
      offset_seconds: Number(form.get("offset")),
      uncertainty_seconds: Number(form.get("uncertainty")),
      correction_reason: form.get("reason"),
    };
    await action(async () => {
      let completed = 0;
      for (const file of files) {
        const data = new FormData();
        data.append("file", file);
        data.append("options", JSON.stringify(options));
        await api(base + "/evidence", { method: "POST", body: data });
        completed++;
        setFiles((previous) => previous.filter((f) => f !== file));
        setRevision((v) => v + 1);
        setChecks([]);
        setNotice(`Preserved ${completed} file(s).`);
      }
      setImporting(false);
      setTab("evidence");
    });
  }
  async function changeClock(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await action(async () => {
      await api(base + `/evidence/${clock!.id}/clock`, {
        method: "PATCH",
        ...jsonBody({
          offset_seconds: Number(form.get("offset")),
          uncertainty_seconds: Number(form.get("uncertainty")),
          reason: form.get("reason"),
        }),
      });
      setClock(null);
      setRevision((v) => v + 1);
      setNotice(
        "Clock correction saved. Original timestamps and evidence are preserved.",
      );
    });
  }
  function inspect(id: string) {
    action(async () =>
      setDetail(await api<EventRecord>(base + "/records/" + id)),
    );
  }
  const nav: [Tab, typeof Activity, string][] = [
    ["timeline", Activity, "Timeline"],
    ["evidence", Layers3, "Evidence vault"],
    ["gaps", ShieldQuestion, "Gaps & review"],
    ["verify", Fingerprint, "Verify & export"],
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="ALIBI home">
          <div className="brand-mark">
            <Fingerprint size={30} />
          </div>
          <span>
            ALIBI<span className="brand-dot">.</span>
          </span>
        </a>
        <p className="brand-caption">EVIDENCE FIRST. ALWAYS.</p>
        <div className="sidebar-label">
          WORKSPACE <span>LOCAL</span>
        </div>
        <label className="case-label" htmlFor="investigation-select">
          Active investigation
        </label>
        <select
          id="investigation-select"
          value={caseId}
          disabled={busy}
          onChange={(e) => setCaseId(e.target.value)}
        >
          <option value="" disabled>
            Select an investigation
          </option>
          {cases.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <button
          className="new-case"
          onClick={() => setCreating(true)}
          disabled={busy}
        >
          <Plus size={16} /> New investigation
        </button>
        <nav>
          {nav.map(([id, Icon, label]) => (
            <button
              key={id}
              className={tab === id ? "nav-item active" : "nav-item"}
              onClick={() => setTab(id)}
            >
              <Icon size={19} />
              {label}
              {id === "gaps" && gaps.length > 0 && (
                <span className="nav-count">{gaps.length}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <LockKeyhole size={20} />
          <strong>Your evidence stays here.</strong>
          <p>
            Local processing. Original bytes preserved. Every event traceable.
          </p>
        </div>
        <div className="sidebar-footer">
          <span className="team-avatar">EX</span>
          <div>
            <strong>Team EXPOSE</strong>
            <small>AIORI 3 · PS-013</small>
          </div>
          <span className="version">v0.1</span>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Investigations</span>
            <ChevronRight size={14} />
            <strong>{selected?.name || "Getting started"}</strong>
          </div>
          <span className={healthy ? "local-status" : "local-status offline"}>
            <span />
            {healthy ? "Local service connected" : "Backend unavailable"}
          </span>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <p className="eyebrow">INVESTIGATION WORKBENCH</p>
              <h1>
                {
                  {
                    timeline: "Reconstruct the story.",
                    evidence: "Preserve the evidence.",
                    gaps: "Know what is missing.",
                    verify: "Make every finding verifiable.",
                  }[tab]
                }
              </h1>
              <p className="subtitle">
                {
                  {
                    timeline:
                      "A clear chronology. Original records. Assumptions in plain sight.",
                    evidence:
                      "Original files, preserved byte for byte, with a SHA-256 fingerprint.",
                    gaps: "Review parsing failures and conflicting observations before drawing conclusions.",
                    verify:
                      "Check preserved files and export a report with a complete evidence trail.",
                  }[tab]
                }
              </p>
            </div>
            <button
              className="primary"
              disabled={!caseId || busy}
              onClick={() => {
                setFiles([]);
                setImporting(true);
              }}
            >
              <Plus size={17} /> Import evidence
            </button>
          </div>
          {error && (
            <div className="banner error" role="alert">
              <AlertTriangle size={18} />
              <span>{error}</span>
              <button
                className="icon-button"
                onClick={() => setError("")}
                aria-label="Dismiss error"
              >
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <div className="banner success" role="status">
              <Check size={18} />
              {notice}
            </div>
          )}
          {!caseId ? (
            <section className="welcome card">
              <div className="welcome-icon">
                <FolderPlus size={40} />
              </div>
              <p className="eyebrow">A DEFENSIBLE TIMELINE STARTS HERE</p>
              <h2>
                Every incident has a story.
                <br />
                Build yours on evidence.
              </h2>
              <p>
                Create an investigation, import Linux or web server logs, and
                follow each event back to its original source.
              </p>
              <button className="primary" onClick={() => setCreating(true)}>
                <FolderPlus size={18} /> Create investigation
              </button>
              <div className="welcome-steps">
                01 Preserve <ArrowRight size={15} /> 02 Calibrate{" "}
                <ArrowRight size={15} /> 03 Reconstruct <ArrowRight size={15} />{" "}
                04 Challenge <ArrowRight size={15} /> 05 Verify
              </div>
            </section>
          ) : (
            <>
              <section className="stats">
                <div className="stat">
                  <span className="stat-icon mint">
                    <Layers3 size={20} />
                  </span>
                  <div>
                    <small>Evidence files</small>
                    <strong>
                      {evidence.length.toString().padStart(2, "0")}
                    </strong>
                  </div>
                  <span className="stat-foot">
                    {bytes(evidence.reduce((s, e) => s + e.size, 0))} preserved
                  </span>
                </div>
                <div className="stat">
                  <span className="stat-icon blue">
                    <Activity size={20} />
                  </span>
                  <div>
                    <small>Timeline events</small>
                    <strong>{parsed.toLocaleString()}</strong>
                  </div>
                  <span className="stat-foot">
                    {recordCount} records imported
                  </span>
                </div>
                <div className="stat">
                  <span className="stat-icon amber">
                    <ShieldQuestion size={20} />
                  </span>
                  <div>
                    <small>Parsing gaps</small>
                    <strong>{gaps.length.toString().padStart(2, "0")}</strong>
                  </div>
                  <span className="stat-foot">
                    {gaps.length ? "Needs your review" : "No parsing failures"}
                  </span>
                </div>
                <div className="stat">
                  <span className="stat-icon lavender">
                    <Clock3 size={20} />
                  </span>
                  <div>
                    <small>Clock corrections</small>
                    <strong>
                      {evidence
                        .filter((e) => e.offset_seconds !== 0)
                        .length.toString()
                        .padStart(2, "0")}
                    </strong>
                  </div>
                  <span className="stat-foot">
                    Explicit, reviewable offsets
                  </span>
                </div>
              </section>
              <div className="workflow">
                <span>
                  <CheckCheck size={16} /> PRESERVE
                </span>
                <i />
                <span>
                  <Clock3 size={16} /> CALIBRATE
                </span>
                <i />
                <span className="current">
                  <Activity size={16} /> RECONSTRUCT
                </span>
                <i />
                <span>
                  <ShieldQuestion size={16} /> CHALLENGE
                </span>
                <i />
                <span>
                  <Fingerprint size={16} /> VERIFY
                </span>
              </div>
              {tab === "timeline" && (
                <section className="card timeline-card">
                  <div className="section-heading">
                    <div>
                      <h2>
                        Incident timeline <span className="count">{total}</span>
                      </h2>
                      <p>
                        Sorted by corrected UTC time. Select an event to inspect
                        its source.
                      </p>
                    </div>
                    <span className="subtle-pill">
                      <Clock3 size={13} /> UTC
                    </span>
                  </div>
                  <div className="filters">
                    <label className="search">
                      <Search size={18} />
                      <input
                        aria-label="Search timeline"
                        placeholder="Search messages, IP addresses, request IDs…"
                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                      />
                    </label>
                    <label>
                      <span className="sr-only">Source filter</span>
                      <select
                        aria-label="Source filter"
                        value={source}
                        onChange={(e) => setSource(e.target.value)}
                      >
                        <option value="">All sources</option>
                        {evidence.map((e) => (
                          <option key={e.id} value={e.id}>
                            {e.source} · {e.filename}
                          </option>
                        ))}
                      </select>
                    </label>
                    <select
                      aria-label="Event type filter"
                      value={kind}
                      onChange={(e) => setKind(e.target.value)}
                    >
                      <option value="">All event types</option>
                      <option value="auth">Authentication</option>
                      <option value="web">Web access</option>
                      <option value="system">System</option>
                    </select>
                    <ListFilter size={18} className="muted" />
                  </div>
                  <div className="time-filters">
                    <label>
                      From (UTC)
                      <input
                        type="datetime-local"
                        value={start}
                        onChange={(e) => setStart(e.target.value)}
                      />
                    </label>
                    <label>
                      To (UTC)
                      <input
                        type="datetime-local"
                        value={end}
                        onChange={(e) => setEnd(e.target.value)}
                      />
                    </label>
                    {(q || source || kind || start || end) && (
                      <button
                        className="text-button"
                        onClick={() => {
                          setQ("");
                          setSource("");
                          setKind("");
                          setStart("");
                          setEnd("");
                        }}
                      >
                        Clear filters
                      </button>
                    )}
                  </div>
                  <div className="table-scroll">
                    <table className="timeline">
                      <thead>
                        <tr>
                          <th>CORRECTED TIME / UTC</th>
                          <th>SOURCE</th>
                          <th>OBSERVATION</th>
                          <th>EVIDENCE</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {events.map((event, i) => {
                          const uncertain =
                            (events[i - 1] &&
                              events[i - 1].interval_end >=
                                event.interval_start) ||
                            (events[i + 1] &&
                              events[i + 1].interval_start <=
                                event.interval_end);
                          return (
                            <tr
                              key={event.id}
                              onClick={() => inspect(event.id)}
                            >
                              <td>
                                <div className="time-cell">
                                  <span
                                    className={"timeline-dot " + event.kind}
                                  />
                                  <div>
                                    <strong className="mono">
                                      {time(event.corrected_timestamp).slice(
                                        11,
                                      )}
                                    </strong>
                                    <small>
                                      {event.corrected_timestamp.slice(0, 10)}
                                      {event.offset_seconds !== 0 && (
                                        <em>
                                          {event.offset_seconds > 0 ? "+" : ""}
                                          {event.offset_seconds}s
                                        </em>
                                      )}
                                    </small>
                                    {uncertain && (
                                      <span className="overlap">
                                        Overlapping time
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </td>
                              <td>
                                <span className={"source-badge " + event.kind}>
                                  {event.kind === "web" ? (
                                    <HardDrive size={12} />
                                  ) : (
                                    <Activity size={12} />
                                  )}{" "}
                                  {event.kind}
                                </span>
                                <small className="source-name">
                                  {event.source}
                                </small>
                              </td>
                              <td>
                                <div className="event-message">
                                  {event.message}
                                </div>
                                <small className="mono muted">
                                  {event.ip || event.host || "—"}{" "}
                                  {event.anchor_id &&
                                    ` · ID ${event.anchor_id}`}
                                </small>
                              </td>
                              <td>
                                <span className="file-ref">
                                  <FileText size={13} />
                                  {event.filename}
                                </span>
                                <small className="muted">
                                  Line {event.line_number}
                                </small>
                              </td>
                              <td>
                                <button
                                  className="icon-button"
                                  aria-label={`Inspect ${event.filename} line ${event.line_number}`}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    inspect(event.id);
                                  }}
                                >
                                  <ChevronRight size={17} />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  {!events.length && (
                    <div className="empty">
                      <Activity size={30} />
                      <h3>
                        {loading
                          ? "Loading timeline…"
                          : evidence.length
                            ? "No events match this view"
                            : "Your timeline is ready for evidence"}
                      </h3>
                      <p>
                        {evidence.length
                          ? "Adjust the filters, or inspect parsing gaps for records without a usable timestamp."
                          : "Import Linux auth/syslog or Apache/Nginx access logs to begin."}
                      </p>
                    </div>
                  )}
                  <div className="table-footer">
                    <span>
                      {loading
                        ? "Updating…"
                        : `${total ? page * 100 + 1 : 0}–${Math.min((page + 1) * 100, total)} of ${total} events`}{" "}
                      <span className="footer-divider">/</span> Time order does
                      not establish causation.
                    </span>
                    <div>
                      <button
                        className="icon-button"
                        aria-label="Previous page"
                        disabled={page === 0}
                        onClick={() => setPage((p) => p - 1)}
                      >
                        <ChevronLeft size={18} />
                      </button>
                      <button
                        className="icon-button"
                        aria-label="Next page"
                        disabled={(page + 1) * 100 >= total}
                        onClick={() => setPage((p) => p + 1)}
                      >
                        <ChevronRight size={18} />
                      </button>
                    </div>
                  </div>
                </section>
              )}
              {tab === "evidence" && (
                <section className="card">
                  <div className="section-heading">
                    <div>
                      <h2>Evidence vault</h2>
                      <p>
                        One preserved original for every import. Correction
                        settings apply to the whole file.
                      </p>
                    </div>
                    <ShieldCheck size={22} className="teal" />
                  </div>
                  {evidence.map((e) => (
                    <article className="evidence-item" key={e.id}>
                      <div className="evidence-title">
                        <span className="file-icon">
                          <FileText size={23} />
                        </span>
                        <div>
                          <h3>{e.filename}</h3>
                          <p>
                            {e.source} · {bytes(e.size)} · {e.parsed_records}/
                            {e.total_records} records normalized
                          </p>
                        </div>
                        <span
                          className={e.gap_records ? "tag warning" : "tag good"}
                        >
                          {e.gap_records
                            ? `${e.gap_records} gaps`
                            : "All records parsed"}
                        </span>
                      </div>
                      <div className="hash">
                        <Fingerprint size={15} />
                        <span>SHA-256</span>
                        <code>{e.sha256}</code>
                      </div>
                      <div className="evidence-meta">
                        <span>
                          Zone assumption <strong>{e.timezone}</strong>
                        </span>
                        <span>
                          Year assumption{" "}
                          <strong>{e.year || "Not supplied"}</strong>
                        </span>
                        <span>
                          Clock correction{" "}
                          <strong>
                            {e.offset_seconds > 0 ? "+" : ""}
                            {e.offset_seconds}s ± {e.uncertainty_seconds}s
                          </strong>
                        </span>
                      </div>
                      <p className="muted">Basis: {e.correction_reason}</p>
                      <div className="button-row">
                        <button
                          className="secondary"
                          disabled={busy}
                          onClick={() => setClock(e)}
                        >
                          <SlidersHorizontal size={15} /> Correct clock
                        </button>
                        <a
                          className="secondary"
                          href={"/api" + base + `/evidence/${e.id}/original`}
                        >
                          <ArrowDownToLine size={15} /> Original file
                        </a>
                      </div>
                    </article>
                  ))}
                  {!evidence.length && (
                    <div className="empty">
                      <Layers3 size={32} />
                      <h3>No evidence imported yet</h3>
                      <p>
                        Choose Import evidence to preserve your first source.
                      </p>
                    </div>
                  )}
                </section>
              )}
              {tab === "gaps" && (
                <section className="card">
                  <div className="section-heading">
                    <div>
                      <h2>
                        Gaps & review{" "}
                        <span className="count">
                          {gaps.length + findings.length}
                        </span>
                      </h2>
                      <p>
                        Unparsed records remain in the vault. Gaps are not proof
                        of malicious activity.
                      </p>
                    </div>
                  </div>
                  <div className="info-strip">
                    <ShieldQuestion size={20} /> ALIBI documents observed
                    parsing failures and conflicts. It cannot establish that
                    unseen events occurred or that logs are complete.
                  </div>
                  {findings.map((f, i) => (
                    <article className="gap-item" key={i}>
                      <span className="tag warning">
                        {f.type.replaceAll("_", " ")}
                      </span>
                      <p>{f.message}</p>
                      <div className="button-row">
                        {f.record_ids.map((id, n) => (
                          <button
                            key={id}
                            className="text-button"
                            onClick={() => inspect(id)}
                          >
                            Inspect record {n + 1} <ArrowRight size={13} />
                          </button>
                        ))}
                      </div>
                    </article>
                  ))}
                  {gaps.map((g) => (
                    <article className="gap-item" key={g.id}>
                      <div className="evidence-title">
                        <AlertTriangle size={18} className="amber-text" />
                        <h3>{g.error}</h3>
                        <button
                          className="text-button push-right"
                          onClick={() => inspect(g.id)}
                        >
                          Inspect original <ArrowRight size={14} />
                        </button>
                      </div>
                      <p>
                        {g.filename} · Line {g.line_number} · Bytes [
                        {g.byte_start}, {g.byte_end})
                      </p>
                      <pre>{g.raw_line || "(blank record)"}</pre>
                    </article>
                  ))}
                  {!gaps.length && !findings.length && (
                    <div className="empty">
                      <ShieldCheck size={32} />
                      <h3>No parsing gaps or conflicts found</h3>
                      <p>
                        This is a statement about imported records, not proof of
                        a complete incident record.
                      </p>
                    </div>
                  )}
                </section>
              )}
              {tab === "verify" && (
                <>
                  <section className="card">
                    <div className="section-heading">
                      <div>
                        <h2>Verify original evidence</h2>
                        <p>
                          Recalculate SHA-256 and compare it with the digest
                          captured at intake.
                        </p>
                      </div>
                      <button
                        className="primary"
                        disabled={busy || !evidence.length}
                        onClick={() =>
                          action(async () => {
                            setChecks(
                              await api<Verification[]>(base + "/verify", {
                                method: "POST",
                              }),
                            );
                            setRevision((r) => r + 1);
                          })
                        }
                      >
                        <Fingerprint size={17} />
                        {busy ? "Checking…" : "Verify all files"}
                      </button>
                    </div>
                    {checks.length ? (
                      checks.map((c) => (
                        <div className="verify-result" key={c.evidence_id}>
                          <ShieldCheck size={21} />
                          <div>
                            <strong>{c.filename}</strong>
                            <small>{time(c.checked_at)}</small>
                          </div>
                          <span
                            className={
                              c.status === "verified"
                                ? "tag good"
                                : "tag warning"
                            }
                          >
                            {c.status}
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="info-strip">
                        No verification run in this view yet. Reports also
                        include a fresh integrity check.
                      </div>
                    )}
                  </section>
                  <section className="exports">
                    {[
                      [
                        "report.pdf",
                        "PDF report",
                        "A readable incident summary, chronology, gaps and limitations.",
                      ],
                      [
                        "report.json",
                        "JSON report",
                        "Complete normalized records, provenance, corrections and audit history.",
                      ],
                      [
                        "manifest.json",
                        "Integrity manifest",
                        "SHA-256 digests and file references for independent verification.",
                      ],
                    ].map(([path, title, description]) => (
                      <a
                        className="card export-card"
                        key={path}
                        href={"/api" + base + "/" + path}
                      >
                        <FileText size={26} />
                        <h3>{title}</h3>
                        <p>{description}</p>
                        <span>
                          Download <ArrowDownToLine size={16} />
                        </span>
                      </a>
                    ))}
                  </section>
                  <section className="card">
                    <div className="section-heading">
                      <div>
                        <h2>Investigation audit trail</h2>
                        <p>
                          Intake, verification and correction history stored
                          locally.
                        </p>
                      </div>
                    </div>
                    <div className="audit-list">
                      {audit
                        .slice()
                        .reverse()
                        .map((a) => (
                          <details key={a.id}>
                            <summary>
                              <span>{a.action.replaceAll(".", " / ")}</span>
                              <time>{time(a.occurred_at)}</time>
                            </summary>
                            <pre>
                              {JSON.stringify(JSON.parse(a.details), null, 2)}
                            </pre>
                          </details>
                        ))}
                    </div>
                  </section>
                </>
              )}
              <div className="bottom-note">
                <LockKeyhole size={14} /> Local evidence workbench{" "}
                <span>·</span>{" "}
                {selected?.description || "Evidence first. Assumptions last."}
                <span className="push-right">TEAM EXPOSE / A3-PS013-TC452</span>
              </div>
            </>
          )}
        </main>
      </div>
      {creating && (
        <Modal
          title="Create investigation"
          onClose={() => {
            if (!busy) setCreating(false);
          }}
        >
          <form onSubmit={createCase}>
            <label>
              Investigation name
              <input
                autoFocus
                name="name"
                required
                maxLength={160}
                placeholder="e.g. Unusual access · October 28"
              />
            </label>
            <label>
              Description
              <textarea
                name="description"
                maxLength={4000}
                rows={3}
                placeholder="Scope, incident context, and questions to investigate"
              />
            </label>
            <div className="info-strip">
              Use synthetic data for the demo. Real logs can contain sensitive
              personal and security information.
            </div>
            <button className="primary full" disabled={busy}>
              {busy ? "Creating…" : "Create investigation"}
              <ArrowRight size={17} />
            </button>
          </form>
        </Modal>
      )}
      {importing && (
        <Modal
          title="Import & preserve evidence"
          onClose={() => {
            if (!busy) setImporting(false);
          }}
        >
          <form onSubmit={importFiles}>
            <label
              className="dropzone"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                if (!busy) setFiles(Array.from(e.dataTransfer.files));
              }}
            >
              <UploadCloud size={32} />
              <strong>
                {files.length
                  ? `${files.length} file(s) selected`
                  : "Drop log files here, or browse"}
              </strong>
              <span>
                Linux syslog / auth · Apache / Nginx access · 10 MiB per file
              </span>
              <input
                aria-label="Evidence files"
                type="file"
                multiple
                disabled={busy}
                onChange={(e) => setFiles(Array.from(e.target.files || []))}
              />
            </label>
            {files.length > 0 && (
              <div className="file-list">
                {files.map((f, i) => (
                  <span key={i}>
                    {f.name} · {bytes(f.size)}
                  </span>
                ))}
              </div>
            )}
            <div className="form-grid">
              <label>
                Source label
                <input
                  name="source"
                  required
                  maxLength={160}
                  placeholder="e.g. Production web server"
                />
              </label>
              <label>
                Log format
                <select name="format">
                  <option value="auto">Detect per record</option>
                  <option value="syslog">Linux auth / syslog</option>
                  <option value="access">Apache / Nginx access</option>
                </select>
              </label>
              <label>
                Timezone for timestamps without a zone
                <input
                  name="timezone"
                  required
                  defaultValue="UTC"
                  placeholder="Asia/Kolkata or +05:30"
                />
              </label>
              <label>
                Year for yearless syslog
                <input
                  name="year"
                  type="number"
                  min="1970"
                  max="2100"
                  placeholder="Explicit year, e.g. 2026"
                />
              </label>
              <label>
                Clock correction (seconds)
                <input
                  name="offset"
                  type="number"
                  min="-604800"
                  max="604800"
                  step="any"
                  defaultValue="0"
                  required
                />
              </label>
              <label>
                Uncertainty ± seconds
                <input
                  name="uncertainty"
                  type="number"
                  min="0"
                  max="86400"
                  step="any"
                  defaultValue="0"
                  required
                />
              </label>
            </div>
            <label>
              Basis for correction
              <input
                name="reason"
                required
                maxLength={2000}
                defaultValue="No clock correction applied"
              />
            </label>
            <div className="info-strip">
              Corrected time = UTC time + correction. A slow clock needs a
              positive correction. Settings apply to every selected file. Import
              different sources separately.
            </div>
            <button className="primary full" disabled={busy || !files.length}>
              <LockKeyhole size={17} />
              {busy ? "Preserving & parsing…" : "Preserve & import"}
            </button>
          </form>
        </Modal>
      )}
      {clock && (
        <Modal
          title={`Correct clock · ${clock.filename}`}
          onClose={() => {
            if (!busy) setClock(null);
          }}
        >
          <form onSubmit={changeClock}>
            <p className="subtitle">
              This replaces the file’s current correction. It never changes the
              original bytes or normalized UTC timestamp.
            </p>
            <div className="form-grid">
              <label>
                Correction (seconds)
                <input
                  name="offset"
                  type="number"
                  min="-604800"
                  max="604800"
                  step="any"
                  defaultValue={clock.offset_seconds}
                  required
                />
              </label>
              <label>
                Uncertainty ± seconds
                <input
                  name="uncertainty"
                  type="number"
                  min="0"
                  max="86400"
                  step="any"
                  defaultValue={clock.uncertainty_seconds}
                  required
                />
              </label>
            </div>
            <label>
              Supporting evidence / reason
              <textarea
                aria-label="Supporting evidence / reason"
                name="reason"
                required
                minLength={3}
                maxLength={2000}
                rows={3}
                defaultValue={clock.correction_reason}
              />
            </label>
            <div className="info-strip">
              Positive adds time; negative subtracts time. Zero uncertainty
              means no bound has been supplied, not perfect accuracy.
            </div>
            <button className="primary full" disabled={busy}>
              Apply correction & record assumption
            </button>
          </form>
          <Calibration
            caseId={caseId}
            target={clock}
            evidence={evidence}
            onApplied={() => {
              setClock(null);
              setRevision((v) => v + 1);
              setNotice(
                "Reviewed anchor correction applied and recorded in the audit trail.",
              );
            }}
          />
        </Modal>
      )}
      {detail && (
        <Modal
          title={
            detail.error
              ? "Source record / parsing gap"
              : "Event / evidence detail"
          }
          onClose={() => setDetail(null)}
        >
          <div className="detail">
            <span
              className={
                detail.integrity?.status === "verified"
                  ? "tag good"
                  : "tag warning"
              }
            >
              {detail.integrity?.status === "verified"
                ? "Original SHA-256 verified"
                : `Integrity: ${detail.integrity?.status}`}
            </span>
            <h3>{detail.error || detail.message}</h3>
            <dl>
              <dt>Source</dt>
              <dd>
                {detail.source} · {detail.filename}
              </dd>
              <dt>Original timestamp</dt>
              <dd>{detail.original_timestamp || "Unparsed"}</dd>
              <dt>Normalized UTC</dt>
              <dd>{time(detail.utc_timestamp)}</dd>
              <dt>Corrected UTC</dt>
              <dd>{time(detail.corrected_timestamp)}</dd>
              <dt>Uncertainty interval</dt>
              <dd>
                {time(detail.interval_start)}
                <br />
                {time(detail.interval_end)}
              </dd>
              <dt>Timezone / year basis</dt>
              <dd>{detail.timezone_basis || "Unparsed"}</dd>
              <dt>Clock correction</dt>
              <dd>
                {detail.offset_seconds}s ± {detail.uncertainty_seconds}s
              </dd>
              <dt>Provenance</dt>
              <dd>
                Line {detail.line_number} · Bytes [{detail.byte_start},{" "}
                {detail.byte_end})
              </dd>
              <dt>Evidence ID</dt>
              <dd className="mono">{detail.evidence_id}</dd>
              <dt>Event ID</dt>
              <dd className="mono">{detail.id}</dd>
              <dt>Parser</dt>
              <dd>{detail.parser_version || "Unsupported record"}</dd>
            </dl>
            <h4>Evidence-supported associations</h4>
            {associations
              .filter((a) => a.record_ids.includes(detail.id))
              .map((a) => (
                <div className="info-strip" key={a.identifier}>
                  <div>
                    <strong>ID {a.identifier}</strong>
                    <p>{a.message}</p>
                    {a.record_ids
                      .filter((id) => id !== detail.id)
                      .map((id, i) => (
                        <button
                          className="text-button"
                          key={id}
                          onClick={() => inspect(id)}
                        >
                          Inspect associated record {i + 1}{" "}
                          <ArrowRight size={12} />
                        </button>
                      ))}
                  </div>
                </div>
              ))}
            <h4>Preserved record preview</h4>
            <pre>{detail.raw_line || "(blank record)"}</pre>
            <p className="muted">
              Preview replaces invalid UTF-8 characters. The downloaded original
              retains the exact bytes and line endings.
            </p>
            <a
              className="secondary"
              href={"/api" + base + `/evidence/${detail.evidence_id}/original`}
            >
              <ArrowDownToLine size={16} /> Download verified original
            </a>
          </div>
        </Modal>
      )}
    </div>
  );
}
