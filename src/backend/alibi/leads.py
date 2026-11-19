"""Investigative leads derived from the current corrected timeline."""
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from ipaddress import ip_address

SSH = re.compile(r"^(Failed|Accepted) (?:password|publickey|keyboard-interactive(?:/pam)?) for (?:invalid user )?\S+ from (\S+) port \d+\b")
ARCHIVE = re.compile(r"(?:^|/)backup(?:[-_]\d{4}(?:[-_]\d{2}){0,2})?\.(?:tar(?:\.gz)?|tgz|zip|sql(?:\.gz)?)$", re.I)
CONFIG = {"/.env", "/.git/config", "/wp-config.php", "/web.config"}
RATIONALE = {
    "Backup archive requested": "An archive can contain several files. Check who was expected to request it.",
    "Configuration file requested": "Configuration files can expose deployment settings. Review the response and expected access.",
    "Administrative endpoint requested": "Check the response status and whether access to this administrative route was expected.",
    "Privileged command recorded": "Check the sudo command against the operator’s expected duties and maintenance schedule.",
}


def address(value):
    try:
        return str(ip_address(value))
    except ValueError:
        return None


def lead(kind, title, priority, message, limit, events, ip):
    return dict(type=kind, title=title, priority=priority, message=message, limitation=limit,
                start=events[0]["corrected_timestamp"], end=events[-1]["corrected_timestamp"],
                ip=ip, record_ids=[e["id"] for e in events],
                references=[{k: e[k] for k in ("id", "evidence_id", "source", "filename", "line_number")} for e in events])


def sensitive(event):
    if event["kind"] == "web":
        path = event["message"].split()[1].partition("?")[0]
        if ARCHIVE.search(path):
            return "Backup archive requested"
        if path.lower() in CONFIG:
            return "Configuration file requested"
        if path.rstrip("/") == "/admin":
            return "Administrative endpoint requested"
    if re.fullmatch(r"sudo(?:\[\d+\])?", event["service"]) and re.search(r"(?:^|[;:] )COMMAND=/\S+", event["message"]):
        return "Privileged command recorded"
    return None


def cross_source(ip, observations):
    """Advance a ten-minute window. Emit one group, then consume its records."""
    counts = {"auth": Counter(), "web": Counter()}
    window = timedelta(minutes=10)
    left = right = 0
    while left < len(observations):
        while right < len(observations) and observations[right][0] - observations[left][0] <= window:
            event = observations[right][1]
            counts[event["kind"]][event["source"]] += 1
            right += 1
        first = observations[left][1]
        other = "auth" if first["kind"] == "web" else "web"
        opposite = counts[other]
        if len(opposite) > int(first["source"] in opposite):
            members = []
            for _, event in observations[left:right]:
                peers = counts["auth" if event["kind"] == "web" else "web"]
                if len(peers) > int(event["source"] in peers):
                    members.append(event)
            yield lead("cross_source_activity", "Related activity across multiple sources", "Informational",
                       "Web and authentication records share an IP across distinct sources within ten minutes.",
                       "Shared addresses can represent several users or devices. Actor identity and causation remain unknown.", members, ip)
            left = right
            for count in counts.values():
                count.clear()
        else:
            count = counts[first["kind"]]
            count[first["source"]] -= 1
            if not count[first["source"]]:
                del count[first["source"]]
            left += 1


def investigative_leads(records):
    ordered = sorted(records, key=lambda e: (e["corrected_timestamp"], e["evidence_id"], e["line_number"]))
    failures, by_ip, result = {}, defaultdict(list), []
    for event in ordered:
        stamp = datetime.fromisoformat(event["corrected_timestamp"])
        ip = address(event["ip"] or "")
        if ip and event["kind"] in ("web", "auth"):
            by_ip[ip].append((stamp, event))
        outcome = SSH.match(event["message"]) if re.fullmatch(r"sshd(?:\[\d+\])?", event["service"]) else None
        if ip and outcome and address(outcome[2]) == ip:
            if outcome[1] == "Failed":
                failures[ip] = (stamp, event)
            elif ip in failures:
                earlier, failure = failures[ip]
                if earlier < stamp:
                    del failures[ip]
                    if stamp - earlier <= timedelta(minutes=5):
                        elapsed = (stamp - earlier).total_seconds()
                        result.append(lead("authentication_sequence", "Authentication sequence requiring review", "High",
                                           f"SSH accepted authentication {elapsed:g} seconds after a failed attempt from the same IP.",
                                           "Different users may share this IP. Check account and clock assumptions before drawing conclusions.", [failure, event], ip))
        title = sensitive(event)
        if title:
            result.append(lead("sensitive_activity", title, "Medium", f"{event['message']}. {RATIONALE[title]}",
                               "Review against expected administrative activity. This record alone cannot establish unauthorized access or data transfer.", [event], ip))
    for ip, observations in by_ip.items():
        result.extend(cross_source(ip, observations))
    rank = {"High": 0, "Medium": 1, "Informational": 2}
    return sorted(result, key=lambda item: (rank[item["priority"]], item["start"], item["record_ids"]))
