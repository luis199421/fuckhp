# Builds the host-side firmware simulator (no Pico SDK needed).
CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -Werror -std=c11
SRC = fw_sim.c ../src/frame.c ../src/ring.c ../src/packbits.c ../src/compose.c ../src/hp45_map.c

fw_sim: $(SRC) ../src/*.h
	$(CC) $(CFLAGS) -o $@ $(SRC) -lm

clean:
	rm -f fw_sim
