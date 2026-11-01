# 3. Electronics

```
 12 V 5 A brick
      │
 [polyfuse 3 A]──┬─[1N5822 to GND: blows the fuse if the plug is reversed]
      │          │
      ├──────────┼──► TMC2209 #1 VM (carriage)   ──► NEMA17 X
      │          ├──► TMC2209 #2 VM (paper feed) ──► NEMA17 Y
      │          ├──► MP1584 buck → 5 V ──► Pico 2 VSYS (via 1N5819), head-board logic
      │          └──► IRF9540N head switch (soft start) ──► VHD ──┐
      │                                                           │ 16-way ribbon
 USB ─┴── Raspberry Pi Pico 2 ── GPIO ── shift-register signals ──┴──► printhead board ──► HP45
            │   │   │
            │   │   └─ ADC: TSR (cartridge present / temperature), VHD voltage
            │   └───── home switch (service station), paper lever switch, button, LED
            └───────── STEP/DIR/EN to both TMC2209
```

The **main board** is hand-wired on a 90 × 70 mm perfboard from modules
(Pico 2, two StepSticks, a buck converter) and sits in the electronics tray
under the platen. The **printhead board** is a small PCB on the carriage;
it is described in [`hardware/head-board/README.md`](../hardware/head-board/README.md).

## Pico 2 pin map

Same as [`firmware/src/config.h`](../firmware/src/config.h).

| GPIO | Signal | Connects to |
|---|---|---|
| GP0 / GP1 | UART0 TX / RX | debug console (115200 baud), optional |
| GP2 | X_STEP | TMC2209 #1 STEP |
| GP3 | X_DIR | TMC2209 #1 DIR |
| GP4 | Y_STEP | TMC2209 #2 STEP |
| GP5 | Y_DIR | TMC2209 #2 DIR |
| GP6 | MOTOR_EN_N | both TMC2209 EN (low = on), 10 kΩ pull-up to 3V3 |
| GP7 | X_HOME_N | home microswitch (service station) to GND, 100 nF to GND |
| GP8 | PAPER_N | paper lever switch to GND (closed = paper), 100 nF to GND |
| GP9 | BUTTON_N | front button to GND |
| GP10 | HEAD_PWR | 2.2 kΩ → 2N3904 base (head supply switch) |
| GP11 | LED | 330 Ω → front LED → GND |
| GP12 | H_CLR_N | ribbon 15 (via 47 Ω) |
| GP13 | A_SER | ribbon 13 (via 47 Ω) |
| GP14 | A_SRCLK | ribbon 12 (via 47 Ω) |
| GP15 | A_RCLK | ribbon 14 (via 47 Ω) |
| GP16 | P_SER | ribbon 9 (via 47 Ω) |
| GP17 | P_SRCLK | ribbon 7 (via 47 Ω) |
| GP18 | P_RCLK | ribbon 10 (via 47 Ω) |
| GP19 | FIRE | ribbon 11 (via 47 Ω) |
| GP26 / ADC0 | TSR | ribbon 16; 1 kΩ pull-up to 3V3; 100 nF to GND |
| GP27 / ADC1 | VHD sense | 100 kΩ from VHD, 15 kΩ to GND, 100 nF to GND |

The 47 Ω series resistors damp ringing on the ribbon. The Pico's 3.3 V
outputs drive the 74**HCT** chips on the head board directly (HCT inputs
switch at 2 V even though they run at 5 V).

## Stepper drivers

* TMC2209 StepSticks in standalone mode: tie **MS1 and MS2 to 3.3 V** (1/16
  microstep, interpolated to 1/256 internally, silent StealthChop).
  `PDN_UART` unconnected.
* VIO = Pico 3V3, VM = 12 V with a 100 µF capacitor right at each driver.
* Motor current via the trim pot (Vref): carriage ~0.6 A RMS
  (Vref ≈ 0.85 V on most TMC2209 boards), paper feed ~0.7 A. Follow your
  board's formula. Too much current only makes heat; too little skips steps.
* A4988 boards also work: set MS1–MS3 high for 1/16.

## Head supply switch (VHD)

```
 +12 V ──┬───────────────┐
         │             S │
       47 kΩ   220 nF  IRF9540N (P-ch)
         │      │      G │      D ──┬── VHD ──► ribbon 1, 2
         ├──────┴────────┘          ├── 1000 µF 25 V to GND
        10 kΩ                       └── 4.7 kΩ bleeder to GND
         │
     C 2N3904  B ── 2.2 kΩ ── GP10
         E
         │
        GND
```

GP10 high → the NPN pulls the gate down → VHD on. The 220 nF gate capacitor
makes it ramp up over ~2 ms so charging the head board's 940 µF doesn't
brown out the brick. The firmware only switches VHD on inside a job (after
it has checked the cartridge) and switches it off at the end of every job,
on errors and on abort. At boot GP10 is driven low before anything else.

## Power

* Input: 12 V brick → 3 A polyfuse → 1N5822 from 12 V to GND (cathode to
  +12 V): if someone plugs in a reversed supply, the diode conducts and the
  fuse trips. Add an SMBJ15A TVS if you like.
* 5 V: MP1584 module, **set it to 5.0 V before connecting anything**. It
  feeds the head board logic and the Pico's VSYS through a 1N5819 (the Pico
  datasheet's recommended way to combine USB and external power).
* Grounds: run a thick GND wire from the brick to the drivers and to the
  ribbon's three GND wires. The head board's pulse current returns there.

## Switches, button, LED

* Home switch: KW11 microswitch in the service station pocket, NO contact
  to GND. Pressed (= carriage home) reads low.
* Paper switch: KW11-3Z with lever on the sensor bracket, NO contact to GND.
  Paper present presses the lever → low.
* Button: front panel, to GND.
  * idle, sheet inside → ejects it
  * idle, no sheet → cleans the printhead (300 spits)
  * waiting for paper → retry grabbing; roll mode → "I've cut the page"
  * after an error, hold 1.5 s → clear the error
* LED: on = ready, fast blink = busy/printing, slow blink = error.

## Connectors (suggested)

| Connector | Type | Pins |
|---|---|---|
| X motor, Y motor | JST-XH 4 | A+, A−, B+, B− (check your motor's pairs with a meter) |
| Home, paper, button | JST-XH 2 | signal, GND |
| Printhead | 2×8 box header | see the head board pin-out (pin 1 = VHD) |
| Power | 5.5 × 2.1 mm jack | centre positive |
| USB | the Pico's own micro-USB / USB-C | |

## Bring-up order (do this before inserting a cartridge)

1. Power the main board without the Pico and without the ribbon. Check
   12 V, 5 V (MP1584 adjusted) and that VHD is **0 V**.
2. Plug in the Pico over USB only, flash the firmware, run `freejet status`.
   Without a cartridge it must report no `head` flag.
3. Connect 12 V and the motors. `freejet home` → the carriage must move left
   and stop on the home switch. Check `freejet feed 20` moves paper forward.
4. Connect the head board **without a cartridge**. With a scope on `FIRE`
   and on a primitive output, run `freejet fire -1 --count 50` (it refuses
   without a cartridge: for this test temporarily put a 330 Ω resistor from
   the TSR pad to a GND pad, and set `tsr_min/tsr_max` around its reading).
   Check: each primitive pulse ≈ 1.8 µs, never longer than the one-shot
   (~3 µs) even if you hold `FIRE` high by hand, and addresses step A1…A22.
5. Remove the test resistor, insert the cartridge, `freejet status` should
   show `head`. Print `freejet test nozzles` on a sheet.
