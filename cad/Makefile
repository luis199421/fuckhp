# Export every printable part:
#   make -j8                 black cartridge (HP 63/302)          -> stl/
#   make -j8 CARTS=KCMY      black + tri-colour cartridges        -> stl-kcmy/
#   (CARTS=CMY, colour cartridge only, uses the same parts as the default build)
# Needs OpenSCAD 2021.01 or newer.
OPENSCAD ?= openscad
S = parts
CARTS ?= K
OUT := $(if $(filter KCMY,$(CARTS)),stl-kcmy,stl)
# same arithmetic as fj.scad: number of platen segments and tray pieces
GEOM := $(shell python3 -c "import math;s=28 if '$(CARTS)'=='KCMY' else 0;w=360+2*s;e=(70+s+88) if 70+s+88<=160 else 70+s-10;print(1+math.ceil((w-e)/130), math.ceil(w/190))")
PLATEN_SEGS := $(word 1,$(GEOM))
TRAY_PIECES := $(word 2,$(GEOM))

PARTS = \
  side_plate_left:side_plate.scad:RIGHT=false \
  side_plate_right:side_plate.scad:RIGHT=true \
  carriage:carriage.scad: \
  carriage_pad:carriage_pad.scad: \
  $(foreach i,$(shell seq 1 $(PLATEN_SEGS)),platen_$(i):platen.scad:SEG=$(shell echo $$(($(i)-1)))) \
  roller_hub:roller_hub.scad: \
  roller_tire_TPU:roller_tire.scad: \
  gt2_pulley_60t:gt2_pulley_60t.scad: \
  leaf_bar_1:leaf_bar.scad:PIECE=0 \
  leaf_bar_2:leaf_bar.scad:PIECE=1 \
  leaf_clamp:leaf_bar.scad:PART="clamp" \
  x_motor_bracket:x_motor_bracket.scad: \
  x_idler_bracket:x_idler_bracket.scad: \
  service_station_base:service_station.scad:PART="base" \
  service_station_sled:service_station.scad:PART="sled" \
  sensor_bracket:sensor_bracket.scad: \
  electronics_tray:electronics_tray.scad: \
  $(foreach i,$(shell seq 1 $(TRAY_PIECES)),paper_tray_$(i):paper_tray.scad:PIECE=$(shell echo $$(($(i)-1)))) \
  paper_guide:paper_tray.scad:PART="guide" \
  tray_bracket:paper_tray.scad:PART="bracket" \
  service_cap_TPU:service_station.scad:PART="cap" \
  service_wiper_TPU:service_station.scad:PART="wiper" \
  rod_collar:rod_collar.scad: \
  roll_core:roll_holder.scad:PART="core" \
  roll_spindle:roll_holder.scad:PART="spindle"

pname = $(word 1,$(subst :, ,$1))
pfile = $(word 2,$(subst :, ,$1))
pdef  = $(word 3,$(subst :, ,$1))
STLS = $(foreach p,$(PARTS),$(OUT)/$(call pname,$p).stl)

all: $(STLS)

define rule
$(OUT)/$(call pname,$1).stl: $(S)/$(call pfile,$1) fj.scad
	@mkdir -p $(OUT)
	$(OPENSCAD) -D 'CARTS="$(CARTS)"' $(if $(call pdef,$1),-D '$(call pdef,$1)') -o $$@ $$<
endef
$(foreach p,$(PARTS),$(eval $(call rule,$p)))

clean:
	rm -rf stl stl-*
.PHONY: all clean
