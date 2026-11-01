// Assembly animation. Driven by tools/render_animation.py, which sets STEP (0..N) and
// U (0..1 progress inside the step) for every frame. Parts of earlier steps sit in place,
// the current step's parts fly in, later steps are hidden. The last step runs a print.
include <fj.scad>
use <parts/side_plate.scad>
use <parts/carriage.scad>
use <parts/platen.scad>
use <parts/roller_hub.scad>
use <parts/star_wheel.scad>
use <parts/gt2_pulley_76t.scad>
use <parts/service_station.scad>
use <parts/x_motor_bracket.scad>
use <parts/x_idler_bracket.scad>
use <parts/sensor_bracket.scad>
use <parts/electronics_tray.scad>
use <parts/paper_tray.scad>
use <parts/rod_collar.scad>

STEP = 0;
U = 1;
$fn = 32;

function ease(u) = u < 0 ? 0 : u > 1 ? 1 : u * u * (3 - 2 * u);
// show children for step k; while k is the current step they travel in from `from`
module at(k, from=[0,0,150], delay=0) {
    if (STEP > k) children();
    else if (STEP == k) {
        e = ease((U - delay) / (1 - delay));
        if (U >= delay) translate(from * (1 - e)) children();
    }
}

module rod(y, z, x0=-20, l=rod_len) { color("silver") translate([x0, y, z]) rotate([0,90,0]) cylinder(d=rod_d, h=l); }
module lm8uu() color("silver") rotate([0,90,0]) cylinder(d=lm8uu_d, h=lm8uu_l, center=true);
module cartridge() color("#202020") translate([-cart_w/2, -nz_back, head_gap]) cube([cart_w, cart_d, cart_h]);
module head_board() color("ForestGreen") translate([-pcb_w/2, -nz_back - pcb_t, carr_z0]) cube([pcb_w, pcb_t, pcb_h]);
module belt_loop2d(circles, w=1.4) difference() {   // GT2 belt around pulleys (2D)
    offset(r=w/2) hull() for (c=circles) translate([c[0], c[1]]) circle(r=c[2]);
    offset(r=-w/2) hull() for (c=circles) translate([c[0], c[1]]) circle(r=c[2]);
}

// ----- the print demo (last step): load a sheet, then 6 passes, feeding 12.7 mm between them
PRINT = 14;
NPASS = 6;
demo = STEP == PRINT ? U : 0;
load = 0.15;
ph = demo < load ? 0 : (demo - load) / (1 - load) * NPASS;   // 0..NPASS
pass = min(floor(ph), NPASS - 1);
pf = ph - pass;                                              // progress inside the pass
function pass_x(p, f) = p % 2 == 0 ? 75 + 220 * ease(f) : 295 - 220 * ease(f);
carr_x = STEP < PRINT ? 180 : demo < load ? 75 : pass_x(pass, min(1, pf * 1.15));
sheet_y0 = -370;                       // sheet on the tray (leading edge at the rollers)
sheet_y1 = -272;                       // leading edge just past the nozzles
paper_y = STEP < PRINT ? sheet_y0 :
          demo < load ? sheet_y0 + (sheet_y1 - sheet_y0) * ease(demo / load) :
          sheet_y1 + 12.7 * (pass + (pf > 0.87 ? ease((pf - 0.87) / 0.13) : 0));

// 0  side plates
at(0, [-160, 0, 0]) color("SteelBlue") translate([-plate_t, 0, 0]) side_plate(false);
at(0, [160, 0, 0], 0.2) color("SteelBlue") translate([inner_w, 0, 0]) side_plate(true);

// 1  carriage + its three bearings
at(1, [0, 0, 160]) translate([carr_x, 0, 0]) color("Gold") carriage();
for (b=[[-13.5, rail_hi_z, -1], [13.5, rail_hi_z, 1], [0, rail_lo_z, 1]])
    at(1, [b[2] * 80, 0, 0], 0.4) translate([carr_x + b[0], rail_y, b[1]]) lm8uu();

// 2  carriage rails slide through plates and bearings
for (z=[rail_lo_z, rail_hi_z]) at(2, [-430, 0, 0], z == rail_hi_z ? 0.25 : 0) rod(rail_y, z);

// 3  platen beam: three segments bolt together and to the plates
for (s=[0:2]) at(3, [0, 0, 170], s * 0.25) color("Gainsboro") platen(s);

// 4  drive shafts with rollers, then the 76T pulleys
for (y=[in_y, out_y]) at(4, [440, 0, 0], y == out_y ? 0.25 : 0) {
    rod(y, shaft_z, -4);
    for (x=tire_x) color("#151515") translate([x - 7, y, shaft_z]) rotate([0,90,0]) roller_hub();
}
for (y=[in_y, out_y]) at(4, [70, 0, 0], 0.6) color("white")
    translate([inner_w + plate_t + 4, y, shaft_z]) rotate([0,90,0]) gt2_pulley_76t();

// 5  feed motor + closed belt
at(5, [0, 0, -120]) color("#333") translate([inner_w - 40, feed_motor_y - 21, feed_motor_z - 21]) cube([40, 42, 42]);
at(5, [60, 0, 0], 0.5) color("#111")
    translate([inner_w + plate_t + 8, 0, 0]) rotate([90, 0, 90]) linear_extrude(6)
        belt_loop2d([[in_y, shaft_z, 76 / PI], [out_y, shaft_z, 76 / PI], [feed_motor_y, feed_motor_z, 20 / PI]]);

// 6  pinch shaft (input) and star-wheel shaft (output)
at(6, [0, 0, 120]) { rod(in_y, pinch_z, -14);
    for (x=tire_x) color("#151515") translate([x - 7, in_y, pinch_z]) rotate([0,90,0]) roller_hub(); }
at(6, [0, 0, 120], 0.3) { rod(out_y, star_z, -14);
    for (x=tire_x) color("#151515") translate([x - 2.5, out_y, star_z]) rotate([0,90,0]) star_wheel(); }

// 7  printed collars on every rod end
for (p=[[rail_y, rail_lo_z], [rail_y, rail_hi_z], [in_y, shaft_z], [out_y, shaft_z], [in_y, pinch_z], [out_y, star_z]])
    color("SteelBlue") {
        at(7, [-60, 0, 0]) translate([-plate_t - collar_w, p[0], p[1]]) rotate([0,90,0]) rod_collar();
        at(7, [60, 0, 0]) translate([inner_w + plate_t, p[0], p[1]]) rotate([0,90,0]) rod_collar();
    }

// 8  service station: cap sled, TPU wiper, spittoon, home switch
at(8, [0, 0, 140]) color("OrangeRed") { service_base(); }
at(8, [0, 0, 140], 0.3) color("Tomato") service_sled();

// 9  carriage motor, idler and belt
at(9, [-120, 0, 0]) { color("DimGray") x_motor_bracket();
    color("#333") translate([-plate_t - 26 - 21, belt_y - 21, belt_z - 14 - 40]) cube([42, 42, 40]); }
at(9, [120, 0, 0], 0.2) color("DimGray") x_idler_bracket();
at(9, [0, 0, 80], 0.5) color("#111") translate([0, 0, belt_z - 3]) linear_extrude(6)
    belt_loop2d([[-plate_t - 26, belt_y, belt_r], [inner_w + plate_t + 20, belt_y, belt_r]]);

// 10 paper sensor + electronics tray
at(10, [0, 0, -90]) color("DimGray") sensor_bracket();
at(10, [0, 0, -140], 0.3) color("DarkSlateGray") electronics_tray();

// 11 printhead board, then the HP45 cartridge
at(11, [0, -60, 0]) translate([carr_x, 0, 0]) head_board();
at(11, [0, 0, 160], 0.35) translate([carr_x, 0, 0]) cartridge();

// 12 rear paper tray
at(12, [0, -160, 0]) color("Wheat") { paper_tray("left"); paper_tray("right"); }

// 13 (camera move only: "ready")

// 14 a sheet feeds in and the carriage prints back and forth, "text" appears under the head
if (STEP >= PRINT) color("white") translate([paper_x0, paper_y, 0.3]) cube([215.9, 279.4, 0.2]);
lens = [[180, 150, 170], [120, 175, 90], [175, 160, 140], [60, 170, 150], [175, 110, 160], [150, 175, 80]];
if (STEP >= PRINT && demo >= load)
    for (i=[0 : pass]) let(done = i < pass ? 1 : min(1, pf * 1.15))
        for (l=[0:2]) let(len = lens[i][l] * done, x0 = paper_x0 + 15,
                          xa = i % 2 == 0 ? x0 : x0 + lens[i][l] * (1 - done))
            color("#111") translate([xa, paper_y - (sheet_y1 + 12.7 * i) - 4 + l * 3.6, 0.45]) cube([len, 2, 0.1]);
