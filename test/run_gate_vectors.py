"""Replay baseline v6 pin vectors on the 40 MHz routed netlist, without SDF."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, time

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--netlist',type=Path,required=True)
    p.add_argument('--models',type=Path,required=True)
    p.add_argument('--vectors',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    a.netlist=a.netlist.resolve()
    a.models=a.models.resolve()
    a.vectors=a.vectors.resolve()
    a.output=a.output.resolve()
    a.output.mkdir(parents=True,exist_ok=True)
    count=len(a.vectors.read_text().splitlines())
    shutil.copy2(a.vectors,a.output/'vectors.hex')
    tb='''`timescale 1ps/1ps
module tb;
reg clk=0,rst_n,ena,external_drive0;
reg [7:0] ui_in,uio_in;
wire [7:0] uo_out,uio_out,uio_oe;
tri pad0;
wire [7:0] input_pins={uio_in[7:1],pad0};
assign pad0=external_drive0 ? uio_in[0] : 1'bz;
assign pad0=uio_oe[0] ? uio_out[0] : 1'bz;
tt_um_sine_area_detector dut(.clk(clk),.rst_n(rst_n),.ena(ena),.ui_in(ui_in),.uio_in(input_pins),.uo_out(uo_out),.uio_out(uio_out),.uio_oe(uio_oe));
reg [42:0] vectors[0:COUNT_MINUS_ONE];
integer i;
initial begin
$readmemh("vectors.hex",vectors);
for(i=0;i<COUNT;i=i+1)begin
clk=0;{rst_n,ena,external_drive0,ui_in,uio_in}=vectors[i][42:24];
#12500;clk=1;#12500;
if({uo_out,uio_out,uio_oe} !== vectors[i][23:0]) $fatal(1,"FAIL cycle=%0d actual=%h expected=%h",i+1,{uo_out,uio_out,uio_oe},vectors[i][23:0]);
if(external_drive0 && uio_oe[0]) $fatal(1,"CONTENTION cycle=%0d",i+1);
if(uio_oe[0] && pad0 !== uio_out[0]) $fatal(1,"PAD mismatch cycle=%0d",i+1);
if(i%50000==0)$display("checked %0d cycles",i+1);
end
$display("GATE_VECTOR_PASS cycles=%0d clock_period_ns=25 no_SDF",i);$finish;
end
endmodule
'''.replace('COUNT_MINUS_ONE',str(count-1)).replace('COUNT',str(count))
    (a.output/'tb.v').write_text(tb)
    iv=shutil.which('iverilog') or r'C:\iverilog\bin\iverilog.exe'
    vv=shutil.which('vvp') or r'C:\iverilog\bin\vvp.exe'
    stages=[('compile',[iv,'-g2001','-DFUNCTIONAL','-s','tb','-o',str(a.output/'gate.vvp'),str(a.models/'primitives.v'),str(a.models/'cells.v'),str(a.netlist),str(a.output/'tb.v')]),('simulation',[vv,str(a.output/'gate.vvp')])]
    logs=[]
    for name,cmd in stages:
        started=time.monotonic()
        with (a.output/(name+'.log')).open('w') as log:
            proc=subprocess.run(cmd,cwd=a.output,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        logs.append({'stage':name,'returncode':proc.returncode,'seconds':time.monotonic()-started,'command':cmd})
        if proc.returncode: break
    result={'status':'PASS' if len(logs)==2 and all(s['returncode']==0 for s in logs) and 'GATE_VECTOR_PASS' in (a.output/'simulation.log').read_text() else 'FAIL','cycles':count,'clock_period_ns':25,'netlist_sha256':hashlib.sha256(a.netlist.read_bytes()).hexdigest(),'vectors_sha256':hashlib.sha256(a.vectors.read_bytes()).hexdigest(),'model_hashes':{f:hashlib.sha256((a.models/f).read_bytes()).hexdigest() for f in ['cells.v','primitives.v']},'stages':logs,'scope':'Pin-level functional replay. FUNCTIONAL cell models, no SDF and no timing validation.'}
    (a.output/'results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='PASS' else 1)

if __name__=='__main__': main()
