"""Audit the completed GF40 build and retain evidence even when signoff fails."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'verification' / 'build'
OUT.mkdir(parents=True, exist_ok=True)
lock = json.loads((ROOT / 'build_lock.json').read_text())
failures = []

def require(condition, message):
    if not condition:
        failures.append(message)

def load_json(path):
    return json.loads(path.read_text())

run = ROOT / 'runs' / 'wokwi'
resolved_path = run / 'resolved.json'
resolved = load_json(resolved_path) if resolved_path.is_file() else {}
source_hash = hashlib.sha256((ROOT / 'src' / 'project.v').read_bytes()).hexdigest().upper()
require(source_hash == lock['source_sha256'], 'RTL source differs from v6')
expected = {
    'CLOCK_PERIOD': 25.0, 'IO_DELAY_CONSTRAINT': 10,
    'CLOCK_PORT': 'clk', 'PDK': 'gf180mcuD',
    'STD_CELL_LIBRARY': 'gf180mcu_fd_sc_mcu7t5v0',
    'SYNTH_STRATEGY': 'AREA 0', 'FP_CORE_UTIL': 50,
    'PL_TARGET_DENSITY_PCT': 60,
    'MAX_TRANSITION_CONSTRAINT': 3, 'MAX_CAPACITANCE_CONSTRAINT': 0.2,
    'MAX_FANOUT_CONSTRAINT': 10,
    'TIMING_VIOLATION_CORNERS': ['*'], 'HOLD_VIOLATION_CORNERS': ['*'],
}
for key, value in expected.items():
    require(resolved.get(key) == value, f'Unexpected resolved {key}: {resolved.get(key)}')
require(resolved.get('DIE_AREA') == [0, 0, 1440.32, 325.36], 'Floorplan differs')
require(resolved.get('meta', {}).get('librelane_version') == lock['librelane_version'], 'LibreLane version differs')
require(lock['pdk_version'] in resolved.get('PDK_ROOT', ''), 'PDK version differs')
tools_head = subprocess.run(['git', '-C', str(ROOT/'tt'), 'rev-parse', 'HEAD'], capture_output=True, text=True)
require(tools_head.returncode == 0 and tools_head.stdout.strip() == lock['support_tools_commit'], 'Support tools commit differs')

metrics_path = run / 'final' / 'metrics.csv'
metrics = {}
if metrics_path.is_file():
    with metrics_path.open(newline='') as f:
        for row in csv.DictReader(f):
            try:
                metrics[row['Metric']] = float(row['Value'])
            except ValueError:
                metrics[row['Metric']] = row['Value']
else:
    require(False, 'Final metrics.csv missing; build is incomplete')
    candidates = sorted(run.glob('*-openroad-stapostpnr/state_out.json'))
    if candidates:
        metrics = load_json(candidates[-1]).get('metrics', {})

sta_dirs = sorted(run.glob('*-openroad-stapostpnr'))
sta = sta_dirs[-1] if sta_dirs else None
require(sta is not None, 'Final routed STA reports missing')
constraints = list((run/'final').rglob('*.sdc')) if (run/'final').exists() else []
if not constraints and sta:
    constraints = list(sta.glob('*.sdc'))
if constraints:
    sdc = constraints[0].read_text()
    in_delays = [float(v) for v in re.findall(r'set_input_delay\s+([\d.]+)', sdc)]
    out_delays = [float(v) for v in re.findall(r'set_output_delay\s+([\d.]+)', sdc)]
    require(bool(in_delays) and bool(out_delays) and all(v == 2.5 for v in in_delays+out_delays), 'Final IO delay budget differs from 2.5 ns')
else:
    require(False, 'Final SDC missing')

corners = []
for corner in lock['sta_corners']:
    def metric(name):
        return metrics.get(f'{name}__corner:{corner}')
    setup = metric('timing__setup__ws')
    hold = metric('timing__hold__ws')
    slew = metric('design__max_slew_violation__count')
    cap = metric('design__max_cap_violation__count')
    fanout = metric('design__max_fanout_violation__count')
    require(setup is not None and hold is not None, f'{corner}: timing metrics missing')
    if setup is not None:
        require(setup >= 0, f'{corner}: setup slack {setup:.6f} ns')
    if hold is not None:
        require(hold >= 0, f'{corner}: hold slack {hold:.6f} ns')
    for kind, count in [('slew', slew), ('capacitance', cap), ('fanout', fanout)]:
        require(count == 0, f'{corner}: {kind} violations {count}')
    annotation = sta / corner / 'filter_unannotated_metrics.json' if sta else None
    meaningful_unannotated = None
    if annotation and annotation.is_file():
        meaningful_unannotated = load_json(annotation).get(f'timing__unannotated_net_filtered__count__corner:{corner}')
    require(meaningful_unannotated == 0, f'{corner}: unannotated functional nets {meaningful_unannotated}')
    old = lock['baseline_corners'][corner]
    corners.append(dict(corner=corner, setup_ns=setup, hold_ns=hold, slew=slew,
        capacitance=cap, fanout=fanout, baseline_setup_ns=old['setup_ns'],
        baseline_hold_ns=old['hold_ns'],
        setup_improvement_ns=setup-old['setup_ns'] if setup is not None else None))

physical_keys = ['magic__drc_error__count', 'design__lvs_error__count', 'route__drc_errors',
                 'antenna__violating__nets', 'antenna__violating__pins']
physical = {key: metrics.get(key) for key in physical_keys}
for key, value in physical.items():
    require(value == 0, f'{key}: {value}')
timing_pass = all(c['setup_ns'] is not None and c['setup_ns'] >= 0 and
                  c['hold_ns'] is not None and c['hold_ns'] >= 0 for c in corners)
electrical_pass = all(c[k] == 0 for c in corners for k in ('slew', 'capacitance', 'fanout'))
result = dict(status='PASS' if not failures else 'FAIL', timing_pass=timing_pass,
    electrical_pass=electrical_pass, source_sha256=source_hash, corners=corners,
    physical=physical, failures=failures, metrics=metrics,
    scope='Routed user-macro STA and physical checks. No SDF, FPGA/ADC, wrapper/pad or silicon signoff.')
(OUT/'assessment.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
lines = ['# GF 40 MHz routed build assessment', '',
    f"Timing: {'PASS' if timing_pass else 'FAIL'}; electrical rules: {'PASS' if electrical_pass else 'FAIL'}; complete build: {result['status']}.", '',
    '| Corner | 80 MHz setup ns | 40 MHz setup ns | Improvement ns | Hold ns | Slew | Cap | Fanout |',
    '|---|---:|---:|---:|---:|---:|---:|---:|']
def fmt(value):
    return 'missing' if value is None else f'{value:.6f}'
for c in corners:
    lines.append('| ' + ' | '.join([c['corner'], fmt(c['baseline_setup_ns']), fmt(c['setup_ns']),
        fmt(c['setup_improvement_ns']), fmt(c['hold_ns']), str(c['slew']), str(c['capacitance']), str(c['fanout'])]) + ' |')
lines.extend(['', '## Remaining checks', ''])
lines.extend('- '+f for f in failures)
lines.extend(['', result['scope'], ''])
(OUT/'assessment.md').write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps({k:result[k] for k in ('status','timing_pass','electrical_pass','failures')}, indent=2))
raise SystemExit(0 if not failures else 1)
