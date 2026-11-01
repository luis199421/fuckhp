// Pressure pad between the clamp screw and the cartridge front. Print in TPU if you have it
// (PETG works). 
include <../fj.scad>
difference() {
    cube([15.6, 3, 38]);
    translate([7.8, -1, 12]) rotate([-90,0,0]) cylinder(d=3.4, h=1.8);   // screw tip seat
}
