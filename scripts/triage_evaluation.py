"""Record real human trials and compare paired results. Never synthesizes times."""
import argparse
import csv
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['participant', 'scenario', 'mode', 'seconds', 'correct_timestamps', 'expected_timestamps', 'correct_gap_count', 'recorded_at']


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    trial = sub.add_parser('trial')
    trial.add_argument('--participant', required=True)
    trial.add_argument('--scenario', choices=['A_conflicting_clocks','B_cross_source','C_gaps_conflicts'], required=True)
    trial.add_argument('--mode', choices=['manual','assisted'], required=True)
    trial.add_argument('--answers', type=Path, required=True, help='Path where the participant will save their completed JSON answers')
    parser.add_argument('--results', type=Path, default=ROOT/'output/human-trials.csv')
    sub.add_parser('compare')
    args = parser.parse_args()
    if args.command == 'trial':
        print('Follow docs/EVALUATION.md. Timing includes creating the required answer file.')
        input('Press Enter when the participant is ready to start: ')
        started = perf_counter()
        input('Complete triage and save the answer JSON, then press Enter to stop: ')
        elapsed = perf_counter()-started
        answers = json.loads(args.answers.read_text(encoding='utf-8'))
        truth = json.loads((ROOT/'datasets/ground_truth.json').read_text())[args.scenario]
        correct = sum(answers.get('times',{}).get(key)==value for key,value in truth['expected_times'].items())
        row = dict(participant=args.participant, scenario=args.scenario, mode=args.mode, seconds=round(elapsed,3), correct_timestamps=correct, expected_timestamps=len(truth['expected_times']), correct_gap_count=int(answers.get('gap_count')==truth['gaps']), recorded_at=datetime.now(timezone.utc).isoformat())
        args.results.parent.mkdir(parents=True, exist_ok=True)
        exists = args.results.exists() and args.results.stat().st_size > 0
        with args.results.open('a', newline='', encoding='utf-8') as output:
            writer = csv.DictWriter(output, fieldnames=FIELDS)
            if not exists: writer.writeheader()
            writer.writerow(row)
        print(json.dumps(row, indent=2))
    else:
        if not args.results.exists():
            print('PENDING: no human trials recorded. No manual baseline or triage speedup is claimed.')
            return
        with args.results.open(newline='',encoding='utf-8') as source:
            rows = list(csv.DictReader(source))
        groups = {}
        for row in rows:
            key = (row['participant'],row['scenario'])
            modes = groups.setdefault(key,{})
            if row['mode'] in modes:
                raise SystemExit('Duplicate participant/scenario/mode trial: use unique participant-session IDs; no silent selection.')
            modes[row['mode']] = row
        pairs = []
        for (person,scenario),modes in groups.items():
            if {'manual','assisted'} <= modes.keys():
                manual,assisted=modes['manual'],modes['assisted']
                pairs.append(dict(participant=person,scenario=scenario,manual_seconds=float(manual['seconds']),assisted_seconds=float(assisted['seconds']),saved_seconds=float(manual['seconds'])-float(assisted['seconds']),manual_correct=int(manual['correct_timestamps']),assisted_correct=int(assisted['correct_timestamps']),manual_gaps_correct=bool(int(manual['correct_gap_count'])),assisted_gaps_correct=bool(int(assisted['correct_gap_count']))))
        print(json.dumps({'paired_trials':len(pairs),'unpaired_trials':len(rows)-2*len(pairs),'median_saved_seconds':statistics.median(p['saved_seconds'] for p in pairs) if pairs else None,'pairs':pairs,'caveat':'Small, repeated synthetic tasks have learning effects; report accuracy and individual trials alongside timing.'},indent=2))


if __name__ == '__main__':
    main()
