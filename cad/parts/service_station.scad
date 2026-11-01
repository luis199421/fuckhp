// Service station (left end, under the carriage park position): cap, wiper, spittoon and the
// carriage HOME switch. Screws to the inner face of the LEFT plate (2x M3).
//
//  - cap: a sled in an inclined channel. When the carriage moves left its left face meets the
//    sled's post, pushes the sled down-the-X / up-the-ramp, and the printed TPU cap
//    (PART="cap": a soft cup with a sealing lip) presses on the nozzle plate so the ink can't
//    dry. A small extension spring from the sled hook to the base hook pulls it back out.
//  - home switch: at the end of the sled's travel the sled presses a KW11 microswitch sitting
//    in the pocket under the channel. That is "X = 0" for the firmware (carriage centre 30 mm).
//  - wiper: a printed TPU blade (PART="wiper") clamped upright; the nozzle plate drags
//    across it on every trip to the park position.
//  - spittoon: a printed cup; the firmware fires every nozzle into it before each page so the
//    first lines come out clean. The baffles stop splashes. Empty/rinse it every few months.
include <../fj.scad>
PART = "base";   // "base", "sled", "cap" (TPU) or "wiper" (TPU)
ramp_a = 24;      // channel angle: 9 mm of travel lifts the cap ~4 mm
chan_len = 46;
base_top = -6;
pad_top_retracted = head_gap - sled_engage * tan(ramp_a) + 0.4;   // 0.4 mm squeeze when parked

module channel_frame() {   // origin at the cap centre (retracted), X axis along the incline
    translate([cap_x, 0, pad_top_retracted - 6]) rotate([0, ramp_a, 0]) children();
}

module base() {
    difference() {
        union() {
            translate([0, -24, -34]) cube([4, 48, 30]);                     // flange on the plate
            translate([0, -15, -30]) cube([spit_x + 9, 30, base_top + 30]); // body
            translate([wiper_x - 4, -11, base_top]) cube([8, 22, 4]);       // wiper clamp
            translate([cap_x + head_span + 20, -3, base_top]) cube([4, 6, 6]);  // spring hook post
        }
        for (y=[-18, 18]) translate([2, y, -24]) rotate([0,90,0]) cylinder(d=m3, h=10, center=true);
        // inclined sled channel (open on top)
        channel_frame() translate([-chan_len + 14, -9.5, -4]) cube([chan_len, 19, 30]);
        // home switch pocket (KW11: 20 x 6.5 x 10 mm body, lever up)
        translate([4, -3.5, base_top - 22]) cube([22, 7, 14]);
        for (x=[9.75, 19.25]) translate([x, 0, base_top - 15]) rotate([90,0,0]) cylinder(d=2, h=30, center=true);
        // wiper slot + clamp screw
        translate([wiper_x, 0, base_top + 2]) cube([1.6, 23, 12], center=true);
        translate([wiper_x + 3, 0, base_top + 2]) rotate([0,90,0]) cylinder(d=2.7, h=12, center=true);
        // spittoon cup (the firmware brings each cartridge over it in turn; baffles added below)
        translate([spit_x, 0, base_top - 16]) cylinder(d=13, h=24);
        // room for the extra caps on the sled to travel
        if (N_HEADS > 1) translate([cap_x + 8 - sled_engage - 2, -9.5, pad_top_retracted - 9])
            cube([head_span + sled_engage + 4, 19, 20]);
        // wiring channel
        translate([4, -2, -31]) cube([10, 4, 10]);
    }
}

module sled() {   // drawn in its retracted position
    // the carriage's left face is 27 mm left of slot 0's nozzles
    post_u = -(cap_x - (park_x + sled_engage - 27)) / cos(ramp_a);   // incline coord of the post face
    post_z = pad_top_retracted - 6 - post_u * sin(ramp_a);
    difference() {
        union() {
            channel_frame() translate([-12, -8.75, -3]) cube([24, 17.5, 6]);              // body
            translate([cap_x - 8, -9, pad_top_retracted - 4.5]) cube([16 + head_span, 18, 4.5]);  // cap holder
            channel_frame() translate([post_u - 4, -4, -3]) cube([-post_u - 4 + 0.01, 8, 6]); // arm
            translate([cap_x + post_u * cos(ramp_a) - 3.6, -4, post_z - 3]) cube([3.6, 8, 12 - post_z + 3]); // post
        }
        translate([cap_x - 6.5, -7.5, pad_top_retracted - 3]) cube([13, 15, 4]);         // pad recess
        translate([cap_x + head_span + 10, 0, pad_top_retracted - 2.5]) rotate([90,0,0]) cylinder(d=2.5, h=30, center=true); // spring hook
    }
}

module spit_baffles() let(x = spit_x) intersection() {
    translate([x, 0, base_top - 16]) cylinder(d=13, h=12);
    for (a=[0, 60, 120]) translate([x, 0, base_top - 10]) rotate(a) cube([14, 1, 12], center=true);
}

// TPU 85A-95A, 100 % infill: a shallow cup whose 1 mm lip seals around the nozzle plate.
module cap() difference() {
    translate([-6.4, -7.4, 0]) cube([12.8, 14.8, 3.6]);
    translate([-5.4, -6.4, 2]) cube([10.8, 12.8, 3]);
}

// TPU 95A: 0.9 mm blade. Clamp it so it stands 0.5 mm above the nozzle plate.
module wiper() union() {
    translate([-11, 0, 0]) cube([22, 0.9, 12]);
    translate([-11, -0.35, 0]) cube([22, 1.6, 5]);     // thicker clamped part
}

module service_base() union() { base(); spit_baffles(); }
module service_sled() sled();
if (PART == "base") service_base();
else if (PART == "sled") sled();
else if (PART == "cap") cap();
else wiper();
