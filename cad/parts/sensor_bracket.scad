// Paper sensor holder: bolts to the back face of the platen's rear web (2x M3x12 + nuts)
// and holds a lever microswitch (KW11-3Z, ~28 mm lever, 2x M2 holes 9.5 mm apart) so the
// lever tip pokes ~1.5 mm up through the slot in platen segment 0. Paper pushes it down.
include <../fj.scad>
module sensor_bracket() {
    wy = web_y[0] - web_t/2;               // back face of the web
    difference() {
        union() {
            translate([sensor_x - 10, wy - 4, web_z0 + 1]) cube([20, 4, 14]);        // against the web
            translate([sensor_x - 3, sensor_y - 2, web_z0 - 12]) cube([6, wy - sensor_y + 2, 6]);
            translate([sensor_x - 3, sensor_y - 2, web_z0 - 12]) cube([6, 6, 18]);  // switch post
            translate([sensor_x - 3, wy - 6, web_z0 - 12]) cube([6, 6, 27]);
        }
        for (x=[sensor_x - 6, sensor_x + 6]) translate([x, wy, -13]) rotate([90,0,0]) cylinder(d=m3, h=20, center=true);
        for (z=[-4.75, 4.75]) translate([sensor_x, sensor_y + 1, web_z0 + z]) rotate([0,90,0]) cylinder(d=2.2, h=10, center=true);
    }
}
sensor_bracket();
