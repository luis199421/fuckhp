"""Printer parameters shared by the host driver and the firmware.

This file is the single source of truth: `tools/gen_params.py` turns it into
firmware/src/params_table.h, and a test checks the two stay in sync.
All values are signed 32-bit integers; units are in the name.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Param:
    id: int
    name: str
    default: int
    min: int
    max: int
    help: str


PARAMS = [
    # --- motion -------------------------------------------------------------
    Param(1, "x_steps_per_m", 80000, 10000, 400000,
          "carriage steps per metre (GT2 20T pulley, 1/16 step = 80 steps/mm)"),
    Param(2, "y_steps_per_m", 175900, 10000, 1000000,
          "paper feed steps per metre (76T/20T belt, 22 mm roller, 1/16 step); calibrate with `freejet test feed`"),
    Param(3, "x_speed_mm_s", 80, 5, 150, "carriage cruise speed while printing"),
    Param(4, "x_accel_mm_s2", 1500, 100, 10000, "carriage acceleration"),
    Param(5, "x_travel_speed_mm_s", 120, 5, 250, "carriage speed for non-printing moves"),
    Param(6, "y_speed_mm_s", 40, 1, 150, "paper feed speed"),
    Param(7, "y_accel_mm_s2", 400, 50, 5000, "paper feed acceleration"),
    Param(8, "x_dir_invert", 0, 0, 1, "flip carriage motor direction"),
    Param(9, "y_dir_invert", 0, 0, 1, "flip feed motor direction"),
    Param(10, "x_travel_um", 300000, 50000, 600000, "usable carriage travel from home"),
    Param(11, "home_speed_mm_s", 25, 2, 100, "homing speed"),
    Param(12, "home_backoff_um", 3000, 0, 20000, "distance to back off the switch after homing"),
    # --- geometry (calibrated) ---------------------------------------------
    Param(20, "col0_x_um", 40000, 0, 600000,
          "head reference X (from home) that sits over the paper's left edge"),
    Param(21, "row_gap_um", 4050, -8000, 8000,
          "signed distance from even to odd nozzle column (+ = odd column is toward +X)"),
    Param(22, "bidir_offset_um", 0, -2000, 2000, "shift applied to right-to-left passes"),
    Param(23, "nozzle0_downstream", 1, 0, 1,
          "1 if nozzle 0 is the nozzle closest to the paper exit"),
    Param(24, "sensor_to_nozzle_um", 60000, 0, 300000,
          "feed distance from the paper sensor switching to the leading edge reaching the exit-most nozzle"),
    Param(25, "eject_um", 120000, 0, 500000, "extra feed after the trailing edge passes the sensor"),
    Param(26, "spit_x_um", 20000, 0, 200000, "carriage X over the spittoon"),
    Param(27, "max_cols", 5184, 100, 7000, "widest printable line in 1/600 in columns"),
    Param(28, "cutter_um", 78000, 0, 200000, "roll mode: distance from the exit-most nozzle to the tear-off edge"),
    # --- printhead -----------------------------------------------------------
    Param(40, "pulse_ns", 1800, 500, 2400, "fire pulse width (hardware one-shot caps it near 3 us)"),
    Param(41, "prim_groups", 3, 1, 4, "split each address into this many sub-pulses to limit heat/current"),
    Param(42, "spit_count", 40, 0, 2000, "drops per nozzle spat into the spittoon before each page"),
    Param(43, "tsr_min", 200, 0, 4095, "TSR ADC reading below this = no cartridge / short"),
    Param(44, "tsr_max", 3900, 0, 4095, "TSR ADC reading above this = no cartridge / open"),
    Param(45, "tsr_hot_delta", 400, 10, 4095, "pause between passes when TSR rises this much above cold value"),
    Param(46, "vhd_min_mv", 10500, 5000, 16000, "refuse to fire below this head supply voltage"),
    # --- extra cartridges (grayscale / colour builds) -------------------------
    Param(47, "n_heads", 1, 1, 4, "cartridges fitted: 1 black, 2 black+light black, 3 CMY, 4 KCMY"),
    Param(48, "head1_x_um", 28000, 5000, 150000, "slot 1 nozzle position right of slot 0 (calibrate: freejet test heads)"),
    Param(49, "head2_x_um", 56000, 5000, 150000, "slot 2 nozzle position right of slot 0"),
    Param(50, "head3_x_um", 84000, 5000, 150000, "slot 3 nozzle position right of slot 0"),
    Param(51, "head1_dy_rows", 0, -6, 6, "slot 1 vertical alignment in 1/600 in rows (uses spare nozzles)"),
    Param(52, "head2_dy_rows", 0, -6, 6, "slot 2 vertical alignment"),
    Param(53, "head3_dy_rows", 0, -6, 6, "slot 3 vertical alignment"),
    # --- misc ----------------------------------------------------------------
    Param(60, "idle_motor_off_s", 30, 0, 3600, "disable motors after this many idle seconds (0 = never)"),
    Param(61, "job_timeout_s", 120, 5, 3600, "abort a job if the host goes silent this long mid-page"),
]

BY_NAME = {p.name: p for p in PARAMS}
BY_ID = {p.id: p for p in PARAMS}
