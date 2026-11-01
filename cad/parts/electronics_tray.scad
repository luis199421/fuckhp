// Electronics tray: bolts under the platen beam (4x M3x12 + nuts through two webs) and carries the main
// board (90 x 70 mm perfboard, long side along X: Pico 2 + 2x TMC2209 + buck converter + head power switch).
// USB and the 12 V barrel jack come out at the back. Print as modelled, PETG.
include <../fj.scad>
tx0 = etray_x0; tw = 110;     // X position / width (sits between the motors)
module electronics_tray() {
tray_x = etray_bolts;                     // match the holes in the platen webs
ty0 = web_y[0] - 8; ty1 = web_y[2] + 12;
tz0 = -58; tz1 = web_z0;
difference() {
    union() {
        // floor + walls
        difference() {
            translate([tx0, ty0, tz0]) rounded_box([tw, ty1 - ty0, tz1 - tz0 - 2], 3);
            translate([tx0 + 2, ty0 + 2, tz0 + 2]) rounded_box([tw - 4, ty1 - ty0 - 4, 60], 2);
        }
        // tabs that bolt to the back face of web -40 and the front face of web 22
        for (x=tray_x) {
            translate([x - 6, ty0, tz1 - 14]) cube([12, web_y[0] - web_t/2 - ty0, 24]);
            translate([x - 6, web_y[2] + web_t/2, tz1 - 14]) cube([12, ty1 - web_y[2] - web_t/2, 24]);
        }
        // board standoffs (90 x 70 perfboard, holes 2 mm in from the corners)
        for (x=[0, 86], y=[0, 66]) translate([tx0 + 12 + x, ty0 + 8 + y, tz0]) cylinder(d=6, h=8);
    }
    for (x=tray_x, y=[web_y[0], web_y[2]]) translate([x, y, -13]) rotate([90,0,0]) cylinder(d=m3, h=30, center=true);
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
