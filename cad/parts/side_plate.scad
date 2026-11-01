// Side plate - print one with RIGHT=false and one with RIGHT=true.
// Prints flat (8 mm), PETG, 4 walls, 40 % infill. Rods are located by 8 mm
// shaft collars on the outside of the plates.
include <../fj.scad>
RIGHT = false;

module plate2d() {
    hull() {
        translate([plate_y0+6, plate_z0+6]) circle(6);
        translate([plate_y1-6, plate_z0+6]) circle(6);
        translate([plate_y1-6, 30]) circle(6);
        translate([rail_y+18, plate_z1-6]) circle(6);
        translate([plate_y0+6, plate_z1-6]) circle(6);
    }
}

module side_plate(right=false) {
    inner = right ? 0 : plate_t;          // local X of the face that looks into the printer
    difference() {
        rotate([90,0,90]) linear_extrude(plate_t) plate2d();
        // fixed rods: carriage rails and platen rods
        for (p=[[rail_y, rail_lo_z], [rail_y, rail_hi_z], [platen_rod_y[0], platen_rod_z],
                [platen_rod_y[1], platen_rod_z]])
            translate([0, p[0], p[1]]) rotate([0,90,0]) rod_hole(40, rod_d+0.2);
        // 608 bearings for the two drive shafts, pocket opens to the inside
        for (y=[in_y, out_y]) translate([0, y, shaft_z]) rotate([0,90,0]) {
            cylinder(d=12, h=40, center=true);
            translate([0,0, right ? -inner - 1 : -inner]) cylinder(d=b608_d+0.15, h=b608_w+1);
        }
        // vertical slots: pinch shaft (input) and star-wheel shaft (output) can lift for the paper
        for (p=[[in_y, pinch_z], [out_y, star_z]]) translate([0, p[0], p[1]]) rotate([0,90,0])
            hull() for (dz=[-1, 7]) translate([-dz, 0, 0]) cylinder(d=rod_d+1, h=40, center=true);
        // spring anchors: an M3 screw on the outside, spring hooks over the shaft end
        translate([0, in_y - 16, pinch_z - 6]) rotate([0,90,0]) cylinder(d=2.8, h=40, center=true);
        // carriage belt window
        translate([0, belt_y, belt_z]) cube([40, 18, 26], center=true);
        // X motor (left) / X idler (right) bracket screws
        for (p=[[belt_y-18, belt_z+24], [belt_y+16, belt_z+24], [belt_y-18, belt_z-24]])
            translate([0, p[0], p[1]]) rotate([0,90,0]) cylinder(d=2.8, h=40, center=true);
        if (!right) {
            // endstop block and service station
            for (z=[belt_z-7, belt_z+7]) translate([0, rail_y+17, z]) rotate([0,90,0]) cylinder(d=2.8, h=40, center=true);
            for (y=[-18, 18]) translate([0, y, -24]) rotate([0,90,0]) cylinder(d=2.8, h=40, center=true);
        } else {
            // feed motor sits inside the frame, shaft through the plate; slots tension the belt
            translate([0, feed_motor_y, feed_motor_z]) rotate([0,90,0]) rotate([0,0,90]) nema17_holes(40, slot=6);
        }
        // paper tray / cutter rail brackets
        for (p=[[plate_y0+10, -6], [plate_y0+10, 16], [plate_y1-10, 20], [plate_y1-10, -2]])
            translate([0, p[0], p[1]]) rotate([0,90,0]) cylinder(d=2.8, h=40, center=true);
        // label on the outside
        translate([right ? plate_t - 0.6 : 0.6, -92, 46]) rotate([90,0,right ? 90 : -90])
            linear_extrude(1) text(right ? "FJ-1 R" : "FJ-1 L", size=7, halign="center");
    }
}

side_plate(RIGHT);
