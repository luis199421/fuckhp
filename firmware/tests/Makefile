# Host-side builds of the firmware's portable code (no Pico SDK needed).
CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -Werror -std=gnu11
COMMON = ../src/frame.c ../src/ring.c ../src/packbits.c ../src/compose.c ../src/hp302.c

all: fw_sim wave_test

fw_sim: fw_sim.c $(COMMON) ../src/*.h
	$(CC) $(CFLAGS) -o $@ fw_sim.c $(COMMON) -lm

wave_test: wave_test.c ../src/hp302.c ../src/hp302.h
	$(CC) $(CFLAGS) -o $@ wave_test.c ../src/hp302.c

clean:
	rm -f fw_sim wave_test
