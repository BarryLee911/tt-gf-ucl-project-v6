# Mengrui's project v6

GF180 sine sign-overlap and approximate peak detector, with cleaned names,
merged duplicate validity state, and flat sequential `if` statements.

Target: **4x2 tiles, 80 MHz (12.5 ns), AREA 0**, using TinyTapeout `ttgf26c`.
The top module, pins, parameters, sampling schedule, and pipeline latency are unchanged.

[Interface](docs/info.md) · [Verification record](docs/v6-verification.md) ·
[Builds](https://github.com/BarryLee911/tt-gf-ucl-project-v6/actions)

The engineering template is v5 `trial-4x2` at
[`d611e62`](https://github.com/BarryLee911/tt-gf-ucl-project-v5/commit/d611e620a799619f136ed79b17ad873b106b6530).
The original v5 repository is retained separately; its `main` is the older 3x4 design.

One local level-5 real-divider test passed for this exact source. Current v6 cloud
RTL, GDS, precheck, and functional gate-level results are reported by Actions.
No SDF simulation is included. The v5 SS setup violation is historical and must
be reassessed from the new build; area reduction has not yet been measured.
