cmake_minimum_required(VERSION 3.13)

# Default to the Raspberry Pi Pico 2 (RP2350). The motion interrupt uses the
# RP2350's hardware floating point unit; an RP2040 Pico is NOT fast enough.
if(NOT PICO_BOARD)
  set(PICO_BOARD pico2)
endif()

include(pico_sdk_import.cmake)
project(freejet C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()

add_executable(freejet
  src/main.c
  src/job.c
  src/comm.c
  src/motion.c
  src/head.c
  src/sensors.c
  src/params.c
  src/usb_descriptors.c
  src/frame.c
  src/ring.c
  src/packbits.c
  src/compose.c
  src/hp45_map.c
)
pico_generate_pio_header(freejet ${CMAKE_CURRENT_LIST_DIR}/src/fire.pio)
target_include_directories(freejet PRIVATE src)
target_compile_options(freejet PRIVATE -Wall -Wextra -Wno-unused-parameter)
target_link_libraries(freejet
  pico_stdlib pico_multicore pico_unique_id pico_flash
  hardware_pio hardware_pwm hardware_adc hardware_flash hardware_watchdog
  tinyusb_device tinyusb_board)

# run entirely from RAM: no flash-cache jitter in the timing-critical code
pico_set_binary_type(freejet copy_to_ram)
pico_enable_stdio_uart(freejet 1)
pico_enable_stdio_usb(freejet 0)
pico_add_extra_outputs(freejet)
