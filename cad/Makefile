# Export every printable part to stl/ :   make -j8
# Needs OpenSCAD 2021.01 or newer.
OPENSCAD ?= openscad
S = parts

PARTS = \
  side_plate_left:side_plate.scad:RIGHT=false \
  side_plate_right:side_plate.scad:RIGHT=true \
  carriage:carriage.scad: \
  carriage_pad:carriage_pad.scad: \
  platen_1:platen.scad:SEG=0 \
  platen_2:platen.scad:SEG=1 \
  platen_3:platen.scad:SEG=2 \
  roller_hub:roller_hub.scad: \
  roller_tire_TPU:roller_tire.scad: \
  star_wheel:star_wheel.scad: \
  gt2_pulley_76t:gt2_pulley_76t.scad: \
  x_motor_bracket:x_motor_bracket.scad: \
  x_idler_bracket:x_idler_bracket.scad: \
  service_station_base:service_station.scad:PART="base" \
  service_station_sled:service_station.scad:PART="sled" \
  sensor_bracket:sensor_bracket.scad: \
  electronics_tray:electronics_tray.scad: \
  paper_tray_left:paper_tray.scad:PART="left" \
  paper_tray_right:paper_tray.scad:PART="right" \
  paper_guide:paper_tray.scad:PART="guide" \
  tray_bracket:paper_tray.scad:PART="bracket" \
  roll_arm:roll_holder.scad:PART="arm" \
  roll_core:roll_holder.scad:PART="core"

pname = $(word 1,$(subst :, ,$1))
pfile = $(word 2,$(subst :, ,$1))
pdef  = $(word 3,$(subst :, ,$1))
STLS = $(foreach p,$(PARTS),stl/$(call pname,$p).stl)

all: $(STLS)

define rule
stl/$(call pname,$1).stl: $(S)/$(call pfile,$1) fj.scad
	@mkdir -p stl
	$(OPENSCAD) $(if $(call pdef,$1),-D '$(call pdef,$1)') -o $$@ $$<
endef
$(foreach p,$(PARTS),$(eval $(call rule,$p)))

clean:
	rm -rf stl
.PHONY: all clean
