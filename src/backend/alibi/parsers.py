"""Deterministic parsers. Failed records are evidence, never silently dropped."""
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

PARSER_VERSION = "alibi-1"
ACCESS = re.compile(r'^(?P<ip>\S+) \S+ \S+ \[(?P<ts>[^\]]+)\] "(?P<request>[^"]*)" (?P<status>\d{3}) (?P<size>\d+|-)(?P<extra>.*)$')
SYSLOG = re.compile(r'^(?:<\d+>)?(?P<ts>[A-Z][a-z]{2}\s+\d{1,2} \d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\S+) (?P<host>\S+) (?P<service>[^: ]+):? (?P<message>.*)$')
MONTHS = {m: i + 1 for i, m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}


def utc_text(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def zone(name: str):
    if re.fullmatch(r'[+-]\d{2}:\d{2}', name):
        hours, minutes = map(int, name[1:].split(':'))
        if hours > 23 or minutes > 59:
            raise ValueError('Invalid fixed timezone offset')
        return timezone(timedelta(minutes=(hours * 60 + minutes) * (-1 if name[0] == '-' else 1)))
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError('Unknown timezone; use an IANA name or +HH:MM') from exc


def localize(dt: datetime, timezone_name: str) -> datetime:
    tz = zone(timezone_name)
    a, b = dt.replace(tzinfo=tz, fold=0), dt.replace(tzinfo=tz, fold=1)
    valid_a = a.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) == dt
    valid_b = b.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) == dt
    if not valid_a and not valid_b:
        raise ValueError('Nonexistent local time during DST transition; provide a fixed offset')
    if valid_a and valid_b and a.utcoffset() != b.utcoffset():
        raise ValueError('Ambiguous local time during DST transition; provide a fixed offset')
    return a if valid_a else b


def parse_line(raw: str, log_format: str, timezone_name: str, year: int | None) -> dict:
    if not raw.strip():
        raise ValueError('Blank record')
    if '\x00' in raw:
        raise ValueError('NUL byte: unsupported binary record')
    match = ACCESS.fullmatch(raw) if log_format in ('auto', 'access') else None
    if match:
        fields = match.groupdict()
        # Parse English month names independently of the machine locale.
        stamp = re.fullmatch(r'(\d{2})/([A-Za-z]{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2}) ([+-]\d{4})', fields['ts'])
        if not stamp:
            raise ValueError('Invalid access timestamp or missing explicit timezone')
        day, month, yr, hour, minute, second, offset = stamp.groups()
        dt = datetime(int(yr), MONTHS[month], int(day), int(hour), int(minute), int(second), tzinfo=zone(offset[:3] + ':' + offset[3:]))
        if not re.fullmatch(r'\S+ \S+ HTTP/\d(?:\.\d)?', fields['request']):
            raise ValueError('Unsupported or missing HTTP request fields')
        fields.update(kind='web', message=f"{fields['request']} · HTTP {fields['status']}", host='', service='http', timezone_basis='explicit timestamp offset')
    else:
        match = SYSLOG.fullmatch(raw) if log_format in ('auto', 'syslog') else None
        if not match:
            raise ValueError('Unsupported record or missing required fields')
        fields = match.groupdict()
        ts = fields['ts']
        if not fields['message'].strip():
            raise ValueError('Missing syslog message')
        if ts[0].isdigit():
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            fields['timezone_basis'] = 'explicit timestamp offset' if dt.tzinfo else f'assumed {timezone_name}'
            if dt.tzinfo is None:
                dt = localize(dt, timezone_name)
        else:
            if year is None:
                raise ValueError('Syslog timestamp has no year; investigator must supply an explicit year')
            month, day, clock = ts.split()
            hour, minute, second = map(int, clock.split(':'))
            dt = localize(datetime(year, MONTHS[month], int(day), hour, minute, second), timezone_name)
            fields['timezone_basis'] = f'assumed {timezone_name}; assumed year {year}; no automatic rollover'
        fields['kind'] = 'auth' if fields['service'].startswith(('sshd', 'sudo', 'su[', 'login')) else 'system'
        ip = re.search(r'\bfrom ([\da-fA-F:.]+)', fields['message'])
        fields['ip'] = ip.group(1) if ip else ''
        fields['status'] = ''
    identity = re.search(r'\b(?:request_id|event_id)=([\w.:-]+)', raw)
    return {k: fields.get(k, '') for k in ('kind', 'message', 'host', 'service', 'ip', 'status', 'timezone_basis')} | {
        'original_timestamp': fields['ts'], 'utc_timestamp': utc_text(dt),
        'anchor_id': identity.group(1) if identity else '', 'parser_version': PARSER_VERSION,
    }


def parse_bytes(data: bytes, log_format: str, timezone_name: str, year: int | None):
    position = 0
    for line_number, chunk in enumerate(data.splitlines(keepends=True), 1):
        # Offsets are half-open and include original line terminators.
        record = {'line_number': line_number, 'byte_start': position, 'byte_end': position + len(chunk), 'raw_line': chunk.decode('utf-8', errors='replace').rstrip('\r\n')}
        position += len(chunk)
        try:
            raw = chunk.decode('utf-8').rstrip('\r\n')
            if len(chunk) > 65536:
                raise ValueError('Record exceeds 64 KiB parser limit')
            record.update(parse_line(raw, log_format, timezone_name, year))
            record['error'] = None
        except (ValueError, KeyError, OverflowError) as exc:
            record['error'] = str(exc) if not isinstance(exc, UnicodeDecodeError) else 'Invalid UTF-8; original bytes preserved'
        yield record
