"""Local exports; log content is escaped as data before PDF layout."""
from io import BytesIO
from collections import Counter
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
    doc = SimpleDocTemplate(output, pagesize=(595.28, 841.89), rightMargin=42, leftMargin=42, topMargin=45, bottomMargin=48, title='ALIBI Incident Report', author='Team EXPOSE')
    styles = getSampleStyleSheet()
    navy, blue = colors.HexColor('#123B68'), colors.HexColor('#205A91')
    styles.add(ParagraphStyle(name='SmallText', fontName='Helvetica', fontSize=9, leading=13, spaceAfter=5, textColor=colors.HexColor('#263648'), wordWrap='CJK', alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='Reference', parent=styles['SmallText'], fontSize=7.5, leading=10, textColor=colors.HexColor('#526579')))
    styles.add(ParagraphStyle(name='Verified', parent=styles['SmallText'], textColor=colors.HexColor('#237A57')))
    styles.add(ParagraphStyle(name='Critical', parent=styles['SmallText'], textColor=colors.HexColor('#C62828')))
    styles.add(ParagraphStyle(name='Review', parent=styles['SmallText'], textColor=colors.HexColor('#B76E00')))
    for name in ('Title', 'Heading1', 'Heading2', 'Heading3'):
        styles[name].textColor = navy
        styles[name].fontName = 'Helvetica-Bold'
        styles[name].keepWithNext = True
    styles['Title'].alignment = TA_LEFT
    styles['Title'].fontSize = 22
    styles['Heading1'].fontSize = 16
    styles['Heading2'].fontSize = 13
    styles['Heading2'].spaceBefore = 16
    styles['Heading3'].fontSize = 10
    styles['Heading3'].spaceBefore = 10
    def p(text, style='SmallText'):
        # Escape all untrusted content. JSON and originals retain full Unicode.
        safe = str(text).encode('latin-1', errors='replace').decode('latin-1')
        return Paragraph(escape(safe).replace('\n', '<br/>'), styles[style])
    evidence_refs = {item['id']: f'E{i+1}' for i, item in enumerate(report['evidence'])}
    integrity = {item['evidence_id']: item for item in report['integrity']}
    case = report['investigation']
    events = report['timeline']
    story = [p('ALIBI / INCIDENT REPORT', 'Title'), p('Team EXPOSE | A3-PS013-TC452 | AIORI Hackathon 3', 'Reference'),
             p('1. Investigation identification', 'Heading2'), p(case['name'], 'Heading1'),
             p(case.get('description') or 'No investigation description supplied.'),
             p(f"Investigation ID: {case['id']}", 'Reference'),
             p(f"Created: {case['created_at']} | Report generated: {report['generated_at']}", 'Reference'),
             p('2. Investigation overview', 'Heading2'),
             p(f"{len(report['evidence'])} evidence files; {len(events)} normalized events; {len(report['gaps'])} parsing gaps; {len(report['findings'])} review findings.")]
    if events:
        story.append(p(f"Corrected UTC coverage: {events[0]['corrected_timestamp']} to {events[-1]['corrected_timestamp']}."))
    else:
        story.append(p('No normalized events are available in this investigation.', 'Review'))
    failed = sum(item['status'] != 'verified' for item in report['integrity'])
    story.append(p(f"Integrity checks: {len(report['integrity']) - failed} verified; {failed} failed or unavailable.", 'Critical' if failed else 'Verified'))
    story.append(p('This report describes imported observations. Timestamp order and shared identifiers do not establish causation, actor identity, or malicious activity.'))
    story.append(p('3. Evidence integrity summary', 'Heading2'))
    if report['evidence']:
        rows = [[p('Reference / file'), p('Records / gaps'), p('Integrity')]]
        for item in report['evidence']:
            check = integrity[item['id']]
            rows.append([p(f"{evidence_refs[item['id']]} / {item['filename']}"),
                         p(f"{item['parsed_records']} parsed / {item['gap_records']} gaps"),
                         p(check['status'].upper(), 'Verified' if check['status'] == 'verified' else 'Critical')])
        table = Table(rows, colWidths=[285, 126, 100], repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EAF2F9')),
                                   ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING',(0,0),(-1,-1),8),
                                   ('TOPPADDING',(0,0),(-1,-1),7), ('BOTTOMPADDING',(0,0),(-1,-1),7),
                                   ('LINEBELOW',(0,0),(-1,0),0.7,blue),
                                   ('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#D6E0EA'))]))
        story.append(table)
    for item in report['evidence']:
        check = integrity[item['id']]
        story.extend([p(f"{evidence_refs[item['id']]} / {item['filename']} / {item['source']}", 'Heading3'),
                      p(f"Evidence ID: {item['id']} | {item['size']} bytes", 'Reference'),
                      p(f"Intake SHA-256: {item['sha256']}", 'Reference'),
                      p(f"Observed SHA-256: {check['actual_sha256'] or 'unavailable'}", 'Reference'),
                      p(f"Checked: {check['checked_at']}", 'Reference')])
    story.append(p('4. Chronology / corrected UTC', 'Heading2'))
    story.append(p('A positive correction adds time to the source clock. Equal or overlapping time intervals leave ordering uncertain.', 'Review'))
    for index, event in enumerate(events, 1):
        ref = evidence_refs[event['evidence_id']]
        story.extend([p(f"{index}. {event['corrected_timestamp']} | {event['kind'].upper()} | {event['source']}", 'Heading3'),
                      p(event['message']),
                      p(f"Original: {event['original_timestamp']} | Normalized UTC: {event['utc_timestamp']}", 'Reference'),
                      p(f"Corrected interval: [{event['interval_start']}, {event['interval_end']}] | {event['timezone_basis']}", 'Reference'),
                      p(f"{ref}, line {event['line_number']}, bytes [{event['byte_start']}, {event['byte_end']}) | Event ID: {event['id']}", 'Reference')])
    story.append(p('5. Clock corrections and assumptions', 'Heading2'))
    for item in report['evidence']:
        story.extend([p(f"{evidence_refs[item['id']]} / {item['source']}", 'Heading3'),
                      p(f"Timezone assumption: {item['timezone']}; year assumption: {item['year'] if item['year'] is not None else 'not supplied'}. Explicit timestamp offsets take precedence."),
                      p(f"Absolute clock correction: {item['offset_seconds']:+g} seconds; supplied uncertainty: +/-{item['uncertainty_seconds']:g} seconds.", 'Review' if item['offset_seconds'] or item['uncertainty_seconds'] else 'SmallText'),
                      p(f"Recorded basis: {item['correction_reason']}")])
    story.append(p('6. Parsing gaps and review findings', 'Heading2'))
    for gap in report['gaps']:
        story.extend([p(f"{gap['filename']} line {gap['line_number']}: {gap['error']}", 'Heading3'),
                      p(f"{evidence_refs[gap['evidence_id']]}; bytes [{gap['byte_start']}, {gap['byte_end']}) | Record ID: {gap['id']}", 'Reference'),
                      p(gap['raw_line'][:1000] or '(blank record)', 'Reference')])
    for finding in report['findings']:
        story.append(p(f"{finding['type'].replace('_', ' ')}: {finding['message']}", 'Review'))
        story.append(p(f"Record references: {', '.join(finding['record_ids'])}", 'Reference'))
    if not report['gaps'] and not report['findings']:
        story.append(p('No parsing gaps or deterministic review findings in the imported evidence. This does not establish completeness.'))
    if report.get('relationships'):
        story.append(p('Shared identifiers / associations only', 'Heading3'))
        for relationship in report['relationships']:
            story.append(p(f"Identifier {relationship['identifier']}: {relationship['message']} Event references: {', '.join(relationship['record_ids'])}"))
    story.append(p('7. Evidence references and limitations', 'Heading2'))
    story.append(p('E1, E2 and subsequent references identify the files and full SHA-256 hashes in section 3. Line numbers are 1-based. Byte ranges include the start and exclude the end, and refer to the preserved original file.'))
    for limitation in report['limitations']:
        story.extend([p(limitation), Spacer(1, 6)])
    story.append(p('PDF uses a Latin-1 font; unsupported characters appear as ?. Use JSON and original evidence for lossless text. Long raw gap previews are limited to 1,000 characters.'))
    counts = Counter(action['action'] for action in report['audit'])
    story.append(p('Audit summary / full history in JSON', 'Heading3'))
    story.append(p(f"{len(report['audit'])} audit entries retained. Download the corresponding JSON report for every audit timestamp and complete details, plus the integrity manifest for independent hash verification."))
    for action, count in sorted(counts.items()):
        story.append(p(f"{action.replace('.', ' / ')}: {count}", 'Reference'))
    story.append(Spacer(1, 10))
    story.append(p('Developed by Anurag Deb and Sangram Keshari Patra\nMentored by Prof. Partha Chakraborty', 'Reference'))
    def footer(canvas, document):
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(navy)
        canvas.drawString(42, 25, 'ALIBI  /  Local evidence reconstruction  /  Team EXPOSE')
        canvas.drawRightString(553, 25, f'Page {document.page}')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
