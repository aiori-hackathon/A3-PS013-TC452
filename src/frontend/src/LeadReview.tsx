import { useState } from "react";
import { ChevronRight, FileText } from "lucide-react";
import type { Lead } from "./types";

const displayTime = (stamp: string) => stamp.replace("T", " ").replace(".000000Z", "Z");

export default function LeadReview({ leads, inspect }: { leads: Lead[]; inspect: (id: string) => void }) {
  const [priority, setPriority] = useState("All");
  const visible = leads.filter(lead => priority === "All" || lead.priority === priority);
  return <section className="card lead-review">
    <div className="section-heading">
      <div><h2>Investigative leads <span className="count">{leads.length}</span></h2>
        <p>Priority suggests a review order. Expand a lead to inspect its evidence.</p></div>
      <label>Review priority <select value={priority} onChange={e => setPriority(e.target.value)}>
        {["All", "High", "Medium", "Informational"].map(value => <option key={value}>{value}</option>)}
      </select></label>
    </div>
    {!visible.length && <p className="lead-empty">No leads match this selection.</p>}
    {visible.map(lead => <details className="lead-row" key={lead.type + lead.record_ids[0]}>
      <summary>
        <ChevronRight size={17} className="lead-chevron" />
        <span><strong>{lead.title}</strong><small>{displayTime(lead.start)}{lead.end !== lead.start && " – " + displayTime(lead.end)} · {lead.references.length} supporting {lead.references.length === 1 ? "event" : "events"}{lead.ip && " · " + lead.ip}</small></span>
        <span className={"lead-priority " + lead.priority.toLowerCase()}>{lead.priority}</span>
      </summary>
      <div className="lead-body"><p>{lead.message}</p><p className="lead-limit">{lead.limitation}</p>
        <div className="lead-sources">{lead.references.map(ref => <button key={ref.id} className="secondary" onClick={() => inspect(ref.id)}>
          <FileText size={14} />{ref.source} · {ref.filename} line {ref.line_number}
        </button>)}</div>
      </div>
    </details>)}
  </section>;
}
