// Whole-printer assembly for checking fit. Not for printing.
// openscad assembly.scad          (CARR_X moves the carriage, SHOW_PAPER adds a sheet)
include <fj.scad>
use <parts/side_plate.scad>
use <parts/carriage.scad>
use <parts/platen.scad>
use <parts/roller_hub.scad>
use <parts/star_wheel.scad>
use <parts/gt2_pulley_76t.scad>
use <parts/service_station.scad>
use <parts/x_motor_bracket.scad>
use <parts/x_idler_bracket.scad>
use <parts/sensor_bracket.scad>
use <parts/electronics_tray.scad>
use <parts/paper_tray.scad>
use <parts/rod_collar.scad>

CARR_X = 180;
SHOW_PAPER = true;

module rod(y, z, x0=-20, l=rod_len) { color("silver") translate([x0, y, z]) rotate([0,90,0]) cylinder(d=rod_d, h=l); }

module static_parts() {
    color("SteelBlue") { translate([-plate_t, 0, 0]) side_plate(false); translate([inner_w, 0, 0]) side_plate(true); }
    color("Gainsboro") for (s=[0:platen_segs-1]) platen(s);
    color("OrangeRed") { service_base(); service_sled(); }
    color("DimGray") { x_motor_bracket(); x_idler_bracket(); sensor_bracket(); }
    color("DarkSlateGray") electronics_tray();
    color("Wheat") { paper_tray("tray"); }
}

module rollers() {
    for (y=[in_y, out_y]) rod(y, shaft_z, -4, rod_len);
    rod(in_y, pinch_z, -14); rod(out_y, star_z, -14);
    color("black") for (x=tire_x) {
        for (y=[in_y, out_y]) translate([x - 7, y, shaft_z]) rotate([0,90,0]) roller_hub();
        translate([x - 7, in_y, pinch_z]) rotate([0,90,0]) roller_hub();
        translate([x - 2.5, out_y, star_z]) rotate([0,90,0]) star_wheel();
    }
    color("white") for (y=[in_y, out_y]) translate([inner_w + plate_t + 4, y, shaft_z]) rotate([0,90,0]) gt2_pulley_76t();
}

module collars() color("SteelBlue") {
    for (p=[[rail_y, rail_lo_z], [rail_y, rail_hi_z], [in_y, shaft_z], [out_y, shaft_z], [in_y, pinch_z], [out_y, star_z]]) {
        translate([-plate_t - collar_w, p[0], p[1]]) rotate([0,90,0]) rod_collar();
        translate([inner_w + plate_t, p[0], p[1]]) rotate([0,90,0]) rod_collar();
    }
}

module motors() {
    color("#333") {
        translate([-plate_t - 26 - 21, belt_y - 21, belt_z - 14 - 40]) cube([42, 42, 40]);           // X motor
        translate([inner_w - 40, feed_motor_y - 21, feed_motor_z - 21]) cube([40, 42, 42]);          // feed motor
    }
}

INK_COLORS = N_HEADS == 4 ? ["#202020", "#00a0dc", "#d8007f", "#f5d800"] :
             N_HEADS == 3 ? ["#00a0dc", "#d8007f", "#f5d800"] : ["#202020", "#9a9a9a"];
module cartridge() for (i=[0:N_HEADS-1]) translate([slot_x(i), 0, 0]) {
    color(INK_COLORS[i]) translate([-cart_w/2, -nz_back, head_gap]) cube([cart_w, cart_d, cart_h]);
    color("green") translate([-pcb_w/2, -nz_back - pcb_t, carr_z0]) cube([pcb_w, pcb_t, pcb_h]);
}

module moving_carriage(x) { translate([x, 0, 0]) { color("Gold") carriage(); cartridge(); } }

static_parts();
rollers();
collars();
motors();
for (z=[rail_lo_z, rail_hi_z]) rod(rail_y, z);
moving_carriage(CARR_X);
if (SHOW_PAPER) color("white", 0.6) translate([paper_x0, -150, 0]) cube([215.9, 279.4, 0.1]);
