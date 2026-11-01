# 4. Assembly

![assembly animation](img/assembly_animation.gif)

Coordinates: **X** = left–right (carriage travel), **Y** = paper travel
(rear → front), **Z** = up. "Inner face" = the side of a plate that faces the
other plate. Tools: 2.5/1.5 mm hex keys, pliers, tin snips (for the spring
steel), a soldering iron, a multimeter.

The printer goes together as a few modules, Openprinter-style: the carriage
axis (rails + carriage), the paper feed (roller shaft + pulley + motor), the
leaf bar, the service station and the electronics tray. Each can come out
again without taking the frame apart.

## 1. Frame + carriage axis

1. Press a 608 bearing into the roller pocket of each side plate (opens on
   the inner face).
2. Press the three LM8UU into the carriage's housings (two on top, one below)
   and snug each clamp screw (M3x16 + nut). The bearings must still slide freely.
3. Slide the two **carriage rails** through the left plate, the carriage and
   the right plate.
4. Bolt the **platen segments** together (3× M3x16 + nuts per joint) and bolt
   the beam's end flanges to the plates (finger-tight for now). The beam sets
   the 360 mm plate spacing and squares the frame.
5. Printed **collars** on the rail ends, outside the plates.

## 2. Paper feed (one roller)

1. Slide the four hubs onto the 8 mm roller shaft at the tire positions
   (X = 90, 145, 215, 270 mm from the left plate's inner face), stretch a TPU
   tire over each, lock with M3x8 set screws.
2. Push the shaft through both 608 bearings, 20 mm sticking out on the right,
   collar both ends, fit the **60T** pulley on the right end.
3. Feed motor on the **inside** of the right plate (shaft through the slotted
   hole, below and behind the roller), 20T pulley outside, **200 mm** loop on
   both pulleys, slide the motor along its slots to tension, tighten.

## 3. Leaf springs

1. Cut four 52 mm pieces of 0.3 mm spring-steel strip (feeler-gauge stock).
   File the ends smooth, round the corners.
2. Join the two **leaf bar** halves (2× M3x16 + nuts at the splice) and bolt
   the bar ends to the inner faces of the plates (2× M3 per side). The bar sits
   above the paper entry; paper slides in underneath it.
3. Lay a leaf on each tilted ledge, pointing forward over the roller, and
   clamp it with a **leaf clamp** and an M3x10 into the nut under the ledge.
   Each leaf tip should rest on its tire with light pressure (~0.4 N: a sheet
   pulled out by hand drags noticeably). Bend a leaf slightly to adjust.

## 4. Platen and paper sensor

1. Screw a KW11-3Z switch to the **sensor bracket** and bolt it to the front
   of the platen's rear web (2× M3x12 + nuts). The lever pokes ~1.5 mm up
   through the slot just in front of the roller. A sheet pushed in must press
   it down before it reaches the roller.

## 5. Carriage drive

1. **X motor bracket** on the outside of the left plate (motor under the
   shelf, shaft up). **X idler bracket** on the outside of the right plate
   (idler on an M5x30).
2. GT2 belt through the plate windows: push each end into the carriage's
   toothed slot from its own side; the rear strand runs free. Tension with the
   motor slots.

## 6. Service station

1. Press the TPU **cap(s)** into the sled, lip up (one per cartridge).
2. KW11 home switch into the pocket under the sled channel.
3. Sled into its channel, small spring from the sled hook to the base hook.
4. TPU **wiper** in its slot, ~0.5 mm above the nozzle plate height.
5. Screw the station to the left plate's inner face (2× M3).

## 7. Electronics

1. Build the main board (`03-electronics.md`). **Adjust the 5 V, 9 V and 16 V
   modules first**, set the TMC2209 currents.
2. Bolt it into the electronics tray and the tray under the platen beam
   (4× M3x12 + nuts through the webs).
3. Wire motors, home switch, paper switch, button, LED.
4. **Contact flex:** screw the salvaged flex (with its foam/spring backing)
   into the recess at the back of each cartridge pocket (2× M2.5), contacts
   facing forward. Route its flat cable up out of the carriage and in a loop to a
   strain relief on the left plate, then down to the main board. It must not touch
   the rails at either end of travel. Identify the signals as described in
   `03-electronics.md` before connecting it.

## 8. Trays and roll

* Sheet tray: tray brackets on the plates' rear holes, tray pieces on top,
  fixed edge on the left.
* Roll: roll on the printed spindle between the two cones, spindle into the
  keyhole slots at the top of the plates. Thread the paper down onto the tray,
  under the leaf bar, until it rests against the roller.

## 9. Cartridges

1. Remove the tape from the nozzles. Don't touch the nozzle plate or the contacts.
2. Black cartridge in the left pocket, colour in the right one (black + colour
   build). Put the pressure pad in front and tighten the thumbscrew until the
   cartridge sits firmly against the contact flex.
3. Check the gap: 12 sheets of 80 g/m² paper (≈ 1.2 mm) should just slide
   between the nozzle plate and the platen ribs. Adjust with the platen beam's
   slotted end flanges.

Then continue with [the bring-up and calibration](08-calibration.md).
