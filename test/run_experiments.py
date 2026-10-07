from pathlib import Path
import json, shutil, subprocess
ROOT = Path(__file__).resolve().parent
results = []
for folder, top, marker in [('fpga_startup_alignment','tb_fpga_alignment','FPGA_ALIGNMENT_TEST_PASS'),('phase_bias_probe','tb_phase_bias','PHASE_BIAS_PASS')]:
    out = ROOT/'output'/folder
    out.mkdir(parents=True, exist_ok=True)
    for source in (ROOT/'vectors'/folder).glob('*.hex'):
        shutil.copy2(source, out/source.name)
    commands = [('compile',['iverilog','-g2001','-Wall','-s',top,'-o',str(out/'sim.vvp'),str(ROOT.parent/'src/project.v'),str(ROOT/(top+'.v'))]),('simulation',['vvp',str(out/'sim.vvp')])]
    for name, command in commands:
        proc = subprocess.run(command, cwd=out, capture_output=True, text=True, timeout=180)
        (out/(name+'.log')).write_text(proc.stdout+proc.stderr)
        if proc.returncode:
            raise RuntimeError(folder+' '+name+' failed: '+proc.stdout+proc.stderr)
    assert marker in proc.stdout
    print(proc.stdout)
    results.append({'test':folder,'status':'PASS','clock_period_ns':25.0,'scope':'Ideal ADC input, RTL only; no SDF or analog delays.'})
(ROOT/'output/experiments.json').write_text(json.dumps(results,indent=2))
