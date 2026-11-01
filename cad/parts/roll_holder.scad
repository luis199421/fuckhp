// Optional roll-paper holder (replaces the rear tray). PART = "arm" (print 2, mirror one in the
// slicer), "core" (print 2: cones that centre a 25-76 mm paper core) and "spindle" (print
// spindle_pieces of it - 3 for the 1-cartridge printer - upright, 100 % infill: they plug
// together and are pinned with M3x16 + nuts).
// The spindle rests in the arm hooks; the roll unwinds from underneath into the input rollers.
// Rolls up to 220 mm wide and 90 mm diameter. Thread the paper, then print with --paper roll.
include <../fj.scad>
PART = "arm";
sp_d = 12;
spindle_len = inner_w + 2 * plate_t + 2 * 8 + 10;     // spans both arms
spindle_pieces = ceil(spindle_len / 150);
sp_half = spindle_len / spindle_pieces;               // length of one piece
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
        translate([plate_t - 1, roll_y, roll_z]) rotate([0,90,0]) cylinder(d=sp_d + 1, h=10);
        translate([plate_t - 1, roll_y - (sp_d + 1)/2, roll_z]) cube([10, sp_d + 1, 20]);
    }
}
module core() {
    difference() {
        union() { cylinder(d1=78, d2=24, h=26); cylinder(d=40, h=34); }
        translate([0,0,-1]) cylinder(d=sp_d + 0.4, h=40);
        translate([0,0,30]) rotate([0,90,0]) cylinder(d=2.7, h=30);
    }
}
echo(str("roll spindle: print ", spindle_pieces, " pieces of ", sp_half, " mm"));
module spindle_half() difference() {       // one piece of the 12 mm spindle; joins at the spigot
    union() { cylinder(d=sp_d, h=sp_half); translate([0,0,sp_half]) cylinder(d=6, h=8); }
    translate([0,0,-1]) cylinder(d=6.3, h=9);         // socket for the other half's spigot
    for (z=[4, sp_half + 4]) translate([0,0,z]) rotate([90,0,0]) cylinder(d=m3, h=20, center=true);  // cross pin
}
if (PART == "arm") arm(); else if (PART == "core") core(); else spindle_half();
