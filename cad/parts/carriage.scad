// Carriage: holds N_HEADS HP45-format cartridges (1 black, 2 grayscale, 3-4 colour) side by side
// at head_pitch, one printhead board behind each, and three LM8UU bearings.
// Print upright as modelled (bottom face on the bed), PETG, 4 walls, 40 % infill, supports OFF.
// The LM8UU bearings press into closed housings (slide the carriage onto the rails before
// the second side plate goes on) and are clamped with one M3x16 + nut each.
// The cartridge drops in from the top; the M3 thumbscrew in the front wall pushes it
// back against the printhead board's contact pads.
include <../fj.scad>

back_y  = -nz_back;                       // cartridge contact face
front_y = -nz_back + cart_d;              // cartridge front face
wall_front = front_y + 9;
rear_y  = back_y - pcb_t - pcb_back - 4;  // back of the board pocket wall
hx      = carr_w/2;

module teardrop(d, h) {      // horizontal hole along X that prints without support
    rotate([0,90,0]) linear_extrude(h, center=true) rotate(90)
        hull() { circle(d=d); translate([d/2 * sqrt(2) / 2 * sqrt(2), 0]) square(0.01); polygon([[0, -d/2*0.707], [d/2*1.414, 0], [0, d/2*0.707]]); }
}
module bearing_housing(l) {  // closed LM8UU housing, clamped by one M3 across a slit
    difference() {
        union() {
            rotate([0,90,0]) cylinder(d=lm8uu_d + 7, h=l, center=true);
            translate([-l/2, -lm8uu_d/2 - 9, -6]) cube([l, 8, 12]);            // clamp lug at the back
        }
        teardrop(lm8uu_d + 0.1, l + 1);
        translate([0, -lm8uu_d/2 - 5, 0]) cube([l + 1, 12, 1.4], center=true);  // slit
        translate([0, -lm8uu_d/2 - 5, 0]) cylinder(d=m3, h=20, center=true);
        translate([0, -lm8uu_d/2 - 5, -6.01]) rotate(30) cylinder(d=m3_nut/cos(30), h=3, $fn=6);
    }
}
bearings = [[-(hx - 13.5), rail_hi_z], [hx - 13.5, rail_hi_z], [0, rail_lo_z]];

module body() {
    difference() {
        union() {
            // cartridge cage
            translate([-hx, rear_y, carr_z0]) cube([carr_w, wall_front - rear_y, carr_z1 - carr_z0]);
            // spine to the bearings
            translate([-hx, rail_y, carr_z0 + 6]) cube([carr_w, rear_y - rail_y + 1, rail_hi_z - carr_z0 - 6]);
            // belt clamp block
            translate([-hx, belt_back_y + 3.5, belt_z - 7]) cube([carr_w, rail_y - belt_back_y - 3.5, 14]);
        }
        for (i=[0:N_HEADS-1]) translate([slot_x(i), 0, 0]) {
            // cartridge pocket
            translate([-cart_w/2 - 0.3, back_y, -1]) cube([cart_w + 0.6, cart_d + 0.6, 100]);
            // board pocket: PCB face flush with the pocket's back face, room for parts behind it
            translate([-pcb_w/2 - 0.3, back_y - pcb_t - 0.1, carr_z0 - 1]) cube([pcb_w + 0.6, pcb_t + 0.2, 100]);
            translate([-pcb_w/2 + 4, back_y - pcb_t - pcb_back, carr_z0 - 1]) cube([pcb_w - 8, pcb_back, 100]);
            // clamp: front wall nut trap + screw
            translate([0, wall_front + 1, carr_z0 + 22]) rotate([90,0,0]) {
                cylinder(d=m3, h=20);
                translate([0,0,4]) rotate([0,0,30]) m3_nut_trap(3.2);
            }
            translate([-8, front_y + 0.6, carr_z0 + 10]) cube([16, 3.2, 40]);   // pressure pad slot
        }
        // bearing clearances
        for (z=[rail_lo_z, rail_hi_z]) translate([0, rail_y, z]) rotate([0,90,0])
            cylinder(d=lm8uu_d + 0.3, h=carr_w + 2, center=true);
        // rods pass under/over the belt block
        for (z=[rail_lo_z, rail_hi_z]) translate([0, rail_y, z]) rotate([0,90,0])
            cylinder(d=rod_d + 3, h=200, center=true);
        // belt: each end pushes into a toothed slot from its own side (no ties needed)
        translate([0, belt_front_y, belt_z]) cube([200, 1.6, 6.6], center=true);
        translate([0, belt_front_y, belt_z]) cube([8, 6, 20], center=true);   // window: check both ends are in
        // lighten the side walls
        for (s=[-1,1]) translate([s*(hx - 2.5) - 3, back_y + 8, carr_z0 + 14]) cube([6, cart_d - 16, carr_z1 - carr_z0 - 22]);
    }
    // bearings: two on the top rail, one on the bottom rail
    for (b=bearings) translate([b[0], rail_y, b[1]]) bearing_housing(lm8uu_l + 2);
    // cartridge rest tabs (see cart_rest_z in fj.scad)
    if (cart_rest_z > 0) for (i=[0:N_HEADS-1], s=[-1,1])
        translate([slot_x(i) + s*(cart_w/2 + 0.3), back_y + cart_d/2, head_gap + cart_rest_z - 2])
            translate([s > 0 ? -1.2 : -0.5, -6, 0]) cube([1.7, 12, 2]);
    // GT2 teeth (2 mm pitch) on the slot wall: the belt's teeth lock into them
    for (x=[-hx + 1 : 2 : -5], x2=[0]) translate([x, belt_front_y + 0.8, belt_z]) cylinder(d=1.0, h=6.6, center=true, $fn=12);
    for (x=[5 : 2 : hx - 1]) translate([x, belt_front_y + 0.8, belt_z]) cylinder(d=1.0, h=6.6, center=true, $fn=12);
    // board standoffs (the narrow boards stick out above the carriage; their connector is on top)
    for (i=[0:N_HEADS-1], x=[-1,1], z=[carr_z0 + 4, carr_z1 - 4])
        translate([slot_x(i) + x*(pcb_w/2 - 3.5), back_y - pcb_t - pcb_back, z])
        difference() {
            translate([-3, 0, -3]) cube([6, pcb_back, 6]);
            rotate([90,0,0]) cylinder(d=2.2, h=20, center=true);   // M2.5 self-tapping
        }
}

module carriage() body();
carriage();
