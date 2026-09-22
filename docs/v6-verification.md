# v6 source and verification record

## Current revision: counter reset priority (2026-09-22)

- RTL SHA256: `7A9D7C5D6CDF0ABF4E5A51DBAE152718059D2807431050BA6E699761C63840B9`.
- Previous RTL SHA256: `AE377AFF09D813BD63B40F847447649CF1B8930161572D1E3C979158AD3ED169`.
- Baseline remains GF180 `gf180mcuD`, 4x2, 80 MHz / 12.5 ns, AREA 0.
- Only the update structure of `history_pointer` and `handoff_count` changes:
  each has one nonblocking assignment, selecting reset-to-zero, increment, or hold.
- Known-one enable comparisons preserve the original procedural-if behavior for X/Z.
- Top module, ports, parameters, algorithms, sample schedule and output latency remain
  unchanged. No additional registers, keep/dont_touch attributes, forced initial values,
  or hand-edited mapped cells are introduced.
- Level 23 retains its existing 78,125,000-clock divisor in this commit. The requested
  correction to 2^23 is a separate pending change, not part of this reset fix.

## Checks performed for the current source

| Check | Actual result |
|---|---|
| Original/current RTL, all outputs and both counters compared every cycle | PASS, 460,637 cycles, Icarus 12 |
| Newly synthesized GF180 netlist against unchanged independent model expectations | PASS, 460,637 cycles, Icarus 12 |
| Real divider levels 0 / 1 / 5 | PASS, 86,300 / 46,300 / 8,800 samples |
| Both counters zero after every reset edge in the gate-level run | PASS |
| Replay of original failing startup inputs through 512.501 ns | PASS, Icarus 12 and 13 |
| Independent mapped-netlist connectivity check | PASS, 0 problems |

The complete runs include illegal configuration, latch without immediate sampling,
default handoff, saturation/recovery, candidate expiry, refill, newer ties, reset,
pending-sample discard, and zero/max inputs. All output data, type and enables are
checked each cycle; X/Z, contention and mismatches fail. Source snapshots, logs,
vectors and waves were retained locally. Icarus 13 only ran the startup replay;
the complete regression is not claimed to have passed on both simulator versions.

Expected vectors came from the existing pin-only `test/test.py` reference model and
test sequence without changing their algorithms or expected values. The local Verilog
replay retains per-cycle output and contention checks. The repository's cloud cocotb
test, reference model and workflow files remain unchanged in this commit.

## Synthesis and physical scope

Local synthesis used Yosys 0.62 / `7326bb7d6` (YoWASP) and a command-sequence
translation of LibreLane 3.0.14, using built-in opt passes, the original build's
filtered GF180 liberty, AREA 0 ABC script and 12.5 ns constraint. This is not a run
of the complete GitHub/Nix physical flow. The unchanged RTL also failed startup in
this local flow, while the candidate passed; the local baseline's X timing differed
from the cloud baseline, so byte-identical mapping is not claimed.

New local mapped-netlist SHA256:
`AD297F6A172A64DBAC5A25364BB3CAAEAD193718C842BA9138906EC364C1DCE9`.
This netlist was generated from the revised RTL, without the earlier diagnostic
four-bit reset patch. Local synthesis area estimates are not post-layout measurements.

The [previous cloud build](https://github.com/BarryLee911/tt-gf-ucl-project-v6/actions/runs/35673421547)
at `c5d76616f5734e5cc554a01b73c093a09ba11d26` passed RTL, GDS generation and precheck,
but failed functional gate simulation; its worst SS setup slack was -8.757775 ns.
The current source has not yet completed a new physical build. SS timing closure,
physical area improvement, and a new cloud gate-level PASS are not claimed here.
No SDF simulation is added and no timing constraint is relaxed.

## Historical record: initial v6 source, not current-source validation

Everything below refers to the previous RTL hash and its initial upload record.
It is retained for provenance and does not replace the current checks above.

### Source and baseline

- v6 RTL SHA256: `AE377AFF09D813BD63B40F847447649CF1B8930161572D1E3C979158AD3ED169`.
- Template: `BarryLee911/tt-gf-ucl-project-v5`, `trial-4x2`, `d611e620a799619f136ed79b17ad873b106b6530`.
- Configuration: GF180 `gf180mcuD`, 4x2, 80 MHz / 12.5 ns, AREA 0.
- Placement density 60%, placement hold margin 0.5 ns, global-route hold margin 0.05 ns are retained.
- AREA 0 is explicitly pinned to the strategy recorded for the v5 baseline.
- Top module, external pins, parameters, and RTL bytes are unchanged from the local v6 source.

### Verified local run for this source

2026-09-21, level 5, real clock division, sine phase 37.5 degrees, 9.64 seconds.
The source snapshot SHA256 matches the uploaded RTL.

`PIPELINE_PASS,5,real,606360,18948,18948,263175,263175,65536,65536,2048,37.500000`

606,360 clock edges and 18,948 samples were checked. The run checked all output pins,
sample/processing pairing, an independent candidate model, sine and zero-input stages,
and 2,048 checks with ena low. Output frames: 263,175 area and 263,175 peak.
The original local run retains its complete snapshots, log and waveform; large artifacts
and machine-specific paths are not included here.

This is one verified case, not a claim that every level or the complete regression passed.
The older regression before the flat-if rewrite does not validate this source.

### Cloud validation

The inherited pin-only cocotb algorithm and expected values are unchanged; only the
version label in its report changes. RTL and functional gate-level tests retain levels
0, 1 and 5, illegal configuration, default handoff, saturation/recovery, candidate expiry,
buffer refill, newer ties, reset, pending-sample discard, and zero/max input cases.
Unknown outputs, pin contention, mismatches and missing required coverage fail the tests.

Actions runs RTL tests, GDS, precheck and functional gate-level checks on this revision.
FPGA remains manual. The GDS viewer uses the new repository's GitHub Pages.
SDF simulation is not included. No new physical PASS, area reduction or SS setup closure
is claimed before this revision's reports are available. TT setup and all-corner hold
checks remain enabled, with SS setup reported separately by the physical results.
