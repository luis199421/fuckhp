// FreeJet FJ-2 - shared dimensions and helpers.
// Coordinates (mm): X = carriage travel (left -> right, 0 = inner face of the left plate)
//                   Y = paper travel (paper moves toward +Y, 0 = black nozzle line)
//                   Z = up (0 = paper surface on the platen)
// Every part file includes this, so changing a number here moves everything.

$fn = 64;
e = 0.01;
tol = 0.25;          // clearance for printed fits

// ---- which cartridges? (HP 63 / 302 / 123 / 803 family) ---------------------------
// "K" = black only, "CMY" = tri-colour only, "KCMY" = black + tri-colour side by side.
CARTS     = "K";
N_SLOTS   = CARTS == "KCMY" ? 2 : 1;
head_pitch = 28;                      // black-to-colour cartridge spacing in the carriage
head_span = (N_SLOTS - 1) * head_pitch;
function slot_ink(i) = CARTS == "CMY" ? "C" : (i == 0 ? "K" : "C");

// ---- frame ----------------------------------------------------------------
inner_w   = 360 + 2 * head_span;     // distance between the side plates
plate_t   = 8;
rod_d     = 8;
// rods reach through both plates plus a printed collar each side; rounded up to a length
// you can buy (400 mm for one cartridge, 500 mm for black + colour, or cut them)
rod_len   = ceil((inner_w + 2 * 8 + 2 * 8 + 8) / 100) * 100;
plate_y0  = -128;    // side plate outline in Y (includes the roll-holder ear)
plate_y1  = 84;
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

// ---- paper path: ONE feed roller just behind the printhead ----------------------------
tire_od   = 22;      // feed roller outside diameter (TPU tires on printed hubs)
feed_y    = -25;     // feed roller axis: as close behind the nozzles as the carriage allows
shaft_z   = -tire_od/2;
// spring-steel leaves press the paper onto the roller (no pinch shaft). They hang from a light
// printed bar spanning the frame above the paper entry; the paper slides in under the bar.
leaf_bar_y = -70;    // bar centre line
leaf_bar_z = 3;      // underside of the bar (paper passes below)
leaf_y1   = -21;     // leaf tip, just past the top of the roller
leaf_w    = 10;      // 0.3 mm spring steel (feeler-gauge strip), cut 52 mm long
leaf_angle = 7.5;    // ledge tilt: the free leaf would end ~2 mm below the paper -> ~0.4 N
tray_y1   = -74;     // front edge of the paper tray
// platen = a printed beam of bolted segments that also braces the frame
web_y     = [-50, -8, 22, 74];   // stiffening webs under the platen (run along X)
web_t     = 4;
web_z0    = -18;                  // bottom of the webs
flange_y  = [-50, 74];            // the two outer webs bolt to the side plates
flange_z  = [-9, -16];            // M3 bolt heights in the plates (vertical slots in the flanges)
platen_y0 = -62;     // platen top surface extent (entry ramp -> tear-off edge)
platen_y1 = 84;
sensor_y  = -42;     // paper lever switch, just before the roller nip
paper_x0  = 70 + head_span;   // paper left edge (fixed guide)
paper_w   = 220;     // widest sheet
sensor_x  = paper_x0 + 14;   // paper lever switch X
tire_x    = [paper_x0+20, paper_x0+75, paper_x0+145, paper_x0+200];  // roller positions

// ---- feed drive: 20T on the motor -> 60T printed pulley on the roller, 200 mm GT2 loop ----
pulley_teeth = 60;
feed_ctr  = 58.6;                     // centre distance for a 200 mm loop with 20T/60T
feed_dir  = [-0.79, -0.62];           // motor sits below and behind the roller
feed_motor_y = feed_y + feed_ctr * feed_dir[0];
feed_motor_z = shaft_z + feed_ctr * feed_dir[1];

// ---- roll holder: keyhole slots in the side plates -------------------------------------
roll_y    = -116;    // spindle axis
roll_z    = 62;
spindle_d = 12;

// ---- cartridges (MEASURE YOURS AND ADJUST) ------------------------------------------------
cart_w    = 21;      // across the carriage travel (X)
cart_d    = 37;      // front-to-back (Y)
cart_h    = 47;
nz_back   = 12;      // nozzle line distance from the contact (back) face
head_gap  = 1.2;     // nozzle plate height above the paper
flex_w    = 22;  flex_h = 26;   // area for the contact flex (salvaged from an HP DeskJet carriage)
carr_w    = 54 + head_span;     // carriage width along X
park_x    = 33;      // black (slot 0) nozzles X when parked (capped); carriage left face at 6
function slot_x(i) = (i - (N_SLOTS - 1) / 2) * head_pitch;   // slot i vs carriage centre

// ---- service station ------------------------------------------------------------
home_x    = 30;      // slot-0 nozzle X where the home switch trips (firmware X = 0)
sled_engage = 9;     // sled travel when parked (cap pressed on the nozzles)
cap_x     = park_x + sled_engage;   // slot-0 cap centre with the sled retracted (caps at head_pitch)
wiper_x   = 56 + head_span;
spit_x    = 62 + head_span;      // firmware spit_x_um = (spit_x - home_x) * 1000

// ---- hardware -----------------------------------------------------------------
lm8uu_d = 15; lm8uu_l = 24;
b608_d = 22; b608_w = 7;
m3 = 3.2; m3_head = 6; m3_nut = 6.4;   // across flats + tolerance
m25 = 2.7;
nema_hole = 31; nema_body = 42.3; nema_boss = 22.5;

// ---- derived layout ------------------------------------------------------------------
// segment boundaries: segment 0 carries the service-station end, the rest share the width
platen_seg0_end = paper_x0 + 88 <= 160 ? paper_x0 + 88 : paper_x0 - 10;   // keep joints off the sensor
platen_rest = ceil((inner_w - platen_seg0_end) / 130);
platen_segs = 1 + platen_rest;
function platen_seg_x(s) = s == 0 ? [0, platen_seg0_end] :
    let(w = (inner_w - platen_seg0_end) / platen_rest)
    [platen_seg0_end + (s - 1) * w, s == platen_segs - 1 ? inner_w : platen_seg0_end + s * w];
// electronics tray position (bolts through the platen webs)
etray_x0  = paper_x0 + 80 + (N_SLOTS > 1 ? 15 : 0);   // keep its bolts off the platen joints
etray_bolts = [etray_x0 + 25, etray_x0 + 95];

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

// ---- printed shaft collars --------------------------------------------------------
collar_od = 20; collar_w = 8;

// ---- carriage details ------------------------------------------------------------
carr_z0   = head_gap + 2.5;   // carriage walls stop above the nozzle plate
carr_z1   = 60;
cart_rest_z = 14;              // height (above cartridge bottom) of the side rest tabs; 0 = none
