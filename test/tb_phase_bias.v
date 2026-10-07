`timescale 1ns/1ps
module tb_phase_bias;
  reg clk=0, rst_n=0;
  reg [7:0] adc_plus=128, adc_minus=128;
  reg [7:0] plus_codes[0:2047], minus_codes[0:2047];
  wire [7:0] po,pu,pe,mo,mu,me;
  wire [10:0] plus_data={pu[7:5],po}, minus_data={mu[7:5],mo};
  integer n,areas=0,peaks=0;
  tt_um_sine_area_detector positive(.ui_in(adc_plus),.uo_out(po),.uio_in(8'd0),.uio_out(pu),.uio_oe(pe),.ena(1'b1),.clk(clk),.rst_n(rst_n));
  tt_um_sine_area_detector negative(.ui_in(adc_minus),.uo_out(mo),.uio_in(8'd0),.uio_out(mu),.uio_oe(me),.ena(1'b1),.clk(clk),.rst_n(rst_n));
  task tick;
    begin clk=0; #12.5; clk=1; #12.5; end
  endtask
  initial begin
    $readmemh("plus.hex",plus_codes); $readmemh("minus.hex",minus_codes);
    repeat(4) tick;
    rst_n=1; tick;
    for(n=0;n<100000;n=n+1) begin
      adc_plus=plus_codes[n%2048]; adc_minus=minus_codes[n%2048]; tick;
      if(n>=82000) begin
        if(pe !== 8'he1 || me !== 8'he1 || pu[0] !== mu[0]) $fatal(1,"Output control mismatch");
        if(pu[0]===1'b0) begin
          if(plus_data !== 11'd768 || minus_data !== 11'd1280) $fatal(1,"Biased area mismatch %0d %0d",plus_data,minus_data);
          areas=areas+1;
        end else begin
          if(plus_data !== 11'd120 || minus_data !== 11'd120) $fatal(1,"Peak mismatch");
          peaks=peaks+1;
        end
      end
    end
    $display("PHASE_BIAS_PASS bias=90deg delta_plus=22.5deg area_plus=768 delta_minus=-22.5deg area_minus=1280 area_frames=%0d peak_frames=%0d",areas,peaks);
    $finish;
  end
endmodule
