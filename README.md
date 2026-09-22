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

The two counters now use one reset-priority assignment each, preserving their
increment and hold conditions. Local RTL equivalence and freshly synthesized GF180
functional gate-level checks each passed 460,637 cycles for this source, including
real divider levels 0, 1 and 5. See the verification record for tool versions and scope.

Cloud RTL, GDS, precheck and functional gate-level results are reported by Actions.
No SDF simulation is included. The previous v6 build had a gate-level startup X
failure and SS setup slack of -8.757775 ns; the new physical results must be checked
separately. Physical area reduction and SS timing closure are not claimed.
