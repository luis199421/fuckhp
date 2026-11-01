// Collision check: intersects the volume swept by the carriage over its whole travel with
// every fixed part. The result must be EMPTY:  openscad -o /tmp/x.stl check_collisions.scad
// ("Current top level object is empty" = pass). Takes ~2 minutes.
include <fj.scad>
use <parts/side_plate.scad>
use <parts/carriage.scad>
use <parts/platen.scad>
use <parts/roller_hub.scad>
use <parts/star_wheel.scad>
use <parts/sensor_bracket.scad>
use <parts/x_motor_bracket.scad>
use <parts/x_idler_bracket.scad>
$fn=24;
module sweep() hull() for (x=[home_x + head_span/2, inner_w - carr_w/2 - 3]) translate([x,0,0]) {
    carriage();
    for (i=[0:N_HEADS-1]) translate([slot_x(i) - cart_w/2, -nz_back, head_gap]) cube([cart_w, cart_d, cart_h]);
}
module statics() {
    translate([-plate_t, 0, 0]) side_plate(false); translate([inner_w, 0, 0]) side_plate(true);
    for (s=[0:platen_segs-1]) platen(s);
    sensor_bracket(); x_motor_bracket(); x_idler_bracket();
    for (x=tire_x) {
        translate([x - 7, in_y, pinch_z]) rotate([0,90,0]) roller_hub();
        translate([x - 2.5, out_y, star_z]) rotate([0,90,0]) star_wheel();
    }
    for (y=[in_y, out_y]) translate([-4, y, y == in_y ? pinch_z : star_z]) rotate([0,90,0]) cylinder(d=rod_d, h=rod_len);
    translate([-30, belt_back_y - 0.7, belt_z - 3]) cube([inner_w + 60, 1.4, 6]);   // return belt strand
    translate([sensor_x - 1, sensor_y - 6, -2]) cube([2, 12, 3.5]);                 // paper lever tip
}
intersection() { sweep(); statics(); }
