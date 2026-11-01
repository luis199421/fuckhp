// Whole-printer assembly for checking fit. Not for printing.
// openscad assembly.scad   (-D 'CARTS="KCMY"', -D CARR_X=200, -D SHOW_PAPER=false, -D SHOW_ROLL=true)
include <fj.scad>
use <parts/side_plate.scad>
use <parts/carriage.scad>
use <parts/platen.scad>
use <parts/roller_hub.scad>
use <parts/gt2_pulley_60t.scad>
use <parts/service_station.scad>
use <parts/x_motor_bracket.scad>
use <parts/x_idler_bracket.scad>
use <parts/sensor_bracket.scad>
use <parts/electronics_tray.scad>
use <parts/paper_tray.scad>
use <parts/rod_collar.scad>
use <parts/leaf_bar.scad>

CARR_X = 180;
SHOW_PAPER = true;
SHOW_ROLL = false;

module rod(y, z, x0=-20, l=rod_len) { color("silver") translate([x0, y, z]) rotate([0,90,0]) cylinder(d=rod_d, h=l); }

INK_COLORS = ["#202020", "#00a0dc"];
module cartridges() for (i=[0:N_SLOTS-1]) translate([slot_x(i), 0, 0])
    color(slot_ink(i) == "K" ? INK_COLORS[0] : "#e8e8e8") translate([-cart_w/2, -nz_back, head_gap]) cube([cart_w, cart_d, cart_h]);

module leaves() color("LightSteelBlue") for (x=tire_x)
    hull() { translate([x - leaf_w/2, leaf_bar_y + 6, leaf_bar_z + 1.5]) cube([leaf_w, 1, 0.3]);
             translate([x - leaf_w/2, leaf_y1, 0.1]) cube([leaf_w, 1, 0.3]); }

module static_parts() {
    color("SteelBlue") { translate([-plate_t, 0, 0]) side_plate(false); translate([inner_w, 0, 0]) side_plate(true); }
    color("Gainsboro") for (s=[0:platen_segs-1]) platen(s);
    color("OrangeRed") { service_base(); service_sled(); }
    color("DimGray") { x_motor_bracket(); x_idler_bracket(); sensor_bracket(); }
    color("DarkSlateGray") electronics_tray();
    color("Wheat") paper_tray("tray");
    color("Peru") { leaf_bar_piece(0); leaf_bar_piece(1); }
    leaves();
}

module feed() {
    rod(feed_y, shaft_z, -4, rod_len);
    color("black") for (x=tire_x) translate([x - 7, feed_y, shaft_z]) rotate([0,90,0]) roller_hub();
    color("white") translate([inner_w + plate_t + 4, feed_y, shaft_z]) rotate([0,90,0]) gt2_pulley_60t();
    color("#333") translate([inner_w - 40, feed_motor_y - 21, feed_motor_z - 21]) cube([40, 42, 42]);   // feed motor
    color("#333") translate([-plate_t - 26 - 21, belt_y - 21, belt_z - 14 - 40]) cube([42, 42, 40]);    // X motor
}

module collars() color("SteelBlue")
    for (p=[[rail_y, rail_lo_z], [rail_y, rail_hi_z], [feed_y, shaft_z]]) {
        translate([-plate_t - collar_w, p[0], p[1]]) rotate([0,90,0]) rod_collar();
        translate([inner_w + plate_t, p[0], p[1]]) rotate([0,90,0]) rod_collar();
    }

static_parts();
feed();
collars();
for (z=[rail_lo_z, rail_hi_z]) rod(rail_y, z);
translate([CARR_X, 0, 0]) { color("Gold") carriage(); cartridges(); }
if (SHOW_PAPER) color("white", 0.6) translate([paper_x0, -150, 0.6]) cube([215.9, 279.4, 0.1]);
if (SHOW_ROLL) {
    color("white") translate([paper_x0, roll_y, roll_z]) rotate([0,90,0]) cylinder(d=85, h=216);
    rod(roll_y, roll_z, -16, inner_w + 32);
}
