// 76-tooth GT2 pulley for the drive shafts (print 2, PETG, 0.12 mm layers, 100 % infill).
// Pitch diameter 48.38 mm. M3 set screw + nut trap onto the 8 mm shaft.
include <../fj.scad>
teeth = pulley_teeth;
pitch_d = teeth * 2 / PI;
od = pitch_d - 0.508;       // GT2 pitch line offset (0.254 mm)
module gt2_tooth() { // simplified GT2 groove profile
    translate([0, -0.4]) union() { circle(d=1.3, $fn=16); translate([-0.65, 0]) square([1.3, 1.2]); }
}
module pulley() {
    difference() {
        union() {
            linear_extrude(8) difference() {
                circle(d=od, $fn=teeth*3);
                for (i=[0:teeth-1]) rotate(i*360/teeth) translate([od/2, 0]) rotate(90) gt2_tooth();
            }
            translate([0,0,8]) cylinder(d=od + 3, h=1.2);     // flange
            translate([0,0,-1.2]) cylinder(d=od + 3, h=1.2);  // flange
            translate([0,0,9]) cylinder(d=20, h=8);           // hub
        }
        translate([0,0,-5]) cylinder(d=rod_d + 0.2, h=40);
        translate([0,0,13]) rotate([0,90,0]) cylinder(d=m3, h=20);
        translate([6,0,13]) rotate([0,90,0]) rotate(30) cylinder(d=m3_nut/cos(30), h=2.8, $fn=6);
        translate([6+1.4, -m3_nut/2, 13]) cube([2.8, m3_nut, 10], center=false);
    }
}
module gt2_pulley_76t() pulley();
pulley();
