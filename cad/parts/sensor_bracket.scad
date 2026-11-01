// Paper sensor holder: snaps onto the rear platen rod and holds a lever microswitch
// (KW11-3Z with a ~28 mm lever, 2x M2 holes 9.5 mm apart) so the lever tip pokes
// ~1.5 mm up through the slot in the first platen segment. Paper pushes it down.
include <../fj.scad>
module sensor_bracket() {
z0 = platen_rod_z - 22;
difference() {
    union() {
        translate([sensor_x - 8, platen_rod_y[0] - 7, z0]) cube([16, 14, platen_rod_z + 6 - z0]);
        translate([sensor_x - 3, sensor_y - 2, z0]) cube([6, platen_rod_y[0] - sensor_y + 2, 6]);
        translate([sensor_x - 3, sensor_y - 2, z0]) cube([6, 6, 18]);
    }
    translate([sensor_x, platen_rod_y[0], platen_rod_z]) rotate([0,90,0]) cylinder(d=rod_d + 0.3, h=40, center=true);
    translate([sensor_x, platen_rod_y[0], platen_rod_z + 6]) cube([20, rod_d - 1.2, 8], center=true);  // snap opening
    for (z=[-4.75, 4.75]) translate([sensor_x, sensor_y + 1, z0 + 12 + z]) rotate([0,90,0]) cylinder(d=2.2, h=10, center=true);
}
}
sensor_bracket();
