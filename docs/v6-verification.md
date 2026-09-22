# v6 source and verification record

## Source and baseline

- v6 RTL SHA256: `AE377AFF09D813BD63B40F847447649CF1B8930161572D1E3C979158AD3ED169`.
- Template: `BarryLee911/tt-gf-ucl-project-v5`, `trial-4x2`, `d611e620a799619f136ed79b17ad873b106b6530`.
- Configuration: GF180 `gf180mcuD`, 4x2, 80 MHz / 12.5 ns, AREA 0.
- Placement density 60%, placement hold margin 0.5 ns, global-route hold margin 0.05 ns are retained.
- AREA 0 is explicitly pinned to the strategy recorded for the v5 baseline.
- Top module, external pins, parameters, and RTL bytes are unchanged from the local v6 source.

## Verified local run for this source

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

## Cloud validation

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
