// Platen beam - print SEG = 0 .. platen_segs-1 (3 for the 1-cartridge printer). Print upside-down (ribs on the bed): the paper
// surface comes out as flat as your bed.
// The segments bolt together (3x M3x16 + nuts per joint) and the outer ones bolt to
// the side plates through vertical slots (head-gap adjustment +-1.5 mm). The assembled beam
// replaces the old steel platen rods and stiffens the frame against racking.
include <../fj.scad>
SEG = 0;
rib_pitch = 8;
joint_y = [-30, 0, 78];               // joint bolts

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
    x0 = platen_seg_x(seg)[0]; x1 = platen_seg_x(seg)[1];
    xs = seg == 0 ? paper_x0 - 2 : x0;      // segment 0's paper surface starts after the service station
    last = seg == platen_segs - 1;
    difference() {
        union() {
            // paper surface: base plate + ribs along Y (paper touches only the rib tops, Z = 0)
            translate([xs, platen_y0, -4]) cube([x1 - xs, platen_y1 - platen_y0, 2.5]);
            for (x=[xs + 3 : rib_pitch : x1 - 2]) translate([x, platen_y0, -2]) cube([1.6, platen_y1 - platen_y0, 2]);
            translate([xs, platen_y1 - 6, -4]) cube([x1 - xs, 6, 4]);              // tear-off bar (roll paper)
            // webs along X (the beam). The outer two run all the way to the plates.
            for (y=web_y) {
                wx0 = (y == flange_y[0] || y == flange_y[1]) ? x0 : max(xs, paper_x0 + 4);
                translate([wx0, y - web_t/2, web_z0]) cube([x1 - wx0, web_t, -web_z0 - 1.5]);
            }
            // cross ribs: at both ends and in the middle
            if (seg != 0) joint_rib(x0, 1);
            if (!last) joint_rib(x1, -1);
            if (seg == 0 && paper_x0 + 4 < x1 - 8) joint_rib(paper_x0 + 4, 1);
            if (seg != 0) joint_rib((x0 + x1) / 2 - 2, 1);
            if (seg == 0) flange(0, 1);
            // segment 0 of a wide printer has no paper surface: tie its two webs together at the
            // plate end (below the carriage, left of the cap sled's post)
            if (seg == 0 && xs >= x1) translate([0, web_y[0] - web_t/2, -4]) cube([5, web_y[3] - web_y[0] + web_t, 2.5]);
            if (last) flange(inner_w, -1);
            // left paper guide (low, the carriage passes over it)
            if (paper_x0 - 2 >= x0 && paper_x0 < x1) translate([paper_x0 - 2, platen_y0, -4]) cube([2, 20, 6]);
        }
        // tear-off teeth
        for (x=[xs : 3 : x1]) translate([x, platen_y1, 0.2]) rotate([0,0,45]) cube([2.2, 2.2, 10], center=true);
        // output drive tires come up through the platen
        for (x=tire_x) translate([x - 9, out_y - 13, -10]) cube([18, 26, 20]);
        // paper sensor lever slot + bracket bolts (segment 0)
        translate([sensor_x - 2, sensor_y - 6, -10]) cube([4, 12, 20]);
        for (x=[sensor_x - 6, sensor_x + 6]) translate([x, web_y[0], -13]) rotate([90,0,0]) cylinder(d=m3, h=20, center=true);
        // electronics tray bolts
        for (x=etray_bolts, y=[web_y[0], web_y[2]]) if (x > x0 + 6 && x < x1 - 6)
            translate([x, y, -13]) rotate([90,0,0]) cylinder(d=m3, h=20, center=true);
    }
}
for (x=etray_bolts) for (s=[0:platen_segs-1]) if (abs(x - platen_seg_x(s)[0]) < 8)
    echo(str("WARNING: electronics tray bolt at X=", x, " is on a platen joint"));
platen(SEG);
