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
    Param(10, "x_travel_um", 300000, 50000, 800000, "usable carriage travel from home"),
    Param(11, "home_speed_mm_s", 25, 2, 100, "homing speed"),
    Param(12, "home_backoff_um", 3000, 0, 20000, "distance to back off the switch after homing"),
    # --- geometry (calibrated) ---------------------------------------------
    Param(20, "col0_x_um", 40000, 0, 800000,
          "black row-0 nozzles X (from home) over the paper's left edge"),
    Param(22, "bidir_offset_um", 0, -2000, 2000, "shift applied to right-to-left passes"),
    Param(24, "sensor_to_nozzle_um", 31000, 0, 300000,
          "feed from the sheet resting in the roller nip to its edge reaching the exit-most nozzle"),
    Param(25, "eject_um", 40000, 0, 500000, "feed after the trailing edge passes the paper sensor"),
    Param(26, "spit_x_um", 32000, 0, 300000, "black nozzles X over the spittoon"),
    Param(27, "max_cols", 5184, 100, 7000, "widest printable line in 1/600 in columns"),
    Param(28, "cutter_um", 78000, 0, 200000, "roll mode: distance from the exit-most nozzle to the tear-off edge"),
    Param(29, "sheet_tail_um", 17000, 0, 100000,
          "sheets: paper still moves this far after its trailing edge passes the sensor (sensor -> roller nip)"),
    # --- cartridges (HP 63 / 302 / 123 / 803) ------------------------------------------
    Param(40, "cartridges", 1, 1, 3, "fitted: 1 = black, 2 = colour, 3 = black + colour"),
    Param(41, "k_row_gap_um", 4000, -8000, 8000, "black cartridge: nozzle row 1 vs row 0 (freejet test rows)"),
    Param(42, "spit_count", 40, 0, 2000, "firing cycles spat into the spittoon before each page"),
    Param(43, "color_x_um", 25000, -60000, 60000, "cyan nozzles vs black row 0 (freejet test colors)"),
    Param(44, "cmy_pitch_um", 4000, -10000, 10000, "magenta vs cyan and yellow vs magenta nozzle columns"),
    Param(45, "k_dy_rows", 78, 0, 156, "colour jobs: black nozzle row lined up with the top colour nozzle"),
    Param(46, "vhd_min_mv", 14500, 5000, 20000, "refuse to fire below this heater supply voltage (16 V rail)"),
    Param(47, "nozzle_flip", 0, 0, 1, "1 if nozzle numbers grow towards the paper entry instead of the exit"),
    # --- misc ----------------------------------------------------------------
    Param(60, "idle_motor_off_s", 30, 0, 3600, "disable motors after this many idle seconds (0 = never)"),
    Param(61, "job_timeout_s", 120, 5, 3600, "abort a job if the host goes silent this long mid-page"),
]

BY_NAME = {p.name: p for p in PARAMS}
BY_ID = {p.id: p for p in PARAMS}
