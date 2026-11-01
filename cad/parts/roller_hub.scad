// Roller hub: 12 needed (4 per drive shaft x2, 4 on the pinch shaft).
// Slides on an 8 mm rod, locked with an M3 set screw (or a drop of CA glue).
// Tire: print roller_tire.scad in TPU 95A, or stretch two 18x2 mm O-rings into the grooves.
include <../fj.scad>
hub_w = 14;
module roller_hub() {
    difference() {
        cylinder(d=tire_od - 3, h=hub_w);
        translate([0,0,-1]) cylinder(d=rod_d + 0.25, h=hub_w + 2);
        for (z=[hub_w*0.3, hub_w*0.7]) translate([0,0,z]) rotate_extrude() translate([(tire_od-3)/2, 0]) circle(d=2.0);
        translate([0,0,hub_w/2]) rotate([0,90,0]) cylinder(d=2.7, h=20);               // set screw (self-tapping M3)
    }
}
roller_hub();
