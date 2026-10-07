# TinyTapeout v6 GF 40 MHz experiment

Independent 40 MHz operating-point experiment based on v6 commit dae8933.
RTL is byte-identical to v6. The system clock constraint is 25 ns; the 80000-cycle handoff is about 2 ms.

See [实验说明与档位表](docs/GF40MHz实验说明.md) and [build provenance](build_lock.json).
All nine setup and hold corners are required. The build assessment distinguishes timing closure from electrical rule closure.
The original v6 main branch and published viewer are preserved.

Local verification reports and build artifacts are stored in verification/. GitHub Actions retains failed-build logs.
Functional gate simulation has no SDF; FPGA, ADC, pad/wrapper and silicon verification remain separate.
