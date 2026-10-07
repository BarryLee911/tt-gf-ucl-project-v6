`timescale 1ns/1ps
module tb_fpga_alignment;
  reg clk = 0;
  reg rst_n = 0;
  reg ena = 1;
  reg [7:0] config_pins = 0;
  reg [7:0] adc_continuous = 128;
  reg [7:0] adc_aligned = 128;
  reg [7:0] adc_restarted = 128;
  reg [7:0] sine_codes [0:2047];
  wire [7:0] out_c, io_c, oe_c, out_a, io_a, oe_a, out_r, io_r, oe_r;
  wire [10:0] data_c = {io_c[7:5], out_c};
  wire [10:0] data_a = {io_a[7:5], out_a};
  wire [10:0] data_r = {io_r[7:5], out_r};
  integer k, level, divisor, expected_position, local_position;
  integer checks = 0;
  integer late_start = 80017;
  integer area_frames = 0;
  integer peak_frames = 0;

  tt_um_sine_area_detector continuous_source (
    .ui_in(adc_continuous), .uo_out(out_c), .uio_in(config_pins),
    .uio_out(io_c), .uio_oe(oe_c), .ena(ena), .clk(clk), .rst_n(rst_n));
  tt_um_sine_area_detector aligned_source (
    .ui_in(adc_aligned), .uo_out(out_a), .uio_in(config_pins),
    .uio_out(io_a), .uio_oe(oe_a), .ena(ena), .clk(clk), .rst_n(rst_n));
  tt_um_sine_area_detector restarted_source (
    .ui_in(adc_restarted), .uo_out(out_r), .uio_in(config_pins),
    .uio_out(io_r), .uio_oe(oe_r), .ena(ena), .clk(clk), .rst_n(rst_n));

  task tick;
    begin clk = 0; #12.5; clk = 1; #12.5; end
  endtask

  task reset_chip;
    input integer requested_level;
    begin
      rst_n = 0;
      ena = 1;
      config_pins = requested_level;
      adc_continuous = 128;
      adc_aligned = 128;
      adc_restarted = 128;
      repeat (4) tick;
      rst_n = 1;
    end
  endtask

  task check_config_edge;
    begin
      tick;
      if (continuous_source.config_latched_valid !== 1'b1 ||
          continuous_source.sample_valid !== 1'b0 ||
          continuous_source.history_pointer !== 11'd0)
        $fatal(1, "Configuration edge unexpectedly sampled or failed to latch");
    end
  endtask

  task check_sample_edge;
    input integer elapsed;
    input integer spacing;
    begin
      if (continuous_source.sample_valid !== ((elapsed % spacing) == 0))
        $fatal(1, "Sample timing mismatch k=%0d D=%0d", elapsed, spacing);
      if ((elapsed % spacing) == 0) begin
        if (continuous_source.sample_position !== ((elapsed / spacing - 1) % 2048))
          $fatal(1, "Saved position mismatch k=%0d D=%0d", elapsed, spacing);
      end
      if (continuous_source.history_pointer !== ((elapsed / spacing) % 2048))
        $fatal(1, "Reference phase mismatch k=%0d D=%0d", elapsed, spacing);
      checks = checks + 1;
    end
  endtask

  initial begin
    $readmemh("plus.hex", sine_codes);
    // Verify actual clock edges for representative dividers, without altering DUT state.
    for (level = 0; level <= 7; level = level + 1) begin
      if (level == 0 || level == 1 || level == 5 || level == 7) begin
        reset_chip(level);
        check_config_edge;
        divisor = 1 << level;
        for (k = 1; k <= 2 * divisor + 2; k = k + 1) begin
          tick;
          check_sample_edge(k, divisor);
        end
        $display("STARTUP_PASS level=%0d first_sample=C+%0d second_sample=C+%0d", level, divisor, 2 * divisor);
      end
    end

    // Illegal configuration waits; changing pins or ena after latching does not stop/rephase.
    reset_chip(24);
    repeat (11) begin
      tick;
      if (continuous_source.config_latched_valid !== 1'b0 ||
          continuous_source.sample_valid !== 1'b0 ||
          continuous_source.history_pointer !== 11'd0)
        $fatal(1, "Illegal configuration advanced the reference");
    end
    config_pins = 5;
    check_config_edge;
    config_pins = 0;
    ena = 0;
    for (k = 1; k <= 66; k = k + 1) begin
      tick;
      check_sample_edge(k, 32);
    end
    $display("CONFIG_PASS illegal_wait=11 latched_level=5 later_pin_level=0 ena=0 spacing=32");

    // Ideal ADC-level experiment: same sinusoid, same frequency, starts after handoff.
    // The supplied table has 90-degree bias plus 22.5-degree lead.
    reset_chip(5);
    check_config_edge;
    divisor = 32;
    for (k = 1; k <= late_start + 2048 * divisor + 4096; k = k + 1) begin
      expected_position = ((k - 1) / divisor) % 2048;
      adc_continuous = sine_codes[expected_position];
      if (k >= late_start) begin
        adc_aligned = sine_codes[expected_position];
        local_position = ((k - late_start) / divisor) % 2048;
        adc_restarted = sine_codes[local_position];
      end
      tick;
      check_sample_edge(k, divisor);
      if (k == 79999 && oe_c !== 8'he0)
        $fatal(1, "Handoff occurred too early");
      if (k >= 80000 && (oe_c !== 8'he1 || oe_a !== 8'he1 || oe_r !== 8'he1))
        $fatal(1, "Handoff was late");
      if (k == 80000 && continuous_source.window_full !== 1'b1)
        $display("HANDOFF_OBSERVATION window_full=0 at_C+80000");
      if (k >= late_start + 2048 * divisor + 16) begin
        if (io_c[0] !== io_a[0] || io_c[0] !== io_r[0])
          $fatal(1, "Output types disagree");
        if (io_c[0] == 0) begin
          if (data_c !== 11'd768 || data_a !== 11'd768 || data_r !== 11'd1672)
            $fatal(1, "Late-start area mismatch continuous=%0d aligned=%0d restarted=%0d", data_c, data_a, data_r);
          area_frames = area_frames + 1;
        end else begin
          if (data_c !== 11'd120 || data_a !== 11'd120 || data_r !== 11'd120)
            $fatal(1, "Late-start peak mismatch");
          peak_frames = peak_frames + 1;
        end
      end
    end
    $display("LATE_ALIGNMENT_PASS level=5 start=C+%0d continuous_area=768 aligned_area=768 zero_restart_area=1672 area_frames=%0d peak_frames=%0d checks=%0d", late_start, area_frames, peak_frames, checks);

    // Handoff is a direction change on uio[0], not a complete-window indication.
    reset_chip(7);
    check_config_edge;
    for (k = 1; k <= 80000; k = k + 1) tick;
    if (oe_c !== 8'he1 || continuous_source.window_full !== 1'b0 ||
        continuous_source.history_pointer !== 11'd625)
      $fatal(1, "Handoff/window observation mismatch");
    $display("HANDOFF_PASS level=7 ready=C+80000 samples=625 window_full=0");
    $display("FPGA_ALIGNMENT_TEST_PASS");
    $finish;
  end
endmodule
