// FreeJet FJ-1 - shared dimensions and helpers.
// Coordinates (mm): X = carriage travel (left -> right, 0 = inner face of the left plate)
//                   Y = paper travel (paper moves toward +Y, 0 = printhead nozzle line)
//                   Z = up (0 = paper surface on the platen)
// Every part file includes this, so changing a number here moves everything.

$fn = 64;
e = 0.01;
tol = 0.25;          // clearance for printed fits

// ---- frame ----------------------------------------------------------------
inner_w   = 360;     // distance between the side plates
plate_t   = 8;
rod_d     = 8;       // all rods: 8 mm x 400 mm smooth rod
rod_len   = 400;
plate_y0  = -112;    // side plate outline in Y
plate_y1  = 88;
plate_z0  = -70;     // bottom of the feet
plate_z1  = 70;

// ---- carriage rods ------------------------------------------------------------
rail_y    = -42;
rail_lo_z = 14;
rail_hi_z = 50;
belt_y    = -60;     // axis line of the X motor pulley and idler (both vertical)
belt_z    = 32;      // height of the belt centre
belt_r    = 20*2/PI/2;          // 20T GT2 pitch radius
belt_front_y = belt_y + belt_r; // strand clamped to the carriage
belt_back_y  = belt_y - belt_r; // return strand, passes behind the carriage

// ---- paper path -------------------------------------------------------------
tire_od   = 22;      // drive and pinch roller outside diameter
in_y      = -76;     // input nip (rollers before the printhead)
out_y     = 52;      // output nip (star wheels after the printhead)
shaft_z   = -tire_od/2;
pinch_z   = tire_od/2;
star_od   = 18;
star_z    = star_od/2;
platen_rod_y = [-40, 26];
platen_rod_z = -13;
platen_y0 = -62;     // platen top surface extent
platen_y1 = 84;
sensor_y  = -54;     // paper lever switch
paper_x0  = 70;      // paper left edge (fixed guide)
paper_w   = 220;     // widest sheet
sensor_x  = paper_x0 + 14;   // paper lever switch X
tire_x    = [paper_x0+20, paper_x0+75, paper_x0+145, paper_x0+200];  // roller positions

// ---- feed drive ---------------------------------------------------------------
pulley_teeth = 76;   // printed GT2 pulleys on both roller shafts
feed_motor_y = -12;
feed_motor_z = -44;  // 400 mm closed GT2 loop around 76T + 76T + 20T

// ---- printhead / cartridge (MEASURE YOUR HP45 AND ADJUST) -----------------------
cart_w    = 24.5;    // across the carriage travel (X)
cart_d    = 50;      // front-to-back (Y)
cart_h    = 62;
nz_back   = 19;      // nozzle line distance from the contact (back) face
head_gap  = 1.2;     // nozzle plate height above the paper
pad_z0    = 3;       // contact pad footprint origin above the cartridge bottom
carr_w    = 54;      // carriage width along X
park_x    = 33;      // carriage centre X when parked (capped)

// ---- service station ------------------------------------------------------------
home_x    = 30;      // carriage centre X where the home switch trips (firmware X = 0)
sled_engage = 9;     // sled travel when parked (cap pressed on the nozzles)
cap_x     = park_x + sled_engage;   // cap centre with the sled retracted
wiper_x   = 56;
spit_x    = 62;      // firmware spit_x_um = (spit_x - home_x) * 1000

// ---- hardware -----------------------------------------------------------------
lm8uu_d = 15; lm8uu_l = 24;
b608_d = 22; b608_w = 7;
m3 = 3.2; m3_head = 6; m3_nut = 6.4;   // across flats + tolerance
m25 = 2.7;
nema_hole = 31; nema_body = 42.3; nema_boss = 22.5;

module rod_hole(l=40, d=rod_d+tol) { cylinder(d=d, h=l, center=true); }
module m3_hole(l=40) { cylinder(d=m3, h=l, center=true); }
module m3_nut_trap(h=3) { cylinder(d=m3_nut/cos(30), h=h, $fn=6); }
module rounded_box(size, r=3) {
    hull() for (x=[r, size[0]-r], y=[r, size[1]-r]) translate([x, y, 0]) cylinder(r=r, h=size[2]);
}
module nema17_holes(l=20, slot=0) {
    for (x=[-1,1], y=[-1,1]) hull() for (s=[-slot/2, slot/2])
        translate([x*nema_hole/2, y*nema_hole/2 + s, 0]) cylinder(d=m3, h=l, center=true);
    hull() for (s=[-slot/2, slot/2]) translate([0, s, 0]) cylinder(d=nema_boss+1, h=l, center=true);
}

// ---- carriage details ------------------------------------------------------------
carr_z0   = head_gap + 2.5;   // carriage walls stop above the nozzle plate
carr_z1   = 64;
pcb_w     = 44;  pcb_h = 46;  pcb_t = 1.6;   // printhead board
pcb_back  = 5;                 // component height behind the board
cart_rest_z = 18;              // height (above cartridge bottom) of the side rest tabs; 0 = none
