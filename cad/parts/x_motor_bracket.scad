// Carriage motor bracket - bolts to the outside of the LEFT plate. NEMA17 shaft points up,
// GT2 20T pulley at belt height. Print as modelled, PETG, 50 % infill.
include <../fj.scad>
mx = -plate_t - 26;     // motor axis X (outside the left plate)
module x_motor_bracket() bracket();
module bracket() {
    difference() {
        union() {
            // flange against the plate
            translate([-plate_t - 5, belt_y - 24, belt_z - 30]) cube([5, 46, 60]);
            // motor shelf (motor hangs below it, shaft up through it)
            translate([mx - nema_body/2, belt_y - nema_body/2, belt_z - 14]) cube([nema_body + (-plate_t - 5 - (mx + nema_body/2)) + 0.01, nema_body, 5]);
            // gussets
            for (y=[belt_y - nema_body/2, belt_y + nema_body/2 - 4])
                translate([mx + nema_body/2 - 1, y, belt_z - 30]) cube([-plate_t - 5 - (mx + nema_body/2) + 1, 4, 16]);
        }
        for (p=[[belt_y-18, belt_z+24], [belt_y+16, belt_z+24], [belt_y-18, belt_z-24]])
            translate([-plate_t - 2.5, p[0], p[1]]) rotate([0,90,0]) cylinder(d=m3, h=12, center=true);
        translate([mx, belt_y, belt_z - 11.5]) nema17_holes(12, slot=6);   // slots tension the belt
    }
}
bracket();
