SRC = alu_4bit.v alu_4bit_tb.v

.PHONY: all sim wave view clean

all: sim wave

alu_sim: $(SRC)
	iverilog -Wall -o alu_sim $(SRC)

sim: alu_sim
	vvp alu_sim

alu_4bit.vcd: alu_sim
	vvp alu_sim

wave: alu_4bit.vcd
	python3 scripts/vcd_to_svg.py alu_4bit.vcd docs/alu_waveform.svg

view: alu_4bit.vcd
	gtkwave alu_4bit.vcd &

clean:
	rm -f alu_sim alu_4bit.vcd
