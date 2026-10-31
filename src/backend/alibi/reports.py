"""Local exports; log content is escaped as data before PDF layout."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

LIMITATIONS = [
    'SHA-256 detects changes relative to the intake digest; it does not prove authenticity before collection or provide forensic certification.',
    'Clock corrections are investigator assumptions. A zero uncertainty setting is not a claim of perfect clock accuracy.',
    'Temporal proximity, shared IPs, and matching identifiers do not by themselves prove causation or malicious activity.',
    'Parsing gaps describe records that could not be normalized. Silence is not proof of missing events. No automatic loss-of-logging claim is made.',
    'Yearless syslog uses the explicitly supplied year for every line. Split files spanning New Year before import; DST ambiguity requires a fixed offset.',
    'This local prototype is not an authenticated multi-user service or a tamper-proof chain-of-custody system. No endpoint takeover or malware removal is performed.',
]


def make_pdf(report: dict) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(595.28, 841.89), rightMargin=42, leftMargin=42, topMargin=45, bottomMargin=45, title='ALIBI Incident Report', author='Team EXPOSE')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SmallText', fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor('#38495b'), wordWrap='CJK', alignment=TA_LEFT))
    styles['Title'].textColor = colors.HexColor('#122b38')
    def p(text, style='SmallText'):
        # Built-in PDF font is Latin-1: explicit replacement is documented;
        # JSON and original downloads retain all Unicode and original bytes.
        safe = str(text).encode('latin-1', errors='replace').decode('latin-1')
        return Paragraph(escape(safe).replace('\n', '<br/>'), styles[style])
    story = [p('ALIBI / INCIDENT REPORT', 'Title'), p(report['investigation']['name'], 'Heading1'), p(report['investigation']['description']), Spacer(1, 10), p(f"Generated {report['generated_at']} | Team EXPOSE | A3-PS013-TC452"), p(f"{len(report['evidence'])} evidence files | {len(report['timeline'])} normalized events | {len(report['gaps'])} parsing gaps"), p('Investigation and integrity', 'Heading2')]
    for item in report['evidence']:
        verification = next(v for v in report['integrity'] if v['evidence_id'] == item['id'])
        story.extend([p(f"{item['filename']} / {item['source']}", 'Heading3'), p(f"Evidence {item['id']} | {item['size']} bytes | Integrity: {verification['status']}"), p(f"Intake SHA-256: {item['sha256']}"), p(f"Observed SHA-256: {verification['actual_sha256'] or 'unavailable'}"), p(f"Timezone: {item['timezone']}; year: {item['year']}; correction: {item['offset_seconds']:+g}s; uncertainty: +/-{item['uncertainty_seconds']:g}s. Basis: {item['correction_reason']}")])
    story.append(p('Chronology / corrected UTC', 'Heading2'))
    for event in report['timeline']:
        story.extend([p(f"{event['corrected_timestamp']} | {event['kind'].upper()} | {event['source']}", 'Heading3'), p(event['message']), p(f"Original: {event['original_timestamp']} | UTC: {event['utc_timestamp']}"), p(f"Interval: [{event['interval_start']}, {event['interval_end']}] | {event['timezone_basis']}"), p(f"Event {event['id']} | Evidence {event['evidence_id']} line {event['line_number']}, bytes [{event['byte_start']}, {event['byte_end']})")])
    story.append(p('Parsing gaps and review findings', 'Heading2'))
    for gap in report['gaps']:
        story.extend([p(f"{gap['filename']} line {gap['line_number']}: {gap['error']}", 'Heading3'), p(f"Evidence {gap['evidence_id']}; bytes [{gap['byte_start']}, {gap['byte_end']})"), p(gap['raw_line'][:1000])])
    for finding in report['findings']:
        story.append(p(f"{finding['type']}: {finding['message']} References: {', '.join(finding['record_ids'])}"))
    if not report['gaps'] and not report['findings']:
        story.append(p('No parsing gaps or deterministic review findings in the imported evidence. This does not establish completeness.'))
    if report.get('relationships'):
        story.append(p('Evidence-supported associations', 'Heading2'))
        for relationship in report['relationships']:
            story.append(p(f"Identifier {relationship['identifier']}: {relationship['message']} Event references: {', '.join(relationship['record_ids'])}"))
    story.append(p('Assumptions, limitations and audit history', 'Heading2'))
    for limitation in report['limitations']:
        story.extend([p(limitation), Spacer(1, 6)])
    story.append(p('PDF uses a Latin-1 font; unsupported characters appear as ?. Use JSON and original evidence for lossless text. Long raw gap previews are limited to 1,000 characters.'))
    for action in report['audit']:
        story.append(p(f"{action['occurred_at']} / {action['action']} / {action['details']}"))
    def footer(canvas, document):
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#536879'))
        canvas.drawString(42, 25, 'ALIBI  /  Local evidence reconstruction  /  Team EXPOSE')
        canvas.drawRightString(553, 25, f'Page {document.page}')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
