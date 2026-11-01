// Carriage: holds the HP45, the printhead board and three LM8UU bearings.
// Print upright as modelled (bottom face on the bed), PETG, 4 walls, 40 % infill, supports OFF.
// The cartridge drops in from the top; the M3 thumbscrew in the front wall pushes it
// back against the printhead board's contact pads.
include <../fj.scad>

back_y  = -nz_back;                       // cartridge contact face
front_y = -nz_back + cart_d;              // cartridge front face
wall_front = front_y + 9;
rear_y  = back_y - pcb_t - pcb_back - 4;  // back of the board pocket wall
hx      = carr_w/2;

module bearing_saddle(l) {   // LM8UU seat open towards -Y, held by two zip ties
    difference() {
        rotate([0,90,0]) cylinder(d=lm8uu_d+7, h=l, center=true);
        rotate([0,90,0]) cylinder(d=lm8uu_d+0.3, h=l+1, center=true);
        translate([0, -12, 0]) cube([l+1, 24, lm8uu_d-3], center=true);            // opening
    }
}
module ziptie_channel() {    // 4.5 mm wide ring around a bearing seat, cut through everything
    rotate([0,90,0]) difference() { cylinder(d=lm8uu_d+11, h=4.5, center=true); cylinder(d=lm8uu_d+5, h=5, center=true); }
}
bearings = [[-13.5, rail_hi_z], [13.5, rail_hi_z], [0, rail_lo_z]];

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
        // cartridge pocket
        translate([-cart_w/2 - 0.3, back_y, -1]) cube([cart_w + 0.6, cart_d + 0.6, 100]);
        // board pocket: PCB face flush with the pocket's back face, room for parts behind it
        translate([-pcb_w/2 - 0.3, back_y - pcb_t - 0.1, carr_z0 - 1]) cube([pcb_w + 0.6, pcb_t + 0.2, 100]);
        translate([-pcb_w/2 + 4, back_y - pcb_t - pcb_back, carr_z0 - 1]) cube([pcb_w - 8, pcb_back, 100]);
        // ribbon cable exit through the top
        translate([-12, back_y - pcb_t - pcb_back - 1, carr_z1 - 12]) cube([24, pcb_back + 2, 20]);
        // clamp: front wall nut trap + screw
        translate([0, wall_front + 1, carr_z0 + 22]) rotate([90,0,0]) {
            cylinder(d=m3, h=20);
            translate([0,0,4]) rotate([0,0,30]) m3_nut_trap(3.2);
        }
        translate([-8, front_y + 0.6, carr_z0 + 10]) cube([16, 3.2, 40]);   // pressure pad slot
        // bearing clearances
        for (z=[rail_lo_z, rail_hi_z]) translate([0, rail_y, z]) rotate([0,90,0])
            cylinder(d=lm8uu_d + 0.3, h=carr_w + 2, center=true);
        // rods pass under/over the belt block
        for (z=[rail_lo_z, rail_hi_z]) translate([0, rail_y, z]) rotate([0,90,0])
            cylinder(d=rod_d + 3, h=200, center=true);
        // belt: run straight through, ends wrap into toothed slots
        translate([0, belt_front_y, belt_z]) cube([200, 2.2, 6.6], center=true);
        for (s=[-1,1]) translate([s*(hx - 7), belt_front_y - 3.5, belt_z]) cube([3, 4, 30], center=true);  // belt end loops + zip tie
        // lighten the side walls
        for (s=[-1,1]) translate([s*(hx - 2.5) - 3, back_y + 8, carr_z0 + 14]) cube([6, cart_d - 16, carr_z1 - carr_z0 - 22]);
    }
    // bearings: two on the top rail, one on the bottom rail
    for (b=bearings) translate([b[0], rail_y, b[1]]) bearing_saddle(lm8uu_l + 2);
    // cartridge rest tabs (see cart_rest_z in fj.scad)
    if (cart_rest_z > 0) for (s=[-1,1])
        translate([s*(cart_w/2 + 0.3) - (s > 0 ? 0 : 0), back_y + cart_d/2, head_gap + cart_rest_z - 2])
            translate([s > 0 ? -1.2 : -0.5, -6, 0]) cube([1.7, 12, 2]);
    // board standoffs
    for (x=[-1,1], z=[0,1]) translate([x*(pcb_w/2 - 3.5), back_y - pcb_t - pcb_back, carr_z0 + 4 + z*(pcb_h - 8)])
        difference() {
            translate([-3, 0, -3]) cube([6, pcb_back, 6]);
            rotate([90,0,0]) cylinder(d=2.2, h=20, center=true);   // M2.5 self-tapping
        }
}

module carriage() difference() {
    body();
    for (b=bearings, s=[-1,1]) translate([b[0] + s*lm8uu_l/4, rail_y, b[1]]) ziptie_channel();
}
carriage();
