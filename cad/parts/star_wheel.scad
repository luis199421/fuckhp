// Star wheel for the output shaft (print 6, PETG, 0.12 mm layers). The points touch the
// freshly printed side of the paper, so they must be thin and sharp.
include <../fj.scad>
points = 18;
module star_wheel() difference() {
    union() {
        linear_extrude(1.2) polygon([for (i=[0:2*points-1]) let(r = i%2 ? star_od/2 - 2.5 : star_od/2, a = i*180/points) [r*cos(a), r*sin(a)]]);
        cylinder(d=rod_d + 5, h=5);
    }
    translate([0,0,-1]) cylinder(d=rod_d + 0.6, h=10);    // free spinning on the shaft
}
star_wheel();
