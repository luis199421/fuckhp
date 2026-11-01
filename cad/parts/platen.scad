// Platen segment - print SEG = 0, 1 and 2 (three pieces). Prints upside-down (ribs on the bed)
// for a flat, accurate paper surface. Each segment sits on the two platen rods on four
// M3x8 set screws (height/flatness adjustment from the top) and is held with zip ties.
include <../fj.scad>
SEG = 0;
seg_x = [[68, 158], [158, 258], [258, 359]];
rib_pitch = 8;

module platen(seg) {
    x0 = seg_x[seg][0]; x1 = seg_x[seg][1];
    difference() {
        union() {
            // base plate
            translate([x0, platen_y0, -4]) cube([x1 - x0, platen_y1 - platen_y0, 2.5]);
            // ribs along Y: the paper only touches their tops (Z = 0)
            for (x=[x0 + 3 : rib_pitch : x1 - 2]) translate([x, platen_y0, -2]) cube([1.6, platen_y1 - platen_y0, 2]);
            // front tear-off bar (roll paper)
            translate([x0, platen_y1 - 6, -4]) cube([x1 - x0, 6, 4]);
            // rod saddles
            for (y=platen_rod_y, x=[x0 + 10, x1 - 10]) translate([x, y, platen_rod_z])
                difference() {
                    translate([-6, -7, 0]) cube([12, 14, -platen_rod_z - 2]);
                    rotate([0,90,0]) cylinder(d=rod_d + 0.6, h=20, center=true);
                }
            // left paper guide on the first segment (kept low where the carriage passes)
            if (seg == 0) translate([paper_x0 - 2, platen_y0, -4]) cube([2, 20, 6]);
        }
        // tear-off teeth
        for (x=[x0 : 3 : x1]) translate([x, platen_y1, 0.2]) rotate([0,0,45]) cube([2.2, 2.2, 10], center=true);
        // output drive tires come up through the platen
        for (x=tire_x) translate([x - 9, out_y - 13, -10]) cube([18, 26, 20]);
        // set screws (from the top) bearing on the rods, and zip-tie slots
        for (y=platen_rod_y, x=[x0 + 10, x1 - 10]) {
            translate([x, y, -10]) cylinder(d=2.7, h=20);
            translate([x, y, -1.5]) cylinder(d=5.6, h=5);            // keep screw below the ribs
            for (s=[-1,1]) translate([x + s*8, y, platen_rod_z]) cube([3, 18, 4], center=true);
        }
        // paper sensor lever slot (first segment)
        if (seg == 0) translate([sensor_x - 2, sensor_y - 6, -10]) cube([4, 12, 20]);
        // ink overspray window: printing past the paper edge lands in this slot, not on the ribs
        // (borderless-ish printing; stick a strip of felt underneath)
    }
}
platen(SEG);
