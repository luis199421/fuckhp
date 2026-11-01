# 7. Firmware

C, Raspberry Pi Pico SDK 2.x, for the **Pico 2 (RP2350)**. About 1800 lines.

## Build and flash

```bash
git clone -b 2.1.1 https://github.com/raspberrypi/pico-sdk ~/pico-sdk
(cd ~/pico-sdk && git submodule update --init lib/tinyusb)
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi
export PICO_SDK_PATH=~/pico-sdk
cmake -S firmware -B firmware/build -DCMAKE_BUILD_TYPE=Release
make -C firmware/build -j
```

Hold BOOTSEL while plugging in the Pico 2 and copy
`firmware/build/freejet.uf2` to the drive that appears (later updates:
`freejet bootsel`).

## Layout

| File | What it does |
|---|---|
| `main.c` | start-up: head supply off first, load params, start everything, watchdog |
| `job.c` | frame handling, 32-entry op queue, executor (home, load paper, passes, eject…), errors/abort |
| `comm.c`, `usb_descriptors.c`, `tusb_config.h` | TinyUSB CDC, back-pressure, frame I/O |
| `frame.c` | frame parser/encoder with CRC and re-sync (portable) |
| `ring.c`, `packbits.c` | 256 KiB pass-data ring, streaming PackBits decoder (portable) |
| `compose.c`, `hp45_map.c` | pixel columns → HP45 fire words for 1–4 cartridges, each nozzle column with its own cursor and X/Y offset (portable) |
| `head.c`, `fire.pio` | core 1 fire loop, address chain, PIO shifter for up to 4 cartridges in parallel + pulse |
| `motion.c` | 50 kHz stepper interrupt with trapezoid moves, sensor stops, column triggers |
| `sensors.c` | ADC (TSR, VHD), switches, button, LED |
| `params.c`, `params_table.h` | parameters, stored in the last flash sector |

The portable files compile on a PC: `make -C firmware/tests` builds
`fw_sim`, which the host test-suite feeds with real job streams.

## How a pass is printed

1. The swath (pass) arrives compressed into the ring buffer.
2. The executor feeds the paper to the pass's `y`, moves the carriage to the
   start (accounting for acceleration distance and the 4.05 mm nozzle-row
   offset), arms the column triggers, and tells core 1 to start.
3. The motion interrupt advances the carriage; each time it crosses the next
   1/600" column it increments a counter.
4. Core 1 has already decoded the next column for both nozzle rows (each row
   reads the data with its own cursor, ~96 columns apart) and turned it into
   22 address words. When the counter moves, it walks the address chain and,
   per address, hands up to 3 primitive masks to the PIO, which shifts them
   into the 74HCT595s and makes the 1.8 µs pulse.
5. If core 1 ever falls a full column behind, the pass is aborted with an
   "underrun" error rather than printing in the wrong place. The executor
   caps the carriage speed at 85 % of what the head can fire.

## Safety behaviour

* Head supply (VHD) is off at boot, between jobs, on any error and on abort.
* Won't power the head without a cartridge (TSR reading in range) or with
  VHD below `vhd_min_mv`.
* Pulse width is clamped to 2.4 µs in firmware; the head board's one-shot
  caps it at ~3 µs in hardware.
* Pauses between passes when the TSR shows the head heating up.
* Watchdog (2 s) reboots a hung firmware, which switches VHD off.
* Aborts a job if the computer goes silent for `job_timeout_s` mid-page.
