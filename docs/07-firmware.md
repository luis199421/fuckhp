# 7. Firmware

C, Raspberry Pi Pico SDK 2.x, for the **Pico 2 (RP2350)**. About 1700 lines.

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
| `compose.c` | pixel columns → nozzle data for the black and colour cartridges: five nozzle columns (black rows 0/1, C, M, Y), each with its own cursor and X offset (portable) |
| `hp302.c` | HP 63/302 nozzle bit maps and waveform generator, ported from Sprite_tm's driver (portable; checked sample-for-sample against the original in `tests/wave_test.c`) |
| `head.c`, `wave.pio` | core 1 fire loop; a 2-instruction PIO program plays the 14-line waveform at 3.33 MHz from DMA, double-buffered |
| `motion.c` | 50 kHz stepper interrupt with trapezoid moves, sensor stops, column triggers |
| `sensors.c` | ADC (16 V rail), switches, button, LED |
| `params.c`, `params_table.h` | parameters, stored in the last flash sector |

The portable files compile on a PC: `make -C firmware/tests` builds
`fw_sim`, which the host test-suite feeds with real job streams.

## How a pass is printed

1. The swath (pass) arrives compressed into the ring buffer: one PackBits
   stream per ink plane (1 for K or CMY, 4 for KCMY).
2. The executor feeds the paper to the pass's `y`, moves the carriage to the
   start (accounting for the acceleration distance, the black cartridge's
   two nozzle columns `k_row_gap_um` apart and the colour cartridge's offset
   `color_x_um`), arms the column triggers, and tells core 1 to start.
3. The motion interrupt advances the carriage; each time it crosses the next
   1/600" column it increments a counter.
4. Core 1 has already composed the next column: for every nozzle column of
   every cartridge it reads the right plane at that column's own offset
   (`fj_pass_compose`, `compose.c`) and sets the nozzle bits in two 42-byte
   nozzle-data blocks, one per cartridge. `hp302_cycle()` turns each block into
   one firing cycle (14 packets, 490 samples at 3.33 MHz, ~147 µs): black
   first, then colour, ~300 µs per column. When the counter moves, DMA plays
   the prepared buffer to the PIO while core 1 builds the next one.
5. If core 1 ever falls a full column behind, the pass is aborted with an
   "underrun" error rather than printing in the wrong place. The executor
   caps the carriage speed at 85 % of what `head_column_time_us()` allows.

## Safety behaviour

* The 16 V cartridge rail is off at boot, between jobs, on any error and on
  abort. GP5 is driven low before anything else at boot.
* Won't start a job when the job's ink set needs a cartridge that
  `cartridges` says isn't fitted, or with the 16 V rail below `vhd_min_mv`.
* The waveform templates give ~2 µs heater pulses; `wave_test` checks that
  no F pulse in the generated waveform exceeds 8 samples (2.4 µs). The
  74HCT123 one-shots cut every heater line after ~3 µs in hardware.
* Single sheets: once the paper sensor sees the sheet's tail, a pass that
  would print more than `sheet_tail_um` past it is refused (`SHEET_END`)
  instead of firing onto the platen.
* Watchdog (2 s) reboots a hung firmware, which switches the 16 V rail off.
* Aborts a job if the computer goes silent for `job_timeout_s` mid-page.
