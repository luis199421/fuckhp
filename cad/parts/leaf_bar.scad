// Leaf-spring bar: spans the frame just above the paper entry and holds four spring-steel
// leaves that press the paper onto the feed roller's tires (Openprinter-style: no pinch shaft).
//   PART="bar" PIECE=0 / 1  - two halves, spliced in the middle with 2x M3x16 + nuts,
//                              ends bolt to the side plates (2x M3 each)
//   PART="clamp"            - print 4: holds a leaf on its ledge with one M3x10 + nut
// Leaves: 0.3 mm spring steel, 10 mm wide, 52 mm long (cut from a feeler-gauge strip).
// Everything stays above Z = 3 so the paper slides in underneath.
include <../fj.scad>
PART = "bar";
PIECE = 0;
bar_h = 7; bar_d = 10;
ledge_y0 = leaf_bar_y + bar_d/2;          // front face of the bar
ledge_l = 5;                               // ledge depth (stays behind the carriage's bearing lug)
half = inner_w / 2;

module ledge(x) {     // tilted seat in front of the bar, top surface drops toward the roller
    translate([x - leaf_w/2 - 2, ledge_y0 - 0.01, leaf_bar_z])
        intersection() {
            cube([leaf_w + 4, ledge_l, 6]);
            translate([0, 0, 2.5]) rotate([-leaf_angle, 0, 0]) translate([-1, -5, -20]) cube([leaf_w + 6, 20, 20]);
        }
}

module bar(xa, xb) {
    difference() {
        union() {
            translate([xa, leaf_bar_y - bar_d/2, leaf_bar_z]) cube([xb - xa, bar_d, bar_h]);
            if (xa == 0) translate([0, leaf_bar_y - 9, leaf_bar_z]) cube([4, 18, bar_h + 6]);
            if (xb == inner_w) translate([inner_w - 4, leaf_bar_y - 9, leaf_bar_z]) cube([4, 18, bar_h + 6]);
            if (xb == half) translate([half - 12, leaf_bar_y - bar_d/2 - 3, leaf_bar_z]) cube([24, 3, bar_h]);
            for (x=tire_x) if (x > xa + 8 && x < xb - 8) ledge(x);
        }
        if (xa == 0) for (y=[-5, 5]) translate([2, leaf_bar_y + y, leaf_bar_z + 9]) rotate([0,90,0]) cylinder(d=m3, h=10, center=true);
        if (xb == inner_w) for (y=[-5, 5]) translate([inner_w - 2, leaf_bar_y + y, leaf_bar_z + 9]) rotate([0,90,0]) cylinder(d=m3, h=10, center=true);
        for (x=[half - 7, half + 7]) translate([x, leaf_bar_y - bar_d/2, leaf_bar_z + bar_h/2]) rotate([90,0,0]) cylinder(d=m3, h=30, center=true);
        // ledge screw + nut trap from below
        for (x=tire_x) if (x > xa + 8 && x < xb - 8) {
            translate([x, ledge_y0 + ledge_l/2, leaf_bar_z - 1]) cylinder(d=m3, h=12);
            translate([x, ledge_y0 + ledge_l/2, leaf_bar_z - 1]) rotate(30) cylinder(d=m3_nut/cos(30), h=3.4, $fn=6);
        }
    }
}

module clamp() {
    difference() {
        cube([leaf_w + 4, ledge_l, 2.5]);
        translate([(leaf_w + 4)/2, ledge_l/2, -1]) cylinder(d=m3, h=5);
    }
}

module leaf_bar_piece(i) { if (i == 0) bar(0, half); else bar(half, inner_w); }
if (PART == "bar") leaf_bar_piece(PIECE); else clamp();
