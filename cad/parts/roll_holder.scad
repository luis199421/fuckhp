// Optional roll-paper holder (replaces the rear tray). PART = "arm" (print 2, mirror one in the
// slicer) or "core" (print 2: cones that centre a 25-76 mm paper core on an 8 mm rod).
// The rod rests in the arm hooks; the roll unwinds from underneath into the input rollers.
// Rolls up to 220 mm wide and 90 mm diameter. Thread the paper, then print with --paper roll.
include <../fj.scad>
PART = "arm";
roll_y = plate_y0 - 60; roll_z = 30;
module arm() {
    difference() {
        union() {
            translate([0, plate_y0 - 2, -10]) cube([plate_t + 6, 24, 32]);
            hull() {
                translate([plate_t, plate_y0, 4]) cube([6, 10, 14]);
                translate([plate_t, roll_y, roll_z]) rotate([0,90,0]) cylinder(d=18, h=6);
            }
        }
        translate([-1, plate_y0, -11]) cube([plate_t + 0.3, 30, 40]);
        for (z=[-6, 16]) translate([plate_t/2, plate_y0 + 10, z]) rotate([0,90,0]) cylinder(d=m3, h=40, center=true);
        // open hook for the rod
        translate([plate_t - 1, roll_y, roll_z]) rotate([0,90,0]) cylinder(d=rod_d + 1, h=10);
        translate([plate_t - 1, roll_y - (rod_d + 1)/2, roll_z]) cube([10, rod_d + 1, 20]);
    }
}
module core() {
    difference() {
        union() { cylinder(d1=78, d2=24, h=26); cylinder(d=40, h=34); }
        translate([0,0,-1]) cylinder(d=rod_d + 0.4, h=40);
        translate([0,0,30]) rotate([0,90,0]) cylinder(d=2.7, h=30);
    }
}
if (PART == "arm") arm(); else core();
