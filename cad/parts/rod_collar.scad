// Printed split collar for the 8 mm rods (print 12, PETG, 100 % infill). M3x16 + nut.
// Replaces bought shaft collars: rails, drive shafts, pinch shaft and star shaft each get
// one collar against the outside of each side plate.
include <../fj.scad>
module rod_collar() difference() {
    union() {
        cylinder(d=collar_od, h=collar_w);
        translate([0, -5, 0]) cube([collar_od/2 + 5, 10, collar_w]);
    }
    translate([0,0,-1]) cylinder(d=rod_d + 0.2, h=collar_w + 2);
    translate([0, -0.75, -1]) cube([collar_od, 1.5, collar_w + 2]);              // slit
    translate([collar_od/2 + 1, 0, collar_w/2]) rotate([90,0,0]) {
        cylinder(d=m3, h=20, center=true);
        translate([0,0,4]) cylinder(d=m3_head + 0.4, h=10);
        translate([0,0,-4 - 10]) rotate(30) cylinder(d=m3_nut/cos(30), h=10, $fn=6);
    }
}
rod_collar();
