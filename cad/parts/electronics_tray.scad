// Electronics tray: hangs under the platen from the two platen rods and carries the main
// board (90 x 70 mm perfboard, long side along X: Pico 2 + 2x TMC2209 + buck converter + head power switch).
// USB and the 12 V barrel jack come out at the back. Print as modelled, PETG.
include <../fj.scad>
tx0 = 150; tw = 110;          // X position / width (sits between the motors)
module electronics_tray() {
ty0 = platen_rod_y[0] - 8; ty1 = platen_rod_y[1] + 8;
tz0 = -58; tz1 = platen_rod_z + 7;
difference() {
    union() {
        // floor + walls
        difference() {
            translate([tx0, ty0, tz0]) rounded_box([tw, ty1 - ty0, tz1 - tz0 - 8], 3);
            translate([tx0 + 2, ty0 + 2, tz0 + 2]) rounded_box([tw - 4, ty1 - ty0 - 4, 60], 2);
        }
        // hangers around the rods
        for (y=platen_rod_y, x=[tx0 + 6, tx0 + tw - 14]) translate([x, y - 7, platen_rod_z - 9]) cube([8, 14, 16]);
        // board standoffs (90 x 70 perfboard, holes 2 mm in from the corners)
        for (x=[0, 86], y=[0, 66]) translate([tx0 + 12 + x, ty0 + 8 + y, tz0]) cylinder(d=6, h=8);
    }
    for (y=platen_rod_y) translate([tx0 + tw/2, y, platen_rod_z]) rotate([0,90,0]) cylinder(d=rod_d + 0.3, h=tw + 2, center=true);
    for (y=platen_rod_y) translate([tx0 + tw/2, y, platen_rod_z + 5]) cube([tw + 2, rod_d - 1.2, 8], center=true);
    for (x=[0, 86], y=[0, 66]) translate([tx0 + 12 + x, ty0 + 8 + y, tz0 + 2]) cylinder(d=2.7, h=10);
    // rear wall cut-outs: USB-C/micro-USB and 5.5x2.1 mm barrel jack
    translate([tx0 + 40, ty0 - 1, tz0 + 8]) cube([14, 5, 9]);
    translate([tx0 + 75, ty0 + 1, tz0 + 16]) rotate([90,0,0]) cylinder(d=11.5, h=5);
    // cable openings to the motors, switches and printhead ribbon
    for (x=[tx0 - 1, tx0 + tw - 3]) translate([x, ty0 + 20, tz0 + 10]) cube([4, 40, 30]);
    // vents
    for (i=[0:6]) translate([tx0 + 15 + i*12, ty0 + 25, tz0 - 1]) cube([5, 40, 4]);
}
}
electronics_tray();
