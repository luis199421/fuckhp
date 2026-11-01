// Side plate - print one with RIGHT=false and one with RIGHT=true.
// Prints flat (8 mm), PETG, 4 walls, 40 % infill. The rails are located by printed collars
// on the outside; the platen beam bolts on inside; the paper roll's spindle drops into the
// keyhole slot at the top of the rear ear (no separate roll holder).
include <../fj.scad>
RIGHT = false;

module plate2d() {
    hull() {
        translate([plate_y0 + 14, plate_z0 + 6]) circle(6);
        translate([plate_y1 - 6, plate_z0 + 6]) circle(6);
        translate([plate_y1 - 6, 24]) circle(6);
        translate([rail_y + 18, plate_z1 - 6]) circle(6);
        translate([roll_y, roll_z]) circle(12);                 // roll-holder ear
        translate([plate_y0 + 6, plate_z0 + 30]) circle(6);
    }
}

module side_plate(right=false) {
    inner = right ? 0 : plate_t;          // local X of the face that looks into the printer
    difference() {
        rotate([90,0,90]) linear_extrude(plate_t) plate2d();
        // carriage rails
        for (z=[rail_lo_z, rail_hi_z]) translate([0, rail_y, z]) rotate([0,90,0]) rod_hole(40, rod_d+0.2);
        // platen beam flange bolts (M3 + nut on the outside)
        for (y=flange_y, z=flange_z) translate([0, y, z]) rotate([0,90,0]) cylinder(d=m3, h=40, center=true);
        // feed roller: 608 bearing, pocket opens to the inside
        translate([0, feed_y, shaft_z]) rotate([0,90,0]) {
            cylinder(d=12, h=40, center=true);
            translate([0,0, right ? -inner - 1 : -inner]) cylinder(d=b608_d+0.15, h=b608_w+1);
        }
        // roll keyhole: the spindle drops in from the top
        translate([0, roll_y, roll_z]) rotate([0,90,0]) cylinder(d=spindle_d + 0.8, h=40, center=true);
        translate([-1, roll_y - (spindle_d + 0.8)/2, roll_z]) cube([plate_t + 2, spindle_d + 0.8, 30]);
        // carriage belt window
        translate([0, belt_y, belt_z]) cube([40, 18, 26], center=true);
        // X motor (left) / X idler (right) bracket screws
        for (p=[[belt_y-18, belt_z+24], [belt_y+16, belt_z+24], [belt_y-18, belt_z-24]])
            translate([0, p[0], p[1]]) rotate([0,90,0]) cylinder(d=2.8, h=40, center=true);
        if (!right) {
            for (y=[-10, 18]) translate([0, y, -24]) rotate([0,90,0]) cylinder(d=2.8, h=40, center=true);  // service station
        } else {
            // feed motor inside the frame, shaft through the plate; slotted along the belt to tension it
            translate([0, feed_motor_y, feed_motor_z]) rotate([0,90,0])
                rotate([0,0,-atan2(feed_dir[1], feed_dir[0])]) nema17_holes(40, slot=6);
        }
        // leaf-spring bar ends
        for (y=[leaf_bar_y - 5, leaf_bar_y + 5]) translate([0, y, leaf_bar_z + 6]) rotate([0,90,0]) cylinder(d=2.8, h=40, center=true);
        // paper tray brackets
        for (p=[[plate_y0 + 22, -6], [plate_y0 + 22, 16]])
            translate([0, p[0], p[1]]) rotate([0,90,0]) cylinder(d=2.8, h=40, center=true);
        // label on the outside
        translate([right ? plate_t - 0.6 : 0.6, -80, 46]) rotate([90,0,right ? 90 : -90])
            linear_extrude(1) text(right ? "FJ-2 R" : "FJ-2 L", size=7, halign="center");
    }
}

side_plate(RIGHT);
