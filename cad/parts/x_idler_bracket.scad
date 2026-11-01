// Carriage belt idler - bolts to the outside of the RIGHT plate. 20T GT2 idler (5 mm bore)
// on an M5x30 bolt; the slot lets you tension the belt.
include <../fj.scad>
module x_idler_bracket() {
x0 = inner_w + plate_t;
ix = x0 + 20;
difference() {
    union() {
        translate([x0, belt_y - 24, belt_z - 30]) cube([5, 46, 60]);
        for (z=[belt_z - 11, belt_z + 7]) translate([x0, belt_y - 9, z]) cube([30, 18, 4]);
    }
    for (p=[[belt_y-18, belt_z+24], [belt_y+16, belt_z+24], [belt_y-18, belt_z-24]])
        translate([x0 + 2.5, p[0], p[1]]) rotate([0,90,0]) cylinder(d=m3, h=12, center=true);
    hull() for (dx=[-4, 4]) translate([ix + dx, belt_y, belt_z]) cylinder(d=5.3, h=40, center=true);
    translate([x0 + 5, belt_y - 8, belt_z - 7]) cube([30, 16, 14]);   // room for the idler
}
}
x_idler_bracket();
