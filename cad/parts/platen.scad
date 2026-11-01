// Platen beam - print SEG = 0, 1 and 2. Print upside-down (ribs on the bed): the paper
// surface comes out as flat as your bed.
// The three segments bolt together (3x M3x16 + nuts per joint) and the outer ones bolt to
// the side plates through vertical slots (head-gap adjustment +-1.5 mm). The assembled beam
// replaces the old steel platen rods and stiffens the frame against racking.
include <../fj.scad>
SEG = 0;
seg_x  = [[0, 158], [158, 258], [258, inner_w]];
surf_x0 = [68, 158, 258];             // segment 0's paper surface starts after the service station
rib_pitch = 8;
joint_y = [-30, 0, 78];               // joint bolts
tray_x  = [175, 245];                 // electronics tray bolts (webs -40 and 22)

module joint_rib(x, toward) {          // cross rib with bolt holes at a joint / end
    difference() {
        union() {
            translate([x - (toward > 0 ? 0 : 4), platen_y0, web_z0]) cube([4, 38 - platen_y0, -web_z0 - 1.5]);
            translate([x - (toward > 0 ? 0 : 4), 66, web_z0]) cube([4, platen_y1 - 66, -web_z0 - 1.5]);
        }
        for (y=joint_y) translate([x, y, -9]) rotate([0,90,0]) cylinder(d=m3, h=20, center=true);
    }
}

module flange(x, inward) {             // bolts to a side plate (inner face at x)
    for (y=flange_y) difference() {
        translate([x - (inward > 0 ? 0 : 5), y - 9, web_z0 - 2]) cube([5, 18, -web_z0 + 0.5]);
        for (z=flange_z) hull() for (dz=[-1.5, 1.5]) translate([x, y, z + dz]) rotate([0,90,0])
            cylinder(d=m3, h=20, center=true);
    }
}

module platen(seg) {
    x0 = seg_x[seg][0]; x1 = seg_x[seg][1]; xs = surf_x0[seg];
    difference() {
        union() {
            // paper surface: base plate + ribs along Y (paper touches only the rib tops, Z = 0)
            translate([xs, platen_y0, -4]) cube([x1 - xs, platen_y1 - platen_y0, 2.5]);
            for (x=[xs + 3 : rib_pitch : x1 - 2]) translate([x, platen_y0, -2]) cube([1.6, platen_y1 - platen_y0, 2]);
            translate([xs, platen_y1 - 6, -4]) cube([x1 - xs, 6, 4]);              // tear-off bar (roll paper)
            // webs along X (the beam). The outer two run all the way to the plates.
            for (y=web_y) {
                wx0 = (y == flange_y[0] || y == flange_y[1]) ? x0 : max(xs, 74);
                translate([wx0, y - web_t/2, web_z0]) cube([x1 - wx0, web_t, -web_z0 - 1.5]);
            }
            // cross ribs: at both ends and in the middle
            if (seg != 0) joint_rib(x0, 1);
            if (seg != 2) joint_rib(x1, -1);
            joint_rib(seg == 0 ? 74 : (x0 + x1) / 2 - 2, 1);
            if (seg == 0) flange(0, 1);
            if (seg == 2) flange(inner_w, -1);
            // left paper guide (low, the carriage passes over it)
            if (seg == 0) translate([paper_x0 - 2, platen_y0, -4]) cube([2, 20, 6]);
        }
        // tear-off teeth
        for (x=[xs : 3 : x1]) translate([x, platen_y1, 0.2]) rotate([0,0,45]) cube([2.2, 2.2, 10], center=true);
        // output drive tires come up through the platen
        for (x=tire_x) translate([x - 9, out_y - 13, -10]) cube([18, 26, 20]);
        // paper sensor lever slot + bracket bolts (segment 0)
        if (seg == 0) {
            translate([sensor_x - 2, sensor_y - 6, -10]) cube([4, 12, 20]);
            for (x=[sensor_x - 6, sensor_x + 6]) translate([x, web_y[0], -13]) rotate([90,0,0]) cylinder(d=m3, h=20, center=true);
        }
        // electronics tray bolts (segment 1)
        if (seg == 1) for (x=tray_x, y=[web_y[0], web_y[2]])
            translate([x, y, -13]) rotate([90,0,0]) cylinder(d=m3, h=20, center=true);
    }
}
platen(SEG);
