// TPU tire for roller_hub.scad (print 4, TPU 95A, 100 % infill). Stretch over the hub.
include <../fj.scad>
difference() {
    cylinder(d=tire_od, h=12);
    translate([0,0,-1]) cylinder(d=tire_od - 3 - 0.6, h=14);
}
