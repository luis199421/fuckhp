// Roll paper: the spindle drops into the keyhole slots in the side plates (no holder arms).
// PART = "core" (print 2: cones that centre a 25-76 mm paper core on the spindle) and
// "spindle" (print spindle_pieces of it, upright, 100 % infill: they plug together and are
// pinned with M3x16 + nuts). Rolls up to 220 mm wide and 90 mm diameter.
// Thread the paper under the leaf bar onto the roller, then print with --paper roll.
include <../fj.scad>
PART = "core";
sp_d = spindle_d;
spindle_len = inner_w + 2 * plate_t + 2 * 8;          // through both keyholes + a collar each side
spindle_pieces = ceil(spindle_len / 150);
sp_half = spindle_len / spindle_pieces;               // length of one piece
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
if (PART == "core") core(); else spindle_half();
