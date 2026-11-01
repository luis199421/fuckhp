// Rear paper tray (print PART="left" and PART="right"; they join with two M3 screws), plus
// PART="guide": the sliding right-hand paper guide. The tray hooks onto the rear edge of the
// side plates with the bracket PART="bracket" (print 2, mirror one in the slicer).
// Sheets slide in face-up along the fixed left edge until the rollers grab them.
include <../fj.scad>
PART = "left";
tray_y0 = plate_y0 - 70; tray_y1 = in_y - 14;      // tray in front of the input rollers
tray_z = 1.2;                                      // tray surface slightly above the paper line
half = (inner_w) / 2;

module tray(xa, xb) {
    difference() {
        union() {
            translate([xa, tray_y0, tray_z - 2]) cube([xb - xa, tray_y1 - tray_y0, 2]);
            // stiffening ribs underneath
            for (x=[xa + 10 : 40 : xb - 5]) translate([x, tray_y0, tray_z - 8]) cube([2, tray_y1 - tray_y0, 6]);
            // fixed left edge guide
            if (xa < paper_x0 && xb > paper_x0) translate([paper_x0 - 4, tray_y0, tray_z]) cube([4, tray_y1 - tray_y0 - 4, 8]);
            // join tabs
            if (xb == half) translate([xb - 10, tray_y0 + 10, tray_z - 8]) cube([10, tray_y1 - tray_y0 - 20, 4]);
        }
        // guide slot for the sliding right guide
        translate([paper_x0 + 100, tray_y0 + 15, -10]) cube([paper_w - 80, 6, 20]);
        if (xa == half) for (y=[tray_y0 + 20, tray_y1 - 20]) translate([xa + 5, y, -10]) cylinder(d=m3, h=20);
        if (xb == half) for (y=[tray_y0 + 20, tray_y1 - 20]) translate([xb - 5, y, -10]) cylinder(d=m3, h=20);
    }
}
module guide() {
    difference() {
        union() {
            cube([4, 50, 10]);
            translate([-12, 20, -2]) cube([16, 10, 2]);
            translate([-4, 22, -6]) cube([5.6, 6, 6]);     // runs in the slot
        }
        translate([-1, 25, -10]) cylinder(d=m3, h=20);
    }
}
module bracket() {    // bolts to a plate's rear edge holes, carries the tray edge
    difference() {
        union() {
            translate([0, plate_y0 - 2, -10]) cube([plate_t + 6, 24, 32]);
            translate([plate_t, tray_y0 + 10, tray_z - 10]) cube([6, plate_y0 - tray_y0 - 8, 8]);
        }
        translate([-1, plate_y0, -10]) cube([plate_t + 0.3, 30, 40]);
        for (z=[-6, 16]) translate([plate_t/2, plate_y0 + 10, z]) rotate([0,90,0]) cylinder(d=m3, h=40, center=true);
    }
}
module paper_tray(p) { if (p == "left") tray(0, half); else if (p == "right") tray(half, inner_w); else if (p == "guide") guide(); else bracket(); }
if (PART == "left") tray(0, half);
else if (PART == "right") tray(half, inner_w);
else if (PART == "guide") guide();
else bracket();
